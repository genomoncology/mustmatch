"""Comparison functions for different matching modes."""

from __future__ import annotations

import json
import re

from .config import CompareMode, CompareResult, MatchConfig
from .detect import ValueType, detect_type, extract_regex, is_jsonl
from .json_utils import (
    find_wildcard_mismatches,
    json_matches_with_wildcards,
    normalize_json,
    parse_jsonl,
    remove_json_paths,
)
from .output import format_diff, unified_diff


def compare_exact_string(
    actual: str, expected: str, config: MatchConfig | None = None
) -> CompareResult:
    """Exact string comparison with trailing newline normalization."""
    actual = actual.rstrip("\n")
    expected = expected.rstrip("\n")

    if actual == expected:
        return CompareResult(success=True)

    # Generate diff
    if config is not None:
        diff = format_diff(actual, expected, config)
    else:
        diff = unified_diff(actual, expected, context=3)

    msg = f"Exact match failed.\n\n{diff}" if diff else "Exact match failed."
    return CompareResult(
        success=False,
        message=msg,
        expected=expected[:200],
        actual=actual[:200],
    )


def compare_contains_string(actual: str, expected: str) -> CompareResult:
    """Check if actual contains expected substring."""
    expected = expected.strip()
    if expected in actual:
        return CompareResult(success=True)

    excerpt = actual[:500] + ("..." if len(actual) > 500 else "")
    return CompareResult(
        success=False,
        message=f"Expected to contain:\n{expected}\n\nActual:\n{excerpt}",
        expected=expected[:200],
        actual=actual[:200],
    )


def compare_regex(actual: str, pattern: str) -> CompareResult:
    """Check if actual matches regex pattern."""
    try:
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
    except re.error as e:
        return CompareResult(success=False, message=f"Invalid regex: {e}")

    if regex.search(actual):
        return CompareResult(success=True)

    return CompareResult(
        success=False,
        message=f"Regex not found:\n{pattern}\n\nActual:\n{actual[:500]}",
        expected=pattern,
        actual=actual[:200],
    )


def compare_not_contains(actual: str, expected: str) -> CompareResult:
    """Check that actual does NOT contain expected substring."""
    expected = expected.strip()
    if expected not in actual:
        return CompareResult(success=True)

    pos = actual.find(expected)
    context_start = max(0, pos - 30)
    context_end = min(len(actual), pos + len(expected) + 30)
    context = actual[context_start:context_end]
    if context_start > 0:
        context = "..." + context
    if context_end < len(actual):
        context = context + "..."

    msg = (
        f"Expected NOT to contain:\n{expected}\n\n"
        f"But found at position {pos}:\n{context}"
    )
    return CompareResult(
        success=False,
        message=msg,
        expected=f"NOT {expected[:200]}",
        actual=context,
    )


def compare_not_regex(actual: str, pattern: str) -> CompareResult:
    """Check that actual does NOT match regex pattern."""
    try:
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
    except re.error as e:
        return CompareResult(success=False, message=f"Invalid regex: {e}")

    match = regex.search(actual)
    if not match:
        return CompareResult(success=True)

    start, end = match.span()
    context_start = max(0, start - 30)
    context_end = min(len(actual), end + 30)
    context = actual[context_start:context_end]
    if context_start > 0:
        context = "..." + context
    if context_end < len(actual):
        context = context + "..."

    msg = (
        f"Expected NOT to match regex:\n{pattern}\n\n"
        f"But matched at position {start}:\n{context}"
    )
    return CompareResult(
        success=False,
        message=msg,
        expected=f"NOT /{pattern}/",
        actual=context,
    )


