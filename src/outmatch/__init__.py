"""
outmatch: CLI output assertion tool for documentation testing.

Pipe command output to `outmatch` to verify it matches expected values.
Designed for use with mktestdocs to test CLI examples in documentation.
"""

from .cli import main
from .compare import compare
from .config import (
    ColorMode,
    CompareMode,
    CompareResult,
    ExpectConfig,
    NormalizeOptions,
)
from .normalize import preprocess
from .pytest import MarkdownTest
from .version import __version__

__all__ = [
    "__version__",
    "main",
    "compare",
    "preprocess",
    "CompareMode",
    "CompareResult",
    "ColorMode",
    "ExpectConfig",
    "NormalizeOptions",
    "MarkdownTest",
]
