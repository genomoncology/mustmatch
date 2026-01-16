"""
Pytest plugin for mustmatch markdown testing.

Uses services layer directly - no subprocess spawning for comparisons.
Bash blocks run via subprocess, Python blocks via exec().
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from .services.parser import (
    Block,
    ParseResult,
    Table,
    get_table_for_block,
    parse_markdown,
)
from .services.runner import create_python_namespace, run_bash, run_python

if TYPE_CHECKING:
    from typing import Iterator


class BlockAssertionError(AssertionError):
    """Error raised when a code block fails."""

    def __init__(
        self,
        message: str,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
    ) -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


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
    group.addoption(
        "--mustmatch-timeout",
        action="store",
        type=int,
        default=30,
        help="Timeout per block in seconds (default: 30)",
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

    def collect(self) -> Iterator[pytest.Item]:
        """Yield test items for each code block in the file."""
        lang = self.config.getoption("--mustmatch-lang", default="all")
        memory = self.config.getoption("--mustmatch-memory", default=False)
        timeout = self.config.getoption("--mustmatch-timeout", default=30)

        # Parse markdown using services layer
        content = self.path.read_text()
        result = parse_markdown(content)

        # Filter blocks by language
        blocks = []
        for block in result.blocks:
            # Check skip directive
            if "skip" in block.directives:
                continue

            if lang == "all" or block.language == lang:
                blocks.append(block)

        if not blocks:
            return

        shared_namespace: dict[str, Any] | None = None
        if memory:
            shared_namespace = create_python_namespace(parse_result=result)

        # Yield test items in the order they appear in the file.
        for block in blocks:
            name = self._make_name(block)
            table = get_table_for_block(result, block)

            if block.language == "bash":
                yield BashItem.from_parent(
                    self,
                    name=name,
                    block=block,
                    timeout=timeout,
                )
            elif block.language == "python":
                yield PythonItem.from_parent(
                    self,
                    name=name,
                    block=block,
                    table=table,
                    parse_result=result,
                    timeout=timeout,
                    shared_namespace=shared_namespace,
                )

    def _make_name(self, block: Block) -> str:
        """Generate a test name from a block."""
        heading = block.name or "unnamed"
        return f"{heading} (line {block.line_start}) [{block.language}]"


class BashItem(pytest.Item):
    """Test item for a bash code block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        block: Block,
        timeout: int = 30,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.timeout = timeout

    def runtest(self) -> None:
        """Execute the bash block."""
        # Get timeout from directives if specified
        timeout = self.timeout
        if "timeout" in self.block.directives:
            try:
                timeout = int(self.block.directives["timeout"])
            except ValueError:
                pass

        result = run_bash(
            self.block.content,
            cwd=self.path.parent,
            timeout=float(timeout),
        )

        if isinstance(result.exception, subprocess.TimeoutExpired):
            raise BlockAssertionError(
                f"Command timed out after {timeout}s",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        if result.exception is not None:
            raise BlockAssertionError(
                result.stderr or str(result.exception),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        if result.exit_code != 0:
            msg = f"Exit code {result.exit_code}"
            if result.stderr:
                msg = f"{msg}\n{result.stderr}"
            raise BlockAssertionError(
                msg,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        """Format failure message."""
        if isinstance(excinfo.value, BlockAssertionError):
            err = excinfo.value
            parts = [str(err)]
            if err.stdout:
                parts.append(f"stdout:\n{err.stdout}")
            if err.stderr:
                parts.append(f"stderr:\n{err.stderr}")
            return "\n".join(parts)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.block.line_start - 1, self.name


class PythonItem(pytest.Item):
    """Test item for a Python code block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        block: Block,
        table: Table | None = None,
        parse_result: ParseResult | None = None,
        timeout: int = 30,
        shared_namespace: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.table = table
        self.parse_result = parse_result
        self.timeout = timeout
        self.shared_namespace = shared_namespace

    def runtest(self) -> None:
        """Execute the Python block."""
        # Prepare table data if present
        table_data: list[dict[str, str]] | None = None
        if self.table:
            table_data = [
                dict(zip(self.table.headers, row))
                for row in self.table.rows
            ]

        timeout = self.timeout
        if "timeout" in self.block.directives:
            try:
                timeout = int(self.block.directives["timeout"])
            except ValueError:
                pass

        if self.shared_namespace is not None:
            namespace = self.shared_namespace
            if table_data is None:
                namespace.pop("table", None)
            else:
                namespace["table"] = table_data

            if self.parse_result is not None:
                from .services.fixture import create_md_fixture

                namespace["md"] = create_md_fixture(self.parse_result, self.block)

            result = run_python(
                self.block.content,
                globals_dict=namespace,
                timeout=float(timeout),
            )
        else:
            namespace = create_python_namespace(
                table=table_data,
                parse_result=self.parse_result,
                current_block=self.block,
            )
            result = run_python(
                self.block.content,
                globals_dict=namespace,
                timeout=float(timeout),
            )

        if result.exit_code != 0:
            raise BlockAssertionError(
                result.stderr or str(result.exception),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        """Format failure message."""
        if isinstance(excinfo.value, BlockAssertionError):
            return str(excinfo.value)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.block.line_start - 1, self.name
