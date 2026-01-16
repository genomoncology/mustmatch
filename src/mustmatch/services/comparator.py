"""
Comparison services for mustmatch.

Provides exact, contains, regex, and JSON comparison modes.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CompareMode(Enum):
    """Comparison mode for matching."""

    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    JSON = "json"
    JSONL = "jsonl"


@dataclass
class CompareResult:
    """Result of a comparison operation."""

    matches: bool
    message: str = ""  # Empty if matches, diff/explanation if not
    mode: CompareMode = CompareMode.EXACT


def exact(actual: str, expected: str) -> CompareResult:
    """Exact string comparison.

    Args:
        actual: The actual string to check.
        expected: The expected string.

    Returns:
        CompareResult indicating if strings are identical.
    """
    if actual == expected:
        return CompareResult(matches=True, mode=CompareMode.EXACT)

    # Generate diff for error message
    diff = _generate_diff(actual, expected)
    return CompareResult(
        matches=False,
        message=diff,
        mode=CompareMode.EXACT,
    )


def contains(actual: str, expected: str) -> CompareResult:
    """Substring/contains comparison.

    Args:
        actual: The actual string to check.
        expected: The substring that should be contained.

    Returns:
        CompareResult indicating if expected is contained in actual.
    """
    if expected in actual:
        return CompareResult(matches=True, mode=CompareMode.CONTAINS)

    return CompareResult(
        matches=False,
        message=f"Expected substring not found: {expected!r}\nActual: {actual!r}",
        mode=CompareMode.CONTAINS,
    )


def regex(actual: str, pattern: str) -> CompareResult:
    """Regex pattern match.

    Args:
        actual: The actual string to check.
        pattern: The regex pattern (without delimiters).

    Returns:
        CompareResult indicating if pattern matches.
    """
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        return CompareResult(
            matches=False,
            message=f"Invalid regex pattern: {e}",
            mode=CompareMode.REGEX,
        )

    if compiled.search(actual):
        return CompareResult(matches=True, mode=CompareMode.REGEX)

    return CompareResult(
        matches=False,
        message=f"Pattern /{pattern}/ did not match\nActual: {actual!r}",
        mode=CompareMode.REGEX,
    )


def json_match(
    actual: str,
    expected: str,
    *,
    subset: bool = False,
) -> CompareResult:
    """Semantic JSON comparison.

    Args:
        actual: The actual JSON string.
        expected: The expected JSON string.
        subset: If True, actual only needs to contain expected fields.

    Returns:
        CompareResult indicating if JSON values match semantically.
    """
    try:
        actual_obj = json.loads(actual)
    except json.JSONDecodeError as e:
        return CompareResult(
            matches=False,
            message=f"Invalid JSON in actual: {e}",
            mode=CompareMode.JSON,
        )

    try:
        expected_obj = json.loads(expected)
    except json.JSONDecodeError as e:
        return CompareResult(
            matches=False,
            message=f"Invalid JSON in expected: {e}",
            mode=CompareMode.JSON,
        )

    if subset:
        if _is_subset(expected_obj, actual_obj):
            return CompareResult(matches=True, mode=CompareMode.JSON)
        return CompareResult(
            matches=False,
            message=(
                f"Expected subset not found\n"
                f"Expected: {json.dumps(expected_obj, indent=2)}\n"
                f"Actual: {json.dumps(actual_obj, indent=2)}"
            ),
            mode=CompareMode.JSON,
        )

    if actual_obj == expected_obj:
        return CompareResult(matches=True, mode=CompareMode.JSON)

    # Generate diff
    actual_formatted = json.dumps(actual_obj, indent=2, sort_keys=True)
    expected_formatted = json.dumps(expected_obj, indent=2, sort_keys=True)
    diff = _generate_diff(actual_formatted, expected_formatted)

    return CompareResult(
        matches=False,
        message=diff,
        mode=CompareMode.JSON,
    )


def jsonl_match(
    actual: str,
    expected: str,
    *,
    subset: bool = False,
) -> CompareResult:
    """JSONL (JSON Lines) comparison.

    Args:
        actual: The actual JSONL string (newline-delimited JSON objects).
        expected: The expected JSONL string or single JSON object.
        subset: If True, just check if expected is contained in any line.

    Returns:
        CompareResult indicating if JSONL values match.
    """
    actual_lines = [line.strip() for line in actual.strip().split("\n") if line.strip()]
    expected_lines = [
        line.strip() for line in expected.strip().split("\n") if line.strip()
    ]

    # Parse all actual lines
    actual_objects = []
    for i, line in enumerate(actual_lines):
        try:
            actual_objects.append(json.loads(line))
        except json.JSONDecodeError as e:
            return CompareResult(
                matches=False,
                message=f"Invalid JSON on line {i + 1}: {e}",
                mode=CompareMode.JSONL,
            )

    # Parse expected
    expected_objects = []
    for i, line in enumerate(expected_lines):
        try:
            expected_objects.append(json.loads(line))
        except json.JSONDecodeError as e:
            return CompareResult(
                matches=False,
                message=f"Invalid JSON in expected line {i + 1}: {e}",
                mode=CompareMode.JSONL,
            )

    if subset:
        # Check if all expected objects are found in actual
        for exp_obj in expected_objects:
            found = any(_is_subset(exp_obj, act_obj) for act_obj in actual_objects)
            if not found:
                return CompareResult(
                    matches=False,
                    message=f"Expected object not found: {json.dumps(exp_obj)}",
                    mode=CompareMode.JSONL,
                )
        return CompareResult(matches=True, mode=CompareMode.JSONL)

    # Exact comparison
    if actual_objects == expected_objects:
        return CompareResult(matches=True, mode=CompareMode.JSONL)

    return CompareResult(
        matches=False,
        message=(
            f"JSONL mismatch\n"
            f"Expected {len(expected_objects)} objects, got {len(actual_objects)}"
        ),
        mode=CompareMode.JSONL,
    )


def compare(
    actual: str,
    expected: str,
    *,
    mode: CompareMode = CompareMode.EXACT,
    subset: bool = False,
    ignore_case: bool = False,
) -> CompareResult:
    """Unified comparison interface.

    Dispatches to the appropriate comparison function based on mode.

    Args:
        actual: The actual value to check.
        expected: The expected value.
        mode: Comparison mode.
        subset: For JSON/JSONL, check subset instead of exact match.
        ignore_case: Case-insensitive comparison.

    Returns:
        CompareResult from the appropriate comparison function.
    """
    if ignore_case:
        actual = actual.lower()
        expected = expected.lower()

    if mode == CompareMode.EXACT:
        return exact(actual, expected)
    elif mode == CompareMode.CONTAINS:
        return contains(actual, expected)
    elif mode == CompareMode.REGEX:
        return regex(actual, expected)
    elif mode == CompareMode.JSON:
        return json_match(actual, expected, subset=subset)
    else:  # CompareMode.JSONL
        return jsonl_match(actual, expected, subset=subset)


def detect_mode(expected: str) -> CompareMode:
    """Auto-detect comparison mode from expected value syntax.

    Rules:
        - /pattern/ -> REGEX
        - {...} -> JSON object
        - [...] -> JSON array
        - Multiple lines of {...} -> JSONL
        - Anything else -> EXACT

    Args:
        expected: The expected value string.

    Returns:
        Detected CompareMode.
    """
    expected = expected.strip()

    # Regex: /pattern/
    if expected.startswith("/") and expected.endswith("/") and len(expected) > 2:
        return CompareMode.REGEX

    # JSON object or array
    if (expected.startswith("{") and expected.endswith("}")) or (
        expected.startswith("[") and expected.endswith("]")
    ):
        # Check if it's JSONL (multiple JSON objects)
        lines = [line.strip() for line in expected.split("\n") if line.strip()]
        if len(lines) > 1 and all(
            (line.startswith("{") and line.endswith("}")) for line in lines
        ):
            return CompareMode.JSONL
        return CompareMode.JSON

    return CompareMode.EXACT


def extract_regex_pattern(expected: str) -> str:
    """Extract regex pattern from /pattern/ syntax.

    Args:
        expected: String like "/pattern/" or "/pattern/i".

    Returns:
        The pattern without delimiters.
    """
    expected = expected.strip()
    if expected.startswith("/") and expected.endswith("/"):
        return expected[1:-1]
    # Handle flags like /pattern/i
    if expected.startswith("/"):
        match = re.match(r"^/(.+)/([gimsuxy]*)$", expected)
        if match:
            return match.group(1)
    return expected


def _generate_diff(actual: str, expected: str) -> str:
    """Generate a unified diff between actual and expected."""
    actual_lines = actual.splitlines(keepends=True)
    expected_lines = expected.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="expected",
        tofile="actual",
        lineterm="",
    )

    return "".join(diff)


def _is_subset(subset: Any, superset: Any) -> bool:
    """Check if subset is contained within superset (recursively for dicts/lists)."""
    if isinstance(subset, dict) and isinstance(superset, dict):
        for key, value in subset.items():
            if key not in superset:
                return False
            if not _is_subset(value, superset[key]):
                return False
        return True
    elif isinstance(subset, list) and isinstance(superset, list):
        # For lists, check if all items in subset exist in superset
        for item in subset:
            if not any(_is_subset(item, sup_item) for sup_item in superset):
                return False
        return True
    else:
        return subset == superset


