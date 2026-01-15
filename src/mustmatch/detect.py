"""Auto-detection of comparison types from value syntax."""

from __future__ import annotations

import json
from enum import Enum, auto


class ValueType(Enum):
    """Detected type of expected value."""
    STRING = auto()
    REGEX = auto()
    JSON = auto()


def detect_type(value: str) -> ValueType:
    """Detect comparison type from value syntax.

    Detection rules:
    - /pattern/ -> REGEX (must start and end with /)
    - {...} -> JSON object
    - [...] -> JSON array
    - everything else -> STRING

    Args:
        value: The expected value string.

    Returns:
        Detected ValueType.
    """
    value = value.strip()

    # Regex: /pattern/
    if value.startswith("/") and value.endswith("/") and len(value) > 2:
        return ValueType.REGEX

    # JSON object or array
    if (value.startswith("{") and value.endswith("}")) or \
       (value.startswith("[") and value.endswith("]")):
        # Verify it's actually valid JSON
        try:
            json.loads(value)
            return ValueType.JSON
        except json.JSONDecodeError:
            pass

    return ValueType.STRING


def extract_regex(value: str) -> str:
    """Extract regex pattern from /pattern/ syntax.

    Args:
        value: Value in /pattern/ format.

    Returns:
        The pattern without surrounding slashes.
    """
    return value.strip()[1:-1]


def is_jsonl(text: str) -> bool:
    """Check if text appears to be JSONL (multiple JSON lines).

    Args:
        text: Text to check.

    Returns:
        True if text has multiple lines that are each valid JSON.
    """
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if len(lines) < 2:
        return False

    # Check if each line is valid JSON
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            return False

    return True
