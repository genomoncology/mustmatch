"""Output formatting and diff generation."""

import difflib
import sys

from .config import ColorMode, CompareResult, DiffFormat, MatchConfig


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


def side_by_side_diff(actual: str, expected: str, width: int = 80) -> str:
    """Generate side-by-side diff between actual and expected."""
    actual_lines = actual.splitlines()
    expected_lines = expected.splitlines()

    col_width = (width - 3) // 2
    result = []
    result.append(f"{'expected':<{col_width}} | {'actual':<{col_width}}")
    result.append("-" * col_width + " | " + "-" * col_width)

    matcher = difflib.SequenceMatcher(None, expected_lines, actual_lines)

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            for exp, act in zip(expected_lines[i1:i2], actual_lines[j1:j2]):
                exp_trunc = exp[:col_width].ljust(col_width)
                act_trunc = act[:col_width].ljust(col_width)
                result.append(f"{exp_trunc} | {act_trunc}")
        elif op == "replace":
            for exp in expected_lines[i1:i2]:
                exp_trunc = exp[:col_width].ljust(col_width)
                result.append(f"{exp_trunc} | <different>")
            for act in actual_lines[j1:j2]:
                act_trunc = act[:col_width].ljust(col_width)
                result.append(f"{'<different>':<{col_width}} | {act_trunc}")
        elif op == "delete":
            for exp in expected_lines[i1:i2]:
                exp_trunc = exp[:col_width].ljust(col_width)
                result.append(f"{exp_trunc} | <missing>")
        elif op == "insert":
            for act in actual_lines[j1:j2]:
                act_trunc = act[:col_width].ljust(col_width)
                result.append(f"{'<extra>':<{col_width}} | {act_trunc}")

    return "\n".join(result)


def inline_diff(actual: str, expected: str) -> str:
    """Generate inline word-level diff."""
    actual_words = actual.split()
    expected_words = expected.split()

    result = []
    matcher = difflib.SequenceMatcher(None, expected_words, actual_words)

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result.extend(expected_words[i1:i2])
        elif op == "replace":
            result.append("[-" + " ".join(expected_words[i1:i2]) + "-]")
            result.append("[+" + " ".join(actual_words[j1:j2]) + "+]")
        elif op == "delete":
            result.append("[-" + " ".join(expected_words[i1:i2]) + "-]")
        elif op == "insert":
            result.append("[+" + " ".join(actual_words[j1:j2]) + "+]")

    return " ".join(result)


def format_diff(actual: str, expected: str, config: MatchConfig) -> str:
    """Format diff according to config.diff_format."""
    if config.diff_format == DiffFormat.NONE:
        return ""
    if config.diff_format == DiffFormat.SIDE_BY_SIDE:
        return side_by_side_diff(actual, expected)
    if config.diff_format == DiffFormat.INLINE:
        return inline_diff(actual, expected)
    return unified_diff(actual, expected, context=config.diff_context)


def colorize_diff(diff: str) -> str:
    """Add ANSI colors to unified diff."""
    lines = []
    for line in diff.splitlines(keepends=True):
        if line.startswith("+++") or line.startswith("---"):
            lines.append(f"\033[1m{line}\033[0m")
        elif line.startswith("+"):
            lines.append(f"\033[32m{line}\033[0m")
        elif line.startswith("-"):
            lines.append(f"\033[31m{line}\033[0m")
        elif line.startswith("@@"):
            lines.append(f"\033[36m{line}\033[0m")
        else:
            lines.append(line)
    return "".join(lines)


def should_use_color(color_mode: ColorMode) -> bool:
    """Determine if color should be used."""
    if color_mode == ColorMode.ALWAYS:
        return True
    if color_mode == ColorMode.NEVER:
        return False
    return sys.stderr.isatty()


def format_error(result: CompareResult, config: MatchConfig) -> str:
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
