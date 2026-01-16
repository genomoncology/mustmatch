"""
Markdown parser using Mistune AST.

Extracts code blocks and tables from markdown files with heading context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import mistune


@lru_cache(maxsize=1)
def _get_markdown_parser():
    """Get cached mistune parser instance."""
    return mistune.create_markdown(renderer="ast", plugins=["table"])


@dataclass
class Block:
    """A code block extracted from markdown."""

    language: str  # "bash" or "python"
    content: str  # The code
    line_start: int  # Source location (1-indexed)
    name: str | None  # From nearest preceding heading
    context: list[str] = field(default_factory=list)  # Heading hierarchy
    directives: dict[str, str] = field(default_factory=dict)  # e.g., skip, timeout


@dataclass
class Table:
    """A table extracted from markdown."""

    headers: list[str]  # Column names
    rows: list[list[str]]  # Row data
    line_start: int  # Source location (1-indexed)
    context: list[str] = field(default_factory=list)  # Heading hierarchy


@dataclass
class ParseResult:
    """Result of parsing a markdown file."""

    blocks: list[Block] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)


def _extract_text(children: list[dict]) -> str:
    """Extract plain text from AST children nodes."""
    if not children:
        return ""
    parts = []
    for child in children:
        if child["type"] == "text":
            parts.append(child["raw"])
        elif child["type"] == "codespan":
            parts.append(child["raw"])
        elif "children" in child:
            parts.append(_extract_text(child["children"]))
    return "".join(parts)


def _parse_info_string(info: str) -> tuple[str, dict[str, str]]:
    """Parse language and directives from info string.

    Examples:
        "bash" -> ("bash", {})
        "python skip" -> ("python", {"skip": ""})
        "bash timeout=5" -> ("bash", {"timeout": "5"})
        "python skip=ci" -> ("python", {"skip": "ci"})
    """
    if not info:
        return "", {}

    parts = info.split()
    if not parts:
        return "", {}

    language = parts[0].lower()
    directives: dict[str, str] = {}

    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            directives[key] = value
        else:
            directives[part] = ""

    return language, directives


def _count_newlines_before(content: str, pos: int) -> int:
    """Count newlines before a position in content."""
    return content[:pos].count("\n")


def _parse_table_token(token: dict) -> tuple[list[str], list[list[str]]]:
    """Parse a table token into headers and rows."""
    headers = []
    rows = []

    # Extract headers and rows from table
    if "children" in token:
        for child in token["children"]:
            if child["type"] == "table_head":
                # Headers are directly under table_head as table_cell elements
                if "children" in child:
                    for cell in child["children"]:
                        if cell["type"] == "table_cell":
                            text = _extract_text(cell.get("children", []))
                            headers.append(text.strip())
            elif child["type"] == "table_body":
                if "children" in child:
                    for row in child["children"]:
                        if row["type"] == "table_row" and "children" in row:
                            row_data = []
                            for cell in row["children"]:
                                if cell["type"] == "table_cell":
                                    text = _extract_text(cell.get("children", []))
                                    row_data.append(text.strip())
                            if row_data:
                                rows.append(row_data)

    return headers, rows


def parse_markdown(content: str) -> ParseResult:
    """Extract code blocks and tables from markdown using Mistune AST.

    Args:
        content: Raw markdown content.

    Returns:
        ParseResult with blocks and tables, each with heading context.
    """
    md = _get_markdown_parser()
    tokens = md(content)

    blocks: list[Block] = []
    tables: list[Table] = []
    heading_stack: list[tuple[int, str]] = []  # (level, text)

    # Track position for line numbers
    lines = content.split("\n")
    line_positions: list[int] = []
    pos = 0
    for line in lines:
        line_positions.append(pos)
        pos += len(line) + 1  # +1 for newline

    def find_line_number(search_text: str, start_line: int = 0) -> int:
        """Find the line number where search_text appears."""
        for i, line in enumerate(lines[start_line:], start=start_line):
            if search_text in line:
                return i + 1  # 1-indexed
        return 1

    current_search_line = 0

    def process_tokens(token_list: list[dict]) -> None:
        nonlocal current_search_line

        for token in token_list:
            token_type = token.get("type", "")

            if token_type == "heading":
                level = token.get("attrs", {}).get("level", 1)
                text = _extract_text(token.get("children", []))

                # Pop headings at same or higher level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))

            elif token_type == "block_code":
                info = token.get("attrs", {}).get("info", "") or ""
                raw = token.get("raw", "")
                marker = token.get("marker", "```")  # Handle 4-backtick fences

                language, directives = _parse_info_string(info)

                if language in ("bash", "python", "sh"):
                    # Normalize sh to bash
                    if language == "sh":
                        language = "bash"

                    # Find line number using the actual marker (``` or ````)
                    code_marker = f"{marker}{info}" if info else marker
                    line_num = find_line_number(code_marker, current_search_line)
                    # Advance search past this line to avoid matching same fence again
                    current_search_line = line_num + 1

                    blocks.append(
                        Block(
                            language=language,
                            content=raw,
                            line_start=line_num,
                            name=heading_stack[-1][1] if heading_stack else None,
                            context=[h[1] for h in heading_stack],
                            directives=directives,
                        )
                    )

            elif token_type == "table":
                headers, rows = _parse_table_token(token)
                if headers:
                    # Find line number by looking for table header separator
                    line_num = find_line_number("|---", current_search_line)
                    if line_num > 1:
                        line_num -= 1  # Go to header row
                    # Advance search past this table to avoid matching same table again
                    current_search_line = line_num + 1

                    tables.append(
                        Table(
                            headers=headers,
                            rows=rows,
                            line_start=line_num,
                            context=[h[1] for h in heading_stack],
                        )
                    )

            # Recurse into children
            if "children" in token:
                process_tokens(token["children"])

    process_tokens(tokens)

    return ParseResult(blocks=blocks, tables=tables)


def get_table_for_block(
    result: ParseResult, block: Block
) -> Table | None:
    """Get the table immediately preceding a block (for test fixtures).

    A table is considered "preceding" if it's under the same heading context
    and appears before the block in the file.
    """
    preceding_table = None

    for table in result.tables:
        # Table must be before the block
        if table.line_start >= block.line_start:
            continue

        # Table should share context with the block
        if table.context == block.context or (
            len(table.context) <= len(block.context)
            and table.context == block.context[: len(table.context)]
        ):
            # Keep the closest preceding table
            if preceding_table is None or table.line_start > preceding_table.line_start:
                preceding_table = table

    return preceding_table
