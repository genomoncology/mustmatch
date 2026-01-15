"""
Pytest plugin for mustmatch markdown testing.

Automatically collects and runs bash and Python blocks from markdown files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from mustmatch.pytest import MarkdownTest

if TYPE_CHECKING:
    from typing import Iterator

__all__ = ["MarkdownTest"]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add mustmatch options to pytest."""
    group = parser.getgroup("mustmatch")
    group.addoption(
        "--mustmatch-lang",
        action="store",
        default="all",
        choices=["bash", "python", "all"],
        help="Language to test: bash, python, all (default: all)",
    )
    group.addoption(
        "--mustmatch-memory",
        action="store_true",
        default=False,
        help="Share state between Python blocks within a file",
    )


def pytest_collect_file(
    parent: pytest.Collector,
    file_path: Path,
) -> MarkdownFile | None:
    """Collect markdown files as test files."""
    if file_path.suffix == ".md":
        return MarkdownFile.from_parent(parent, path=file_path)
    return None


class MarkdownFile(pytest.File):
    """Collector for markdown files containing code blocks."""

    def collect(self) -> Iterator[MarkdownItem]:
        """Yield test items for each code block in the file."""
        lang = self.config.getoption("--mustmatch-lang", default="all")
        memory = self.config.getoption("--mustmatch-memory", default=False)

        tests = list(MarkdownTest._parse_file(self.path, lang=lang))

        if memory and any(t.lang == "python" for t in tests):
            # In memory mode, run all Python blocks together as one item
            python_tests = [t for t in tests if t.lang == "python"]
            bash_tests = [t for t in tests if t.lang == "bash"]

            # Yield bash blocks individually
            for test in bash_tests:
                yield MarkdownItem.from_parent(
                    self,
                    name=f"{test.name} (line {test.line}) [bash]",
                    test=test,
                )

            # Yield Python blocks as a single memory-mode item
            if python_tests:
                yield PythonMemoryItem.from_parent(
                    self,
                    name=f"Python blocks ({len(python_tests)} blocks) [memory]",
                    tests=python_tests,
                )
        else:
            # Run each block independently
            for test in tests:
                lang_tag = f"[{test.lang}]"
                yield MarkdownItem.from_parent(
                    self,
                    name=f"{test.name} (line {test.line}) {lang_tag}",
                    test=test,
                )


class MarkdownItem(pytest.Item):
    """Test item for a single code block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        test: MarkdownTest,
    ) -> None:
        super().__init__(name, parent)
        self.test = test

    def runtest(self) -> None:
        """Execute the code block."""
        self.test.run(cwd=Path.cwd())

    def repr_failure(self, excinfo: pytest.ExceptionInfo) -> str:
        """Format failure message."""
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.test.line - 1, self.name


class PythonMemoryItem(pytest.Item):
    """Test item for Python blocks with shared state (memory mode)."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        tests: list[MarkdownTest],
    ) -> None:
        super().__init__(name, parent)
        self.tests = tests

    def runtest(self) -> None:
        """Execute all Python blocks with shared namespace."""
        namespace: dict[str, Any] = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
        }
        for test in self.tests:
            namespace = test.run(namespace=namespace) or namespace

    def repr_failure(self, excinfo: pytest.ExceptionInfo) -> str:
        """Format failure message."""
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int | None, str]:
        """Report test location."""
        first_line = self.tests[0].line - 1 if self.tests else None
        return self.path, first_line, self.name
