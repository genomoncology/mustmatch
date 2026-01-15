"""Shared markdown parsing utilities.

This module provides common parsing functions used by both mdtest.py and pytest.py
to avoid code duplication. Supports both bash and Python code blocks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Supported fence markers by language
BASH_FENCES = frozenset({"```bash", "```sh", "```shell"})
PYTHON_FENCES = frozenset({"```python", "```py"})

# Combined for lookup
SUPPORTED_LANGS = {
    "bash": BASH_FENCES,
    "python": PYTHON_FENCES,
}


@dataclass
class ParsedBlock:
    """A parsed code block from markdown."""

    content: str
    line_start: int
    line_end: int
    name: str | None = None
    lang: str = "bash"  # "bash" or "python"


def find_block_name(lines: list[str], fence_index: int) -> str | None:
    """Find the name for a bash block from preceding heading or comment.

    Searches backwards from the fence line to find:
    - A markdown heading (# Title)
    - An HTML comment (<!-- name -->)
    - A bash comment at the start of the block content

    Args:
        lines: All lines of the markdown file.
        fence_index: Index of the fence opening line (0-indexed).

    Returns:
        Block name if found, None otherwise.
    """
    # Search up to 10 lines backwards for a heading or comment
    start = max(fence_index - 10, 0)
    for i in range(fence_index - 1, start - 1, -1):
        line = lines[i].strip()

        # Markdown heading
        if line.startswith("#"):
            return line.lstrip("#").strip()

        # HTML comment
        if line.startswith("<!--") and line.endswith("-->"):
            return line[4:-3].strip()

    return None


def should_skip_block(lines: list[str], fence_index: int) -> bool:
    """Check if a block should be skipped based on preceding HTML comment.

    Looks for <!-- mustmatch: skip --> in the few lines before the fence.

    Args:
        lines: All lines of the markdown file.
        fence_index: Index of the fence opening line (0-indexed).

    Returns:
        True if the block should be skipped, False otherwise.
    """
    # Check up to 3 lines before the fence for skip directive
    start = max(fence_index - 3, 0)
    for i in range(fence_index - 1, start - 1, -1):
        line = lines[i].strip()
        if not line:
            continue
        # Check for skip directive
        if "mustmatch:" in line.lower() and "skip" in line.lower():
            return True
        # Stop at non-empty, non-comment lines
        if not line.startswith("<!--"):
            break
    return False


def _count_backticks(line: str) -> int:
    """Count leading backticks in a line (after stripping whitespace)."""
    stripped = line.strip()
    count = 0
    for char in stripped:
        if char == "`":
            count += 1
        else:
            break
    return count


def parse_code_blocks(
    content: str,
    lang: str = "bash",
    include_name: bool = True,
) -> Iterator[ParsedBlock]:
    """Parse markdown content and yield code blocks of specified language.

    This is the shared implementation used by both mdtest and pytest integrations.
    Properly handles nested fences (e.g., ````markdown containing ```python).

    Args:
        content: Markdown file content.
        lang: Language to parse: "bash", "python", or "all".
        include_name: If True, attempt to find names for blocks from headings/comments.

    Yields:
        ParsedBlock instances for each matching code block found.
    """
    lines = content.split("\n")

    # Determine which fences to look for
    if lang == "all":
        target_fences = BASH_FENCES | PYTHON_FENCES
    else:
        target_fences = SUPPORTED_LANGS.get(lang, BASH_FENCES)

    in_block = False
    current_lang = "bash"
    block_start = 0
    block_lines: list[str] = []
    block_name: str | None = None
    current_fence_level = 0  # Number of backticks for current fence

    # Track outer fences that contain our target blocks (e.g., ````markdown)
    outer_fence_level = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        backtick_count = _count_backticks(stripped)

        # Check if we're entering or exiting an outer fence (4+ backticks)
        if backtick_count >= 4:
            if outer_fence_level == 0:
                # Entering an outer fence
                outer_fence_level = backtick_count
            elif (
                backtick_count == outer_fence_level
                and stripped == "`" * backtick_count
            ):
                # Exiting the outer fence (exact match of backticks only)
                outer_fence_level = 0
            continue

        # Skip processing if we're inside an outer fence
        if outer_fence_level > 0:
            continue

        # Check for fence opening (only 3-backtick fences)
        detected_lang = None
        if not in_block and backtick_count == 3:
            if stripped in BASH_FENCES and stripped in target_fences:
                detected_lang = "bash"
            elif stripped in PYTHON_FENCES and stripped in target_fences:
                detected_lang = "python"

        if detected_lang:
            # Check for skip directive
            if should_skip_block(lines, i):
                # Skip this block - read until closing fence and discard
                in_block = True
                current_lang = detected_lang
                current_fence_level = 3
                block_lines = []
                block_name = None
                # Mark as skipped (will be filtered out when yielding)
                block_start = -1  # Sentinel value to indicate skip
            else:
                in_block = True
                current_lang = detected_lang
                current_fence_level = 3
                block_start = i + 2  # Line number (1-indexed, after fence)
                block_lines = []
                block_name = find_block_name(lines, i) if include_name else None

        # Check for fence closing (exactly 3 backticks)
        elif stripped == "```" and in_block and current_fence_level == 3:
            in_block = False
            current_fence_level = 0

            # Skip blocks marked with sentinel value (-1)
            if block_start == -1:
                continue

            block_content = "\n".join(block_lines)

            # Try to get name from first comment if not found from heading
            # Both bash and python use # for comments
            if include_name and block_name is None and block_lines:
                first_line = block_lines[0].strip()
                if first_line.startswith("#"):
                    comment_match = re.match(r"^#\s*(.+)$", first_line)
                    if comment_match:
                        block_name = comment_match.group(1).strip()

            yield ParsedBlock(
                content=block_content,
                line_start=block_start,
                line_end=i + 1,  # 1-indexed
                name=block_name,
                lang=current_lang,
            )

        # Collect block content
        elif in_block:
            block_lines.append(line)


def parse_bash_blocks(content: str, include_name: bool = True) -> Iterator[ParsedBlock]:
    """Parse markdown content and yield bash code blocks.

    This is a convenience function that wraps parse_code_blocks for bash.

    Args:
        content: Markdown file content.
        include_name: If True, attempt to find names for blocks from headings/comments.

    Yields:
        ParsedBlock instances for each bash/sh/shell code block found.
    """
    yield from parse_code_blocks(content, lang="bash", include_name=include_name)


def parse_python_blocks(
    content: str, include_name: bool = True
) -> Iterator[ParsedBlock]:
    """Parse markdown content and yield Python code blocks.

    Args:
        content: Markdown file content.
        include_name: If True, attempt to find names for blocks from headings/comments.

    Yields:
        ParsedBlock instances for each python/py code block found.
    """
    yield from parse_code_blocks(content, lang="python", include_name=include_name)


def parse_markdown_file(
    path: Path,
    include_name: bool = True,
    lang: str = "bash",
) -> Iterator[ParsedBlock]:
    """Parse a markdown file and yield code blocks.

    Args:
        path: Path to the markdown file.
        include_name: If True, attempt to find names for blocks.
        lang: Language to parse: "bash", "python", or "all".

    Yields:
        ParsedBlock instances for each matching code block.

    Raises:
        OSError: If file cannot be read.
    """
    content = path.read_text()
    yield from parse_code_blocks(content, lang=lang, include_name=include_name)
