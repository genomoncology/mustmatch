"""Configuration dataclasses for mustmatch."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class CompareMode(Enum):
    """Comparison mode for mustmatch."""
    EXACT = auto()          # Exact match (string or JSON)
    CONTAINS = auto()       # Contains/subset (string or JSON)
    REGEX = auto()          # Regex match
    NOT_EXACT = auto()      # Must NOT match exactly
    NOT_CONTAINS = auto()   # Must NOT contain
    NOT_REGEX = auto()      # Regex must NOT match


class ColorMode(Enum):
    """Color output mode."""
    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class DiffFormat(Enum):
    """Diff output format."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side-by-side"
    INLINE = "inline"
    NONE = "none"


@dataclass(frozen=True)
class CompareResult:
    """Result of a comparison operation."""
    success: bool
    message: str = ""
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class MatchConfig:
    """Configuration for a match operation."""
    mode: CompareMode = CompareMode.EXACT
    ignore_case: bool = False
    json_ignore_paths: tuple[str, ...] = ()
    quiet: bool = False
    color: ColorMode = ColorMode.AUTO
    diff_context: int = 3
    diff_format: DiffFormat = DiffFormat.UNIFIED


# Backward compatibility alias
ExpectConfig = MatchConfig


@dataclass(frozen=True)
class NormalizeOptions:
    """Options for text normalization.

    Note: strip_ansi and normalize_newlines are now always applied.
    """
    trim: bool = False
    collapse_whitespace: bool = False
    ignore_case: bool = False
    replacements: tuple[tuple[re.Pattern[str], str], ...] = ()
    redactions: tuple[re.Pattern[str], ...] = ()
