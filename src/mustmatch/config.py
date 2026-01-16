"""Configuration dataclasses for mustmatch."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto


class CompareMode(Enum):
    """Comparison mode for mustmatch."""

    EXACT = auto()
    CONTAINS = auto()
    REGEX = auto()
    JSON = auto()
    JSONL = auto()
    JSONL_SET = auto()
    JSONL_KEY = auto()
    JSONL_CONTAINS = auto()
    NOT_CONTAINS = auto()
    NOT_REGEX = auto()


class ColorMode(Enum):
    """Color output mode."""

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class DiffFormat(Enum):
    """Diff output format."""

    UNIFIED = "unified"  # Default unified diff
    SIDE_BY_SIDE = "side-by-side"  # Side-by-side comparison
    INLINE = "inline"  # Word-level inline diff
    NONE = "none"  # No diff output


class RegexError(Exception):
    """Error raised when a regex pattern is invalid or potentially unsafe."""

    pass


# Patterns that are known to cause catastrophic backtracking (ReDoS)
#
# NOTE: This is a best-effort heuristic, NOT a comprehensive ReDoS detector.
# It catches common dangerous patterns but cannot detect all problematic regexes.
# More sophisticated patterns like overlapping greedy quantifiers (.*.*), nested
# alternations ((a|b)*)*), or backreference loops may still cause issues.
#
# For untrusted input, consider:
# - Using the `regex` library with timeout support
# - Adding execution timeouts to regex operations
# - Restricting allowed regex syntax
_REDOS_PATTERNS = [
    # Nested quantifiers on overlapping groups: (a+)+, (a*)*+, (a+)*
    re.compile(r"\([^)]*[+*][^)]*\)[+*]"),
    # Overlapping alternations with quantifiers: (a|a)+
    re.compile(r"\(([^|)]+)\|+\1[^)]*\)[+*]"),
]


def compile_pattern(pattern: str, name: str = "pattern") -> re.Pattern[str]:
    """Compile a regex pattern with validation.

    Args:
        pattern: The regex pattern string to compile.
        name: Human-readable name for error messages.

    Returns:
        Compiled regex pattern.

    Raises:
        RegexError: If the pattern is invalid or potentially unsafe.
    """
    # Check for potentially dangerous patterns (ReDoS)
    for dangerous in _REDOS_PATTERNS:
        if dangerous.search(pattern):
            raise RegexError(
                f"Potentially unsafe regex {name}: '{pattern}' - "
                "pattern may cause catastrophic backtracking (ReDoS). "
                "Avoid nested quantifiers like (a+)+ or (a|a)+."
            )

    try:
        return re.compile(pattern)
    except re.error as e:
        raise RegexError(f"Invalid regex {name}: '{pattern}' - {e}") from e


def compile_replacements(
    replacements: tuple[tuple[str, str], ...],
) -> tuple[tuple[re.Pattern[str], str], ...]:
    """Compile replacement patterns with validation.

    Args:
        replacements: Tuple of (pattern, replacement) string pairs.

    Returns:
        Tuple of (compiled_pattern, replacement) pairs.

    Raises:
        RegexError: If any pattern is invalid or potentially unsafe.
    """
    result = []
    for i, (pattern, repl) in enumerate(replacements):
        compiled = compile_pattern(pattern, f"replacement[{i}]")
        result.append((compiled, repl))
    return tuple(result)


def compile_redactions(
    redactions: tuple[str, ...],
) -> tuple[re.Pattern[str], ...]:
    """Compile redaction patterns with validation.

    Args:
        redactions: Tuple of pattern strings.

    Returns:
        Tuple of compiled patterns.

    Raises:
        RegexError: If any pattern is invalid or potentially unsafe.
    """
    result = []
    for i, pattern in enumerate(redactions):
        compiled = compile_pattern(pattern, f"redaction[{i}]")
        result.append(compiled)
    return tuple(result)


@dataclass(frozen=True)
class NormalizeOptions:
    """Options for text normalization/preprocessing.

    Use compile_replacements() and compile_redactions() to create
    validated, pre-compiled patterns for the replacements and redactions
    fields.
    """

    strip_ansi: bool = False
    normalize_newlines: bool = False
    trim: bool = False
    collapse_whitespace: bool = False
    ignore_case: bool = False
    # Pre-compiled patterns for replacements: tuple of (compiled_pattern, repl)
    replacements: tuple[tuple[re.Pattern[str], str], ...] = ()
    # Pre-compiled patterns for redactions
    redactions: tuple[re.Pattern[str], ...] = ()


@dataclass(frozen=True)
class CompareResult:
    """Result of a comparison operation."""

    success: bool
    message: str = ""


@dataclass(frozen=True)
class ExpectConfig:
    """Full configuration for an expect operation."""

    mode: CompareMode = CompareMode.EXACT
    normalize: NormalizeOptions = field(default_factory=NormalizeOptions)
    json_ignore_paths: tuple[str, ...] = ()
    jsonl_key_field: str | None = None
    quiet: bool = False
    color: ColorMode = ColorMode.AUTO
    diff_context: int = 3
    diff_format: DiffFormat = DiffFormat.UNIFIED
    update_file: bool = False
