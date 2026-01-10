r"""JSON and JSONL utility functions.

JSON Path Support
-----------------
The ``--json-ignore`` option uses a simplified JSON path syntax:

Supported syntax:
    - ``$.field`` or ``field`` - Access object field
    - ``$.field.nested`` - Access nested field
    - ``$.array[0]`` - Access array element by index
    - ``$.field[0].nested`` - Combined access

Limitations (not supported):
    - Escaped dots in field names (e.g., ``a\.b`` for key "a.b")
    - Bracket notation for keys (e.g., ``["key-with-dashes"]``)
    - Wildcards or recursive descent (``*``, ``..*``)
    - Filter expressions (``[?(@.price < 10)]``)
    - Slice notation (``[0:5]``)

For keys containing special characters, consider using ``--replace`` to
transform the output before comparison instead.
"""

from __future__ import annotations

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
    obj = json.loads(json.dumps(obj))  # Deep copy

    for path in paths:
        _remove_single_path(obj, path)

    return obj


def _remove_single_path(obj: Any, path: str) -> None:
    """Remove a single path from object in place."""
    # Remove leading $ if present
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:]

    parts = re.split(r"\.|\[(\d+)\]", path)
    parts = [p for p in parts if p]

    if not parts:
        return

    # Navigate to parent
    current = obj
    for part in parts[:-1]:
        if current is None:
            return
        current = _navigate(current, part)

    # Remove the final key
    if current is None:
        return

    final = parts[-1]
    if final.isdigit() and isinstance(current, list):
        idx = int(final)
        if 0 <= idx < len(current):
            current.pop(idx)
    elif isinstance(current, dict) and final in current:
        del current[final]


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
