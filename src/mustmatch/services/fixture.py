"""
Markdown document fixture for Python code blocks.

Provides an `md` object that gives Python blocks access to the
document's structure: sections, tables, and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Section:
    """A heading/section in the markdown document."""

    title: str
    level: int  # 1-6
    line: int
    parent: Section | None = None
    children: list[Section] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Section({self.title!r}, level={self.level})"


@dataclass
class TableRow:
    """A row in a table with dot-notation access to columns."""

    _data: dict[str, str]

    def __getattr__(self, name: str) -> str:
        if name.startswith("_"):
            raise AttributeError(name)
        # Try exact match first
        if name in self._data:
            return self._data[name]
        # Try case-insensitive match
        for key, value in self._data.items():
            if key.lower().replace(" ", "_") == name.lower():
                return value
        raise AttributeError(f"No column {name!r}")

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __repr__(self) -> str:
        return f"TableRow({self._data})"

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def values(self) -> list[str]:
        return list(self._data.values())

    def items(self) -> list[tuple[str, str]]:
        return list(self._data.items())


@dataclass
class Table:
    """A table in the markdown document."""

    name: str  # From heading context
    headers: list[str]
    rows: list[TableRow]
    line: int
    section: Section | None = None

    def __iter__(self) -> Iterator[TableRow]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> TableRow:
        return self.rows[idx]

    def __repr__(self) -> str:
        return f"Table({self.name!r}, {len(self.rows)} rows)"

    def as_dicts(self) -> list[dict[str, str]]:
        """Return rows as plain dictionaries."""
        return [row._data for row in self.rows]


class Tables:
    """Collection of tables with dot-notation access by name."""

    def __init__(self, tables: list[Table]) -> None:
        self._tables = tables
        self._by_name: dict[str, Table] = {}
        for t in tables:
            # Index by normalized name (lowercase, underscores)
            key = t.name.lower().replace(" ", "_").replace("-", "_")
            self._by_name[key] = t

    def __getattr__(self, name: str) -> Table:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._by_name:
            return self._by_name[name]
        raise AttributeError(f"No table {name!r}")

    def __getitem__(self, idx: int | str) -> Table:
        if isinstance(idx, int):
            return self._tables[idx]
        return self._by_name[idx]

    def __iter__(self) -> Iterator[Table]:
        return iter(self._tables)

    def __len__(self) -> int:
        return len(self._tables)

    def __repr__(self) -> str:
        names = [t.name for t in self._tables]
        return f"Tables({names})"


class Sections:
    """Collection of sections with hierarchy access."""

    def __init__(self, sections: list[Section]) -> None:
        self._sections = sections
        self._by_title: dict[str, Section] = {}
        for s in sections:
            key = s.title.lower().replace(" ", "_").replace("-", "_")
            self._by_title[key] = s

    def __getattr__(self, name: str) -> Section:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._by_title:
            return self._by_title[name]
        raise AttributeError(f"No section {name!r}")

    def __getitem__(self, idx: int | str) -> Section:
        if isinstance(idx, int):
            return self._sections[idx]
        return self._by_title[idx]

    def __iter__(self) -> Iterator[Section]:
        return iter(self._sections)

    def __len__(self) -> int:
        return len(self._sections)

    def __repr__(self) -> str:
        return f"Sections({len(self._sections)} sections)"


@dataclass
class MD:
    """The markdown document fixture.

    Provides access to the document's structure from within Python blocks.
    """

    tables: Tables
    sections: Sections
    current_section: Section | None = None

    def __repr__(self) -> str:
        return f"MD(tables={self.tables}, sections={self.sections})"


def create_md_fixture(
    parse_result,  # ParseResult from parser
    current_block=None,  # Block being executed
) -> MD:
    """Create an MD fixture from a ParseResult.

    Args:
        parse_result: The ParseResult from parse_markdown()
        current_block: The Block currently being executed (for context)

    Returns:
        An MD object with access to document structure
    """

    # Build sections from heading contexts in blocks and tables
    # We need to reconstruct the section hierarchy
    seen_headings: dict[tuple[int, str], Section] = {}
    all_sections: list[Section] = []

    def get_or_create_section(level: int, title: str, context: list[str]) -> Section:
        key = (level, title)
        if key in seen_headings:
            return seen_headings[key]

        # Find parent from context
        parent = None
        if len(context) > 1:
            # Parent is the previous item in context
            parent_title = context[-2] if len(context) >= 2 else None
            if parent_title:
                for s in all_sections:
                    if s.title == parent_title and s.level < level:
                        parent = s
                        break

        section = Section(
            title=title,
            level=level,
            line=0,  # We don't have exact line info here
            parent=parent,
        )
        if parent:
            parent.children.append(section)

        seen_headings[key] = section
        all_sections.append(section)
        return section

    # Extract sections from blocks and tables contexts
    for block in parse_result.blocks:
        for i, title in enumerate(block.context):
            level = i + 1  # Approximate level from context depth
            get_or_create_section(level, title, block.context[: i + 1])

    for table in parse_result.tables:
        for i, title in enumerate(table.context):
            level = i + 1
            get_or_create_section(level, title, table.context[: i + 1])

    # Build tables
    tables: list[Table] = []
    for t in parse_result.tables:
        name = t.context[-1] if t.context else "unnamed"
        section = None
        if t.context:
            key = (len(t.context), t.context[-1])
            section = seen_headings.get(key)

        rows = [
            TableRow(_data=dict(zip(t.headers, row)))
            for row in t.rows
        ]
        tables.append(Table(
            name=name,
            headers=t.headers,
            rows=rows,
            line=t.line_start,
            section=section,
        ))

    # Find current section
    current_section = None
    if current_block and current_block.context:
        key = (len(current_block.context), current_block.context[-1])
        current_section = seen_headings.get(key)

    return MD(
        tables=Tables(tables),
        sections=Sections(all_sections),
        current_section=current_section,
    )
