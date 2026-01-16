"""
Services layer for mustmatch.

This is the core logic layer. Both CLI and pytest plugin delegate to these services.
"""

from .comparator import CompareResult, compare, contains, exact, json_match, regex
from .fixture import MD, Section, TableRow, Tables, create_md_fixture
from .fixture import Table as MDTable
from .normalizer import NormalizeOptions, normalize
from .parser import Block, ParseResult, Table, parse_markdown
from .runner import RunResult, run_bash, run_python

__all__ = [
    # Comparator
    "CompareResult",
    "compare",
    "exact",
    "contains",
    "regex",
    "json_match",
    # Fixture
    "MD",
    "Section",
    "MDTable",
    "TableRow",
    "Tables",
    "create_md_fixture",
    # Normalizer
    "NormalizeOptions",
    "normalize",
    # Parser
    "Block",
    "Table",
    "ParseResult",
    "parse_markdown",
    # Runner
    "RunResult",
    "run_bash",
    "run_python",
]
