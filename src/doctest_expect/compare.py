"""Comparison functions for different matching modes."""

from __future__ import annotations

import json
import re
from typing import Any

from .config import CompareMode, CompareResult, ExpectConfig
from .json_utils import normalize_json, parse_jsonl, remove_json_paths
from .output import unified_diff


def compare_exact(actual: str, expected: str) -> CompareResult:
    """Exact string comparison with trailing newline normalization."""
    actual = actual.rstrip("\n")
    expected = expected.rstrip("\n")
    if actual == expected:
        return CompareResult(success=True)
    diff = unified_diff(actual, expected)
    return CompareResult(success=False, message=f"Exact match failed.\n\n{diff}")


def compare_contains(actual: str, expected: str) -> CompareResult:
    """Check if actual contains expected substring."""
    expected_stripped = expected.strip()
    if expected_stripped in actual:
        return CompareResult(success=True)
    excerpt = actual[:500] + ("..." if len(actual) > 500 else "")
    return CompareResult(
        success=False,
        message=f"Expected to contain:\n{expected_stripped}\n\nActual:\n{excerpt}",
    )


def compare_regex(actual: str, expected: str) -> CompareResult:
    """Check if actual matches regex pattern."""
    try:
        pattern = re.compile(expected, re.MULTILINE | re.DOTALL)
    except re.error as e:
        return CompareResult(success=False, message=f"Invalid regex pattern: {e}")

    if pattern.search(actual):
        return CompareResult(success=True)
    return CompareResult(
        success=False,
        message=f"Regex not found:\n{expected}\n\nActual:\n{actual}",
    )


def compare_json(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Compare single JSON values semantically."""
    try:
        actual_obj = json.loads(actual.strip())
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"Actual is not valid JSON: {e}")

    try:
        expected_obj = json.loads(expected.strip())
    except json.JSONDecodeError as e:
        return CompareResult(
            success=False,
            message=f"Expected is not valid JSON: {e}",
        )

    if ignore_paths:
        actual_obj = remove_json_paths(actual_obj, ignore_paths)
        expected_obj = remove_json_paths(expected_obj, ignore_paths)

    if normalize_json(actual_obj) == normalize_json(expected_obj):
        return CompareResult(success=True)

    return CompareResult(
        success=False,
        message=(
            f"JSON mismatch:\n"
            f"Expected: {json.dumps(expected_obj, indent=2)}\n"
            f"Actual: {json.dumps(actual_obj, indent=2)}"
        ),
    )


def compare_jsonl(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Compare JSONL output semantically (record order matters)."""
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"JSON parse error: {e}")

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [
            remove_json_paths(r, ignore_paths) for r in expected_records
        ]

    if len(actual_records) != len(expected_records):
        return CompareResult(
            success=False,
            message=(
                f"Record count mismatch: expected {len(expected_records)}, "
                f"got {len(actual_records)}"
            ),
        )

    for i, (act, exp) in enumerate(zip(actual_records, expected_records)):
        if normalize_json(act) != normalize_json(exp):
            return CompareResult(
                success=False,
                message=(
                    f"Record {i} mismatch:\n"
                    f"Expected: {json.dumps(exp)}\n"
                    f"Actual: {json.dumps(act)}"
                ),
            )

    return CompareResult(success=True)


