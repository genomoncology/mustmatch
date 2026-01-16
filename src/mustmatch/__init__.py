"""
mustmatch: CLI output assertion tool for documentation testing.

Pipe command output to `mustmatch` to verify it matches expected values.
Test bash and Python code blocks in markdown documentation.
"""

from pathlib import Path

from .cli import main
from .compare import compare
from .config import (
    ColorMode,
    CompareMode,
    CompareResult,
    ExpectConfig,
    NormalizeOptions,
    RegexError,
    compile_pattern,
    compile_redactions,
    compile_replacements,
)
from .normalize import preprocess
from .pytest import MarkdownTest
from .python_exec import create_namespace
from .version import __version__


def check_md_file(
    path: str | Path,
    *,
    lang: str = "all",
    memory: bool = False,
) -> bool:
    """Check all code blocks in a markdown file.

    This is the primary API for programmatic testing of markdown files.
    It runs all code blocks (bash and/or Python) and returns whether
    all blocks passed.

    Args:
        path: Path to the markdown file.
        lang: Language to test: "bash", "python", or "all" (default: "all").
        memory: For Python, share state between blocks (default: False).

    Returns:
        True if all blocks passed, False otherwise.

    Example:
        >>> from mustmatch import check_md_file
        >>> check_md_file("docs/getting-started.md")
        True
        >>> check_md_file("docs/python-tutorial.md", lang="python", memory=True)
        True
    """
    from .mdtest import TestConfig, run_file

    path = Path(path)
    config = TestConfig(
        quiet=True,
        lang=lang,
        memory=memory,
    )

    result = run_file(path, config)
    return result.failed == 0 and result.timeout == 0 and result.error is None


__all__ = [
    "__version__",
    "main",
    "compare",
    "preprocess",
    "check_md_file",
    "create_namespace",
    "CompareMode",
    "CompareResult",
    "ColorMode",
    "ExpectConfig",
    "NormalizeOptions",
    "RegexError",
    "compile_pattern",
    "compile_redactions",
    "compile_replacements",
    "MarkdownTest",
]
