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
    MatchConfig,
    NormalizeOptions,
)
from .detect import ValueType, detect_type
from .normalize import normalize, preprocess
from .version import __version__


def check_md_file(
    path: str | Path,
    *,
    lang: str = "all",
    memory: bool = False,
) -> bool:
    """Check all code blocks in a markdown file.

    Args:
        path: Path to the markdown file.
        lang: Language to test: "bash", "python", or "all".
        memory: For Python, share state between blocks.

    Returns:
        True if all blocks passed, False otherwise.
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


# Backward compatibility
ExpectConfig = MatchConfig


__all__ = [
    "__version__",
    "main",
    "compare",
    "normalize",
    "preprocess",
    "check_md_file",
    "detect_type",
    "ValueType",
    "CompareMode",
    "CompareResult",
    "ColorMode",
    "MatchConfig",
    "ExpectConfig",
    "NormalizeOptions",
]
