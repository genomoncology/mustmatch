"""
mustmatch: CLI output assertion tool for documentation testing.

Pipe command output to `mustmatch` to verify it matches expected values.
Test bash and Python code blocks in markdown documentation.
"""

from pathlib import Path

from .cli import main
from .services.comparator import CompareMode, CompareResult, compare
from .services.normalizer import NormalizeOptions, normalize
from .services.parser import Block, ParseResult, Table, parse_markdown
from .services.runner import RunResult, run_bash, run_python
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
    from .services.runner import create_python_namespace

    path = Path(path)
    content = path.read_text()
    result = parse_markdown(content)

    # Filter blocks by language
    blocks = [
        b for b in result.blocks
        if lang == "all" or b.language == lang
    ]

    if not blocks:
        return True

    # Run blocks
    namespace = create_python_namespace() if memory else None

    for block in blocks:
        if block.language == "bash":
            run_result = run_bash(block.content, cwd=path.parent)
            if run_result.exit_code != 0:
                return False
        elif block.language == "python":
            if memory:
                run_result = run_python(block.content, globals_dict=namespace)
            else:
                run_result = run_python(block.content)
            if run_result.exit_code != 0:
                return False

    return True


__all__ = [
    "__version__",
    "main",
    "check_md_file",
    # Services
    "compare",
    "normalize",
    "parse_markdown",
    "run_bash",
    "run_python",
    # Types
    "CompareMode",
    "CompareResult",
    "NormalizeOptions",
    "Block",
    "Table",
    "ParseResult",
    "RunResult",
]
