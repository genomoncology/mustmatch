"""
Text normalization services for mustmatch.

Provides preprocessing steps like ANSI stripping, whitespace handling, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ANSI escape sequence pattern
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07")


@dataclass
class NormalizeOptions:
    """Options for text normalization."""

    strip_ansi: bool = True  # Always strip ANSI
    normalize_newlines: bool = True  # CRLF -> LF
    trim: bool = True  # Strip leading/trailing whitespace
    ignore_case: bool = False  # Lowercase for comparison


def normalize(text: str, options: NormalizeOptions | None = None) -> str:
    """Apply normalization steps to text.

    Args:
        text: Input text to normalize.
        options: Normalization options (uses defaults if None).

    Returns:
        Normalized text.
    """
    if options is None:
        options = NormalizeOptions()

    # Always normalize newlines first (CRLF -> LF)
    if options.normalize_newlines:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip ANSI escape sequences
    if options.strip_ansi:
        text = strip_ansi(text)

    # Trim whitespace
    if options.trim:
        text = text.strip()

    # Case normalization
    if options.ignore_case:
        text = text.lower()

    return text


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.

    Handles:
        - Color codes: \\x1b[31m (red), \\x1b[0m (reset)
        - Cursor movement: \\x1b[2J (clear screen)
        - OSC sequences: \\x1b]0;title\\x07

    Args:
        text: Text potentially containing ANSI sequences.

    Returns:
        Text with ANSI sequences removed.
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)






def default_options() -> NormalizeOptions:
    """Return default normalization options.

    Always enabled:
        - Strip ANSI escape sequences
        - Normalize newlines (CRLF -> LF)
        - Trim leading/trailing whitespace
    """
    return NormalizeOptions(
        strip_ansi=True,
        normalize_newlines=True,
        trim=True,
        ignore_case=False,
    )
