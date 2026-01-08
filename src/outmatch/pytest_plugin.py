"""
Pytest plugin for outmatch markdown testing.

Automatically collects and runs bash blocks from markdown files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from outmatch.pytest import MarkdownTest

if TYPE_CHECKING:
    from typing import Iterator

__all__ = ["MarkdownTest"]


def pytest_collect_file(
    parent: pytest.Collector,
    file_path: Path,
) -> MarkdownFile | None:
    """Collect markdown files as test files."""
    if file_path.suffix == ".md":
        return MarkdownFile.from_parent(parent, path=file_path)
    return None


class MarkdownFile(pytest.File):
    """Collector for markdown files containing bash blocks."""

    def collect(self) -> Iterator[MarkdownItem]:
        """Yield test items for each bash block in the file."""
        for test in MarkdownTest._parse_file(self.path):
            yield MarkdownItem.from_parent(
                self,
                name=f"{test.name} (line {test.line})",
                test=test,
            )


class MarkdownItem(pytest.Item):
    """Test item for a single bash block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        test: MarkdownTest,
    ) -> None:
        super().__init__(name, parent)
        self.test = test

    def runtest(self) -> None:
        """Execute the bash block."""
        self.test.run(cwd=Path.cwd())

    def repr_failure(self, excinfo: pytest.ExceptionInfo) -> str:
        """Format failure message."""
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.test.line - 1, self.name
