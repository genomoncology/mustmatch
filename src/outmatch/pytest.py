"""
outmatch pytest plugin for testing markdown documentation.

Provides native pytest integration for testing bash blocks in markdown files.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from typing import Any


class MarkdownTest:
    """Represents a single bash block from markdown.

    Attributes:
        file: Path to the markdown file
        line: Starting line number of the bash block content
        content: The bash block content
        name: Block name (from preceding heading or comment)
    """

    def __init__(
        self,
        file: Path,
        line: int,
        content: str,
        name: str,
    ) -> None:
        self.file = file
        self.line = line
        self.content = content
        self.name = name

    @property
    def id(self) -> str:
        """Unique test ID for pytest."""
        return f"{self.file}:{self.line}"

    def __repr__(self) -> str:
        return f"MarkdownTest({self.file}:{self.line} - {self.name})"

    @classmethod
    def discover(
        cls,
        path: str | Path,
        *,
        pattern: str = "**/*.md",
        exclude: list[str] | None = None,
    ) -> Iterator[MarkdownTest]:
        """Discover all bash blocks in markdown files.

        Args:
            path: Directory to search for markdown files
            pattern: Glob pattern for markdown files (default: "**/*.md")
            exclude: List of path substrings to exclude

        Yields:
            MarkdownTest instances for each bash block found
        """
        path = Path(path)
        if not path.exists():
            return

        # Find all markdown files
        files = sorted(path.glob(pattern))

        # Parse each file
        for file in files:
            if exclude and any(e in str(file) for e in exclude):
                continue

            yield from cls._parse_file(file)

    @classmethod
    def _parse_file(cls, file: Path) -> Iterator[MarkdownTest]:
        """Parse markdown file and yield bash blocks.

        Args:
            file: Path to the markdown file

        Yields:
            MarkdownTest instances for each bash block
        """
        content = file.read_text()
        lines = content.split("\n")

        in_bash_block = False
        block_start = 0
        block_content: list[str] = []
        block_name = "Unnamed block"

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect bash block start
            if stripped in ("```bash", "```sh", "```shell"):
                in_bash_block = True
                block_start = i + 1
                block_content = []
                # Look for preceding heading
                block_name = cls._find_block_name(lines, i - 1)

            # Detect bash block end
            elif stripped == "```" and in_bash_block:
                in_bash_block = False
                # Only yield non-empty blocks
                block_text = "\n".join(block_content)
                if block_text.strip():
                    yield cls(
                        file=file,
                        line=block_start,
                        content=block_text,
                        name=block_name,
                    )

            # Accumulate block content
            elif in_bash_block:
                block_content.append(line)

    @classmethod
    def _find_block_name(cls, lines: list[str], end_index: int) -> str:
        """Find the name for a bash block from preceding context.

        Looks backwards from end_index to find either:
        1. A markdown heading (# Heading)
        2. A comment (<!-- name -->)
        3. Falls back to "Unnamed block"

        Args:
            lines: All lines in the file (0-indexed)
            end_index: Index to start searching backwards from (0-indexed)

        Returns:
            The block name
        """
        # Search backwards for a heading or comment (up to 10 lines back)
        start = max(end_index - 10, 0)
        for i in range(end_index - 1, start - 1, -1):
            line = lines[i].strip()

            # Check for markdown heading
            if line.startswith("#"):
                return line.lstrip("#").strip()

            # Check for HTML comment with name
            if line.startswith("<!--") and line.endswith("-->"):
                return line[4:-3].strip()

        return "Unnamed block"

    def run(
        self,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Execute the bash block.

        Args:
            env: Additional environment variables to set
            cwd: Working directory for execution
            timeout: Maximum execution time in seconds

        Raises:
            AssertionError: If the block fails (non-zero exit code)
            TimeoutError: If execution exceeds timeout
        """
        # Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            # Execute with bash -e (exit on error) -u (error on undefined vars)
            proc = subprocess.run(
                ["bash", "-e", "-u", "-c", self.content],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=exec_env,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired as e:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {self.content}\n\n"
            error_msg += f"Error: Execution timed out after {timeout}s"
            raise TimeoutError(error_msg) from e

        # Check result
        if proc.returncode != 0:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {self._indent(self.content)}\n\n"
            if proc.stdout:
                error_msg += f"Stdout:\n  {self._indent(proc.stdout)}\n\n"
            if proc.stderr:
                error_msg += f"Stderr:\n  {self._indent(proc.stderr)}\n"
            error_msg += f"\nExit code: {proc.returncode}"
            raise AssertionError(error_msg)

    def run_with_fixture(self, fixture_value: Any) -> None:
        """Execute block with access to pytest fixture.

        This is a convenience method for passing fixture values
        to bash blocks via environment variables.

        Args:
            fixture_value: Value to make available in the block
        """
        if isinstance(fixture_value, dict):
            # Pass dict entries as environment variables
            env = {k: str(v) for k, v in fixture_value.items()}
            self.run(env=env)
        else:
            # Pass as FIXTURE_VALUE
            self.run(env={"FIXTURE_VALUE": str(fixture_value)})

    @staticmethod
    def _indent(text: str, prefix: str = "  ") -> str:
        """Indent all lines in text."""
        return "\n".join(prefix + line for line in text.split("\n"))
