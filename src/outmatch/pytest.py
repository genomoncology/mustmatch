"""
outmatch pytest plugin for testing markdown documentation.

Provides native pytest integration for testing bash blocks in markdown files.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterator


class MarkdownTest:
    """Represents a single bash block from markdown."""

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

    def __repr__(self) -> str:
        return f"MarkdownTest({self.file}:{self.line} - {self.name})"

    @classmethod
    def _parse_file(cls, file: Path) -> Iterator[MarkdownTest]:
        """Parse markdown file and yield bash blocks."""
        content = file.read_text()
        lines = content.split("\n")

        in_bash_block = False
        block_start = 0
        block_content: list[str] = []
        block_name = "Unnamed block"

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped in ("```bash", "```sh", "```shell"):
                in_bash_block = True
                block_start = i + 1
                block_content = []
                block_name = cls._find_block_name(lines, i - 1)

            elif stripped == "```" and in_bash_block:
                in_bash_block = False
                block_text = "\n".join(block_content)
                if block_text.strip():
                    yield cls(
                        file=file,
                        line=block_start,
                        content=block_text,
                        name=block_name,
                    )

            elif in_bash_block:
                block_content.append(line)

    @classmethod
    def _find_block_name(cls, lines: list[str], end_index: int) -> str:
        """Find the name for a bash block from preceding heading or comment."""
        start = max(end_index - 10, 0)
        for i in range(end_index - 1, start - 1, -1):
            line = lines[i].strip()

            if line.startswith("#"):
                return line.lstrip("#").strip()

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
        """Execute the bash block."""
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
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

        if proc.returncode != 0:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {self._indent(self.content)}\n\n"
            if proc.stdout:
                error_msg += f"Stdout:\n  {self._indent(proc.stdout)}\n\n"
            if proc.stderr:
                error_msg += f"Stderr:\n  {self._indent(proc.stderr)}\n"
            error_msg += f"\nExit code: {proc.returncode}"
            raise AssertionError(error_msg)

    @staticmethod
    def _indent(text: str, prefix: str = "  ") -> str:
        """Indent all lines in text."""
        return "\n".join(prefix + line for line in text.split("\n"))
