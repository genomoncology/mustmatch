"""Shared markdown parsing utilities.

This module provides common parsing functions used by both mdtest.py and pytest.py
to avoid code duplication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Supported bash fence markers
BASH_FENCES = frozenset({"```bash", "```sh", "```shell"})


@dataclass
class ParsedBlock:
    """A parsed bash code block from markdown."""

    content: str
    line_start: int
    line_end: int
    name: str | None = None


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


def parse_bash_blocks(content: str, include_name: bool = True) -> Iterator[ParsedBlock]:
    """Parse markdown content and yield bash code blocks.

    This is the shared implementation used by both mdtest and pytest integrations.

    Args:
        content: Markdown file content.
        include_name: If True, attempt to find names for blocks from headings/comments.

    Yields:
        ParsedBlock instances for each bash/sh/shell code block found.
    """
    lines = content.split("\n")

    in_bash_block = False
    block_start = 0
    block_lines: list[str] = []
    block_name: str | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for bash fence opening
        if stripped in BASH_FENCES:
            in_bash_block = True
            block_start = i + 2  # Line number (1-indexed, after fence)
            block_lines = []
            block_name = find_block_name(lines, i) if include_name else None

        # Check for fence closing
        elif stripped == "```" and in_bash_block:
            in_bash_block = False
            block_content = "\n".join(block_lines)

            # Try to get name from first bash comment if not found from heading
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
            )

        # Collect block content
        elif in_bash_block:
            block_lines.append(line)


def parse_markdown_file(path: Path, include_name: bool = True) -> Iterator[ParsedBlock]:
    """Parse a markdown file and yield bash code blocks.

    Args:
        path: Path to the markdown file.
        include_name: If True, attempt to find names for blocks.

    Yields:
        ParsedBlock instances for each bash code block.

    Raises:
        OSError: If file cannot be read.
    """
    content = path.read_text()
    yield from parse_bash_blocks(content, include_name)