def compare_jsonl_set(
    actual: str,
    expected: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Compare JSONL output as unordered multiset."""
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"JSON parse error: {e}")

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [
            remove_json_paths(r, ignore_paths) for r in expected_records
        ]

    actual_norm = sorted(
        json.dumps(normalize_json(r), sort_keys=True) for r in actual_records
    )
    expected_norm = sorted(
        json.dumps(normalize_json(r), sort_keys=True) for r in expected_records
    )

    if actual_norm == expected_norm:
        return CompareResult(success=True)

    return _format_set_diff(actual_norm, expected_norm)


def _format_set_diff(actual: list[str], expected: list[str]) -> CompareResult:
    """Format difference between two multisets."""
    actual_counts: dict[str, int] = {}
    for r in actual:
        actual_counts[r] = actual_counts.get(r, 0) + 1

    expected_counts: dict[str, int] = {}
    for r in expected:
        expected_counts[r] = expected_counts.get(r, 0) + 1

    missing = []
    extra = []

    all_keys = set(actual_counts.keys()) | set(expected_counts.keys())
    for key in all_keys:
        act_count = actual_counts.get(key, 0)
        exp_count = expected_counts.get(key, 0)
        if act_count > exp_count:
            extra.extend([key] * (act_count - exp_count))
        elif exp_count > act_count:
            missing.extend([key] * (exp_count - act_count))

    parts = ["JSONL set comparison failed:"]
    if missing:
        parts.append(f"Missing {len(missing)} record(s):")
        parts.extend(f"  {r}" for r in missing[:5])
        if len(missing) > 5:
            parts.append(f"  ... and {len(missing) - 5} more")
    if extra:
        parts.append(f"Extra {len(extra)} record(s):")
        parts.extend(f"  {r}" for r in extra[:5])
        if len(extra) > 5:
            parts.append(f"  ... and {len(extra) - 5} more")

    return CompareResult(success=False, message="\n".join(parts))


def compare_jsonl_key(
    actual: str,
    expected: str,
    key_field: str,
    ignore_paths: tuple[str, ...] = (),
) -> CompareResult:
    """Compare JSONL records matched by a key field."""
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return CompareResult(success=False, message=f"JSON parse error: {e}")

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [
            remove_json_paths(r, ignore_paths) for r in expected_records
        ]

    # Build dicts by key
    actual_by_key: dict[Any, Any] = {}
    for r in actual_records:
        if not isinstance(r, dict) or key_field not in r:
            return CompareResult(
                success=False,
                message=f"Record missing key field '{key_field}': {json.dumps(r)}",
            )
        actual_by_key[r[key_field]] = r

    expected_by_key: dict[Any, Any] = {}
    for r in expected_records:
        if not isinstance(r, dict) or key_field not in r:
            return CompareResult(
                success=False,
                message=f"Expected record missing key '{key_field}': {json.dumps(r)}",
            )
        expected_by_key[r[key_field]] = r

    actual_keys = set(actual_by_key.keys())
    expected_keys = set(expected_by_key.keys())

    errors = []
    if missing := expected_keys - actual_keys:
        errors.append(f"Missing keys: {sorted(missing)}")
    if extra := actual_keys - expected_keys:
        errors.append(f"Extra keys: {sorted(extra)}")

    for key in expected_keys & actual_keys:
        if normalize_json(actual_by_key[key]) != normalize_json(expected_by_key[key]):
            errors.append(
                f"Mismatch for key '{key}':\n"
                f"  Expected: {json.dumps(expected_by_key[key])}\n"
                f"  Actual: {json.dumps(actual_by_key[key])}"
            )

    if errors:
        return CompareResult(
            success=False,
            message="JSONL key comparison failed:\n" + "\n".join(errors),
        )
    return CompareResult(success=True)


def compare_jsonl_contains(
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
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [
            remove_json_paths(r, ignore_paths) for r in expected_records
        ]

    missing = []
    for exp in expected_records:
        if not _record_contained(exp, actual_records):
            missing.append(exp)

    if missing:
        return CompareResult(
            success=False,
            message="Missing expected records:\n"
            + "\n".join(json.dumps(m) for m in missing),
        )
    return CompareResult(success=True)


def _record_contained(expected: Any, actual_list: list[Any]) -> bool:
    """Check if expected record is contained in actual list."""
    for act in actual_list:
        if isinstance(expected, dict) and isinstance(act, dict):
            if all(act.get(k) == v for k, v in expected.items()):
                return True
        elif expected == act:
            return True
    return False


def compare(
    actual: str,
    expected: str,
    config: ExpectConfig,
) -> CompareResult:
    """Dispatch to appropriate comparison function based on config."""
    ignore = config.json_ignore_paths

    match config.mode:
        case CompareMode.EXACT:
            return compare_exact(actual, expected)
        case CompareMode.CONTAINS:
            return compare_contains(actual, expected)
        case CompareMode.REGEX:
            return compare_regex(actual, expected)
        case CompareMode.JSON:
            return compare_json(actual, expected, ignore)
        case CompareMode.JSONL:
            return compare_jsonl(actual, expected, ignore)
        case CompareMode.JSONL_SET:
            return compare_jsonl_set(actual, expected, ignore)
        case CompareMode.JSONL_KEY:
            return compare_jsonl_key(
                actual, expected, config.jsonl_key_field or "", ignore
            )
        case CompareMode.JSONL_CONTAINS:
            return compare_jsonl_contains(actual, expected, ignore)
