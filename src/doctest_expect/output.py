"""Output formatting and diff generation."""

import difflib
import sys

from .config import ColorMode, CompareResult, ExpectConfig


def unified_diff(actual: str, expected: str, context: int = 3) -> str:
    """Generate unified diff between actual and expected."""
    actual_lines = actual.splitlines(keepends=True)
    expected_lines = expected.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="expected",
        tofile="actual",
        n=context,
    )
    return "".join(diff)


def colorize_diff(diff: str) -> str:
    """Add ANSI colors to unified diff."""
    lines = []
    for line in diff.splitlines(keepends=True):
        if line.startswith("+++") or line.startswith("---"):
            lines.append(f"\033[1m{line}\033[0m")  # Bold
        elif line.startswith("+"):
            lines.append(f"\033[32m{line}\033[0m")  # Green
        elif line.startswith("-"):
            lines.append(f"\033[31m{line}\033[0m")  # Red
        elif line.startswith("@@"):
            lines.append(f"\033[36m{line}\033[0m")  # Cyan
        else:
            lines.append(line)
    return "".join(lines)


def should_use_color(color_mode: ColorMode) -> bool:
    """Determine if color should be used based on mode and terminal."""
    if color_mode == ColorMode.ALWAYS:
        return True
    if color_mode == ColorMode.NEVER:
        return False
    return sys.stderr.isatty()


def format_error(result: CompareResult, config: ExpectConfig) -> str:
    """Format error message for output."""
    use_color = should_use_color(config.color)
    msg = result.message

    if use_color and "---" in msg:
        msg = colorize_diff(msg)
        return f"FAIL: {msg}"
    elif use_color:
        return f"\033[31mFAIL:\033[0m {msg}"
    else:
        return f"FAIL: {msg}"