def compare_json(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Compare JSON values semantically.

    Supports wildcard matching: "*" matches any value.
    """
    try:
        actual_obj = json.loads(actual.strip())
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"Actual is not valid JSON: {e}")

    try:
        expected_obj = json.loads(expected.strip())
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"Expected is not valid JSON: {e}")

    if ignore_paths:
        actual_obj = remove_json_paths(actual_obj, ignore_paths)
        expected_obj = remove_json_paths(expected_obj, ignore_paths)

    if json_matches_with_wildcards(actual_obj, expected_obj):
        return CompareResult(success=True)

    # Generate mismatch report
    mismatches = find_wildcard_mismatches(actual_obj, expected_obj)
    if mismatches:
        details = "\n".join(f"  {m}" for m in mismatches[:10])
        if len(mismatches) > 10:
            details += f"\n  ... and {len(mismatches) - 10} more"
        return CompareResult(
            success=False,
            message=f"JSON mismatch:\n{details}",
            expected=json.dumps(expected_obj, indent=2)[:200],
            actual=json.dumps(actual_obj, indent=2)[:200],
        )

    msg = (
        f"JSON mismatch:\nExpected: {json.dumps(expected_obj)}\n"
        f"Actual: {json.dumps(actual_obj)}"
    )
    return CompareResult(
        success=False,
        message=msg,
        expected=json.dumps(expected_obj)[:200],
        actual=json.dumps(actual_obj)[:200],
    )


def compare_json_contains(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Check if actual JSON contains expected fields/values (subset match).

    For objects: all expected keys must exist with matching values.
    For arrays: all expected elements must be present.
    For JSONL: all expected records must be present.
    """
    try:
        actual_obj = json.loads(actual.strip())
    except json.JSONDecodeError:
        # Try as JSONL
        if is_jsonl(actual):
            return _compare_jsonl_contains(actual, expected, ignore_paths)
        return CompareResult(success=False, message="Actual is not valid JSON")

    try:
        expected_obj = json.loads(expected.strip())
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"Expected is not valid JSON: {e}")

    if ignore_paths:
        actual_obj = remove_json_paths(actual_obj, ignore_paths)
        expected_obj = remove_json_paths(expected_obj, ignore_paths)

    if _json_contains(actual_obj, expected_obj):
        return CompareResult(success=True)

    msg = (
        f"JSON does not contain expected:\nExpected: {json.dumps(expected_obj)}\n"
        f"Actual: {json.dumps(actual_obj)}"
    )
    return CompareResult(
        success=False,
        message=msg,
        expected=json.dumps(expected_obj)[:200],
        actual=json.dumps(actual_obj)[:200],
    )


def _json_contains(actual: object, expected: object) -> bool:
    """Check if actual JSON contains expected (subset match)."""
    if expected == "*":
        return True

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(
            k in actual and _json_contains(actual[k], v)
            for k, v in expected.items()
        )

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        # All expected items must be present in actual
        return all(
            any(_json_contains(a, e) for a in actual)
            for e in expected
        )

    return actual == expected


def _compare_jsonl_contains(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Check if actual JSONL contains all expected records."""
    try:
        actual_records = [normalize_json(r) for r in parse_jsonl(actual)]
        expected_records = [normalize_json(r) for r in parse_jsonl(expected)]
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"JSON parse error: {e}")

    if ignore_paths:
        actual_records = [
            remove_json_paths(r, ignore_paths) for r in actual_records
        ]
        expected_records = [
            remove_json_paths(r, ignore_paths) for r in expected_records
        ]

    missing = []
    for exp in expected_records:
        if not any(_json_contains(act, exp) for act in actual_records):
            missing.append(exp)

    if missing:
        msg = "Missing expected records:\n" + "\n".join(
            json.dumps(m) for m in missing
        )
        exp = json.dumps(expected_records[0])[:200] if expected_records else ""
        act = json.dumps(actual_records[0])[:200] if actual_records else ""
        return CompareResult(success=False, message=msg, expected=exp, actual=act)

    return CompareResult(success=True)


def compare(
    actual: str,
    expected: str,
    config: MatchConfig,
) -> CompareResult:
    """Main comparison dispatcher.

    Auto-detects value type (string/regex/json) and routes to appropriate
    comparison function based on config.mode.
    """
    value_type = detect_type(expected)
    ignore_paths = config.json_ignore_paths

    # Handle regex patterns
    if value_type == ValueType.REGEX:
        pattern = extract_regex(expected)
        negated_modes = (
            CompareMode.NOT_EXACT, CompareMode.NOT_CONTAINS, CompareMode.NOT_REGEX
        )
        if config.mode in negated_modes:
            return compare_not_regex(actual, pattern)
        return compare_regex(actual, pattern)

    # Handle JSON
    if value_type == ValueType.JSON:
        if config.mode == CompareMode.CONTAINS:
            return compare_json_contains(actual, expected, ignore_paths)
        if config.mode in (CompareMode.NOT_EXACT, CompareMode.NOT_CONTAINS):
            # For JSON, NOT means the JSON should not match
            result = compare_json(actual, expected, ignore_paths)
            if result.success:
                return CompareResult(
                    success=False,
                    message="Expected JSON NOT to match, but it did",
                    expected=expected[:200],
                    actual=actual[:200],
                )
            return CompareResult(success=True)
        return compare_json(actual, expected, ignore_paths)

    # Handle strings
    match config.mode:
        case CompareMode.EXACT:
            return compare_exact_string(actual, expected, config)
        case CompareMode.CONTAINS:
            return compare_contains_string(actual, expected)
        case CompareMode.REGEX:
            return compare_regex(actual, expected)
        case CompareMode.NOT_EXACT:
            result = compare_exact_string(actual, expected, config)
            if result.success:
                return CompareResult(
                    success=False,
                    message="Expected NOT to match, but it did",
                    expected=expected[:200],
                    actual=actual[:200],
                )
            return CompareResult(success=True)
        case CompareMode.NOT_CONTAINS:
            return compare_not_contains(actual, expected)
        case CompareMode.NOT_REGEX:
            return compare_not_regex(actual, expected)

    return CompareResult(success=False, message=f"Unknown mode: {config.mode}")
