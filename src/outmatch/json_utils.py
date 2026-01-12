r"""JSON and JSONL utility functions.

JSON Path Support
-----------------
The ``--json-ignore`` option uses a simplified JSON path syntax:

Supported syntax:
    - ``$.field`` or ``field`` - Access object field
    - ``$.field.nested`` - Access nested field
    - ``$.array[0]`` - Access array element by index
    - ``$.array[*]`` - Access all array elements (wildcard)
    - ``$.field[0].nested`` - Combined access
    - ``$.items[*].timestamp`` - Ignore field in all array elements

Limitations (not supported):
    - Escaped dots in field names (e.g., ``a\.b`` for key "a.b")
    - Bracket notation for keys (e.g., ``["key-with-dashes"]``)
    - Recursive descent (``..*``)
    - Filter expressions (``[?(@.price < 10)]``)
    - Slice notation (``[0:5]``)

For keys containing special characters, consider using ``--replace`` to
transform the output before comparison instead.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any


def normalize_json(obj: Any) -> Any:
    """Recursively sort dicts for stable comparison."""
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [normalize_json(v) for v in obj]
    return obj


# Wildcard marker for JSON matching - matches any value
JSON_WILDCARD = "*"


def json_matches_with_wildcards(actual: Any, expected: Any) -> bool:
    """Check if actual matches expected, treating "*" as a wildcard.

    The string "*" in expected matches any value in actual, including:
    - Strings, numbers, booleans, null
    - Objects and arrays (any structure)

    For partial object matching (only checking certain fields), use
    jsonl-contains mode instead.

    Args:
        actual: The actual JSON value to check.
        expected: The expected pattern, potentially containing "*" wildcards.

    Returns:
        True if actual matches expected (with wildcard substitution).
    """
    # If expected is wildcard, match anything
    if expected == JSON_WILDCARD:
        return True

    # If types don't match (and expected isn't wildcard), fail
    if not isinstance(actual, type(expected)):
        return False

    # For dicts, check all expected keys exist and match
    if isinstance(expected, dict):
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(
            json_matches_with_wildcards(actual[k], v)
            for k, v in expected.items()
        )

    # For lists, check same length and each element matches
    if isinstance(expected, list):
        if len(actual) != len(expected):
            return False
        return all(
            json_matches_with_wildcards(a, e)
            for a, e in zip(actual, expected)
        )

    # For primitives, direct equality
    return actual == expected


def find_wildcard_mismatches(
    actual: Any, expected: Any, path: str = "$"
) -> list[str]:
    """Find mismatches between actual and expected, returning paths.

    Used for error reporting when json_matches_with_wildcards returns False.

    Args:
        actual: The actual JSON value.
        expected: The expected pattern with potential wildcards.
        path: Current JSON path (for error messages).

    Returns:
        List of mismatch descriptions.
    """
    if expected == JSON_WILDCARD:
        return []

    mismatches = []

    if not isinstance(actual, type(expected)):
        mismatches.append(
            f"{path}: type mismatch - expected {type(expected).__name__}, "
            f"got {type(actual).__name__}"
        )
        return mismatches

    if isinstance(expected, dict):
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())

        for key in expected_keys - actual_keys:
            mismatches.append(f"{path}.{key}: missing key")
        for key in actual_keys - expected_keys:
            mismatches.append(f"{path}.{key}: unexpected key")

        for key in expected_keys & actual_keys:
            mismatches.extend(
                find_wildcard_mismatches(actual[key], expected[key], f"{path}.{key}")
            )
        return mismatches

    if isinstance(expected, list):
        if len(actual) != len(expected):
            mismatches.append(
                f"{path}: array length mismatch - expected {len(expected)}, "
                f"got {len(actual)}"
            )
            return mismatches

        for i, (a, e) in enumerate(zip(actual, expected)):
            mismatches.extend(find_wildcard_mismatches(a, e, f"{path}[{i}]"))
        return mismatches

    if actual != expected:
        mismatches.append(f"{path}: expected {expected!r}, got {actual!r}")

    return mismatches


def parse_jsonl(text: str) -> list[Any]:
    """Parse JSONL text into list of values."""
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    return [json.loads(line) for line in lines]


def remove_json_paths(obj: Any, paths: tuple[str, ...]) -> Any:
    """Remove paths from JSON object (returns new object).

    Args:
        obj: JSON-serializable object to modify.
        paths: Tuple of JSON paths to remove. See module docstring for
            supported path syntax and limitations.

    Returns:
        A deep copy of the object with specified paths removed.
        Non-existent paths are silently ignored.

    Example:
        >>> obj = {"a": 1, "b": {"c": 2}}
        >>> remove_json_paths(obj, ("$.b.c",))
        {'a': 1, 'b': {}}
    """
    obj = copy.deepcopy(obj)

    for path in paths:
        _remove_single_path(obj, path)

    return obj


def _remove_single_path(obj: Any, path: str) -> None:
    """Remove a single path from object in place.

    Supports wildcard [*] to remove from all array elements.
    """
    # Remove leading $ if present
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:]

    # Split path, preserving wildcards
    parts = re.split(r"\.|\[(\d+|\*)\]", path)
    parts = [p for p in parts if p]

    if not parts:
        return

    _remove_path_recursive(obj, parts)


def _remove_path_recursive(obj: Any, parts: list[str]) -> None:
    """Recursively remove path, handling wildcards."""
    if not parts or obj is None:
        return

    part = parts[0]
    remaining = parts[1:]

    # Wildcard: apply to all array elements
    if part == "*":
        if isinstance(obj, list):
            for item in obj:
                if remaining:
                    _remove_path_recursive(item, remaining)
        return

    # Final part: remove the key/index
    if not remaining:
        if part.isdigit() and isinstance(obj, list):
            idx = int(part)
            if 0 <= idx < len(obj):
                obj.pop(idx)
        elif isinstance(obj, dict) and part in obj:
            del obj[part]
        return

    # Navigate deeper
    next_obj = _navigate(obj, part)
    if next_obj is not None:
        _remove_path_recursive(next_obj, remaining)


def _navigate(obj: Any, part: str) -> Any:
    """Navigate one step into an object."""
    if part.isdigit():
        idx = int(part)
        if isinstance(obj, list) and 0 <= idx < len(obj):
            return obj[idx]
        return None
    if isinstance(obj, dict):
        return obj.get(part)
    return None
