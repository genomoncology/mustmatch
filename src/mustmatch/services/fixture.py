"""
Markdown document fixture for Python code blocks.

Provides an `md` object that gives Python blocks access to the
 document's structure: sections, tables, and metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterator


def _normalize_key(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_")


def _coerce_value(value: str) -> Any:
    """Auto-coerce markdown table cell values to Python types."""
    stripped = value.strip()
    if stripped == "" or stripped == "None":
        return None

    lowered = stripped.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)

    return stripped


def _prepare_headers(headers: list[str]) -> tuple[list[str], set[str]]:
    cleaned_headers: list[str] = []
    coerce_columns: set[str] = set()

    for raw_header in headers:
        header = raw_header.strip()
        lower = header.lower()

        if lower.startswith("str:"):
            normalized = header[4:].strip()
        else:
            normalized = header
            coerce_columns.add(normalized)

        cleaned_headers.append(normalized)

    return cleaned_headers, coerce_columns


def build_table_rows(
    headers: list[str],
    row_values: list[list[str]],
) -> tuple[list[str], list[TableRow]]:
    """Build `TableRow` objects from parser table data."""
    normalized_headers, coerce_columns = _prepare_headers(headers)
    rows = [
        TableRow(
            _data=dict(zip(normalized_headers, row)),
            _coerce=coerce_columns,
        )
        for row in row_values
    ]
    return normalized_headers, rows


@dataclass
class Section:
    """A heading/section in the markdown document."""

    title: str
    level: int  # 1-6
    line: int
    parent: Section | None = None
    children: list[Section] = field(default_factory=list)


@dataclass
class TableRow:
    """A row in a table with dot-notation access to columns."""

    _data: dict[str, str]
    _coerce: set[str] = field(default_factory=set)

    def _get_key_value(self, name: str) -> tuple[str, str]:
        if name in self._data:
            return name, self._data[name]

        normalized_name = _normalize_key(name)
        for key, value in self._data.items():
            if _normalize_key(key) == normalized_name:
                return key, value

        raise KeyError(name)

    def _get_value(self, key: str, raw: str) -> Any:
        if key in self._coerce:
            return _coerce_value(raw)
        return raw

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)

        try:
            key, raw = self._get_key_value(name)
        except KeyError as err:
            raise AttributeError(f"No column {name!r}") from err

        return self._get_value(key, raw)

    def __getitem__(self, key: str) -> Any:
        resolved_key, raw = self._get_key_value(key)
        return self._get_value(resolved_key, raw)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def values(self) -> list[Any]:
        return [self._get_value(key, raw) for key, raw in self._data.items()]

    def items(self) -> list[tuple[str, Any]]:
        return [(key, self._get_value(key, raw)) for key, raw in self._data.items()]


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

    def as_dicts(self) -> list[dict[str, Any]]:
        """Return rows as dictionaries with per-column coercion applied."""
        return [dict(row.items()) for row in self.rows]


class Tables:
    """Collection of tables with dot-notation access by name."""

    def __init__(self, tables: list[Table]) -> None:
        self._tables = tables
        self._by_name: dict[str, Table] = {}
        for table in tables:
            key = _normalize_key(table.name)
            self._by_name[key] = table

    def __getattr__(self, name: str) -> Table:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._by_name:
            return self._by_name[name]
        raise AttributeError(f"No table {name!r}")

    def __getitem__(self, idx: int | str) -> Table:
        if isinstance(idx, int):
            return self._tables[idx]
        key = _normalize_key(idx)
        return self._by_name[key]

    def __iter__(self) -> Iterator[Table]:
        return iter(self._tables)

    def __len__(self) -> int:
        return len(self._tables)


class Sections:
    """Collection of sections with hierarchy access."""

    def __init__(self, sections: list[Section]) -> None:
        self._sections = sections
        self._by_title: dict[str, Section] = {}
        for section in sections:
            key = _normalize_key(section.title)
            self._by_title[key] = section

    def __getattr__(self, name: str) -> Section:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._by_title:
            return self._by_title[name]
        raise AttributeError(f"No section {name!r}")

    def __getitem__(self, idx: int | str) -> Section:
        if isinstance(idx, int):
            return self._sections[idx]
        key = _normalize_key(idx)
        return self._by_title[key]

    def __iter__(self) -> Iterator[Section]:
        return iter(self._sections)

    def __len__(self) -> int:
        return len(self._sections)


@dataclass
class MD:
    """The markdown document fixture.

    Provides access to the document's structure from within Python blocks.
    """

    tables: Tables
    sections: Sections
    current_section: Section | None = None


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

    sections_by_path: dict[tuple[str, ...], Section] = {}
    all_sections: list[Section] = []

    def get_or_create_section(
        *,
        level: int,
        title: str,
        path: list[str],
        line: int,
    ) -> Section:
        path_key = tuple(path)
        if path_key in sections_by_path:
            return sections_by_path[path_key]

        parent: Section | None = None
        if len(path) > 1:
            parent = sections_by_path.get(tuple(path[:-1]))

        section = Section(
            title=title,
            level=level,
            line=line,
            parent=parent,
        )
        if parent is not None:
            parent.children.append(section)

        sections_by_path[path_key] = section
        all_sections.append(section)
        return section

    for block in parse_result.blocks:
        context_lines = getattr(block, "context_lines", [])
        for idx, title in enumerate(block.context):
            get_or_create_section(
                level=idx + 1,
                title=title,
                path=block.context[: idx + 1],
                line=context_lines[idx] if idx < len(context_lines) else 0,
            )

    for parser_table in parse_result.tables:
        context_lines = getattr(parser_table, "context_lines", [])
        for idx, title in enumerate(parser_table.context):
            get_or_create_section(
                level=idx + 1,
                title=title,
                path=parser_table.context[: idx + 1],
                line=context_lines[idx] if idx < len(context_lines) else 0,
            )

    tables: list[Table] = []
    for parser_table in parse_result.tables:
        table_name = parser_table.context[-1] if parser_table.context else "unnamed"
        if parser_table.context:
            section = sections_by_path.get(tuple(parser_table.context))
        else:
            section = None

        normalized_headers, rows = build_table_rows(
            parser_table.headers,
            parser_table.rows,
        )

        tables.append(
            Table(
                name=table_name,
                headers=normalized_headers,
                rows=rows,
                line=parser_table.line_start,
                section=section,
            )
        )

    current_section = None
    if current_block and current_block.context:
        current_section = sections_by_path.get(tuple(current_block.context))

    return MD(
        tables=Tables(tables),
        sections=Sections(all_sections),
        current_section=current_section,
    )
