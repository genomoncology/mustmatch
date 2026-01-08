"""Text normalization and preprocessing functions."""

import re

from .config import NormalizeOptions

# ANSI escape sequence pattern
_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_ESCAPE.sub("", text)


def normalize_newlines(text: str) -> str:
    """Convert CRLF and CR to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces."""
    return re.sub(r"\s+", " ", text)


def apply_replacements(
    text: str,
    replacements: tuple[tuple[str, str], ...],
) -> str:
    """Apply regex replacements to text."""
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    return text


def apply_redactions(text: str, patterns: tuple[str, ...]) -> str:
    """Replace regex patterns with <redacted>."""
    for pattern in patterns:
        text = re.sub(pattern, "<redacted>", text)
    return text


def preprocess(text: str, options: NormalizeOptions) -> str:
    """Apply all preprocessing steps to text based on options."""
    if options.strip_ansi:
        text = strip_ansi(text)
    if options.normalize_newlines:
        text = normalize_newlines(text)
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
