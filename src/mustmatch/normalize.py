"""Text normalization and preprocessing functions."""

from __future__ import annotations

import re

from .config import NormalizeOptions

# ANSI escape sequence pattern
_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Pre-compiled pattern for whitespace collapsing
_WHITESPACE = re.compile(r"\s+")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_ESCAPE.sub("", text)


def normalize_newlines(text: str) -> str:
    """Convert CRLF and CR to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces."""
    return _WHITESPACE.sub(" ", text)


def apply_replacements(
    text: str,
    replacements: tuple[tuple[re.Pattern[str], str], ...],
) -> str:
    """Apply pre-compiled regex replacements to text."""
    for pattern, repl in replacements:
        text = pattern.sub(repl, text)
    return text


def apply_redactions(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
) -> str:
    """Replace patterns with <redacted>."""
    for pattern in patterns:
        text = pattern.sub("<redacted>", text)
    return text


def normalize(text: str) -> str:
    """Apply standard normalization (always-on).

    - Strip ANSI escape sequences
    - Normalize newlines (CRLF -> LF)
    """
    text = strip_ansi(text)
    text = normalize_newlines(text)
    return text


def preprocess(text: str, options: NormalizeOptions | None = None) -> str:
    """Apply all preprocessing steps to text.

    Always applies:
    - Strip ANSI escape sequences
    - Normalize newlines (CRLF -> LF)

    Optionally applies (based on options):
    - Replacements
    - Redactions
    - Trim whitespace
    - Collapse whitespace
    - Lowercase (ignore_case)
    """
    # Always-on normalizations
    text = normalize(text)

    if options is None:
        return text

    # Optional normalizations
    if options.replacements:
        text = apply_replacements(text, options.replacements)
    if options.redactions:
        text = apply_redactions(text, options.redactions)
    if options.trim:
        text = text.strip()
    if options.collapse_whitespace:
        text = collapse_whitespace(text)
    if options.ignore_case:
        text = text.lower()

    return text
