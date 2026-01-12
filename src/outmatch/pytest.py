"""
outmatch pytest plugin for testing markdown documentation.

Provides native pytest integration for testing bash blocks in markdown files.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterator

from .parsing import parse_markdown_file


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
        """Parse markdown file and yield bash blocks.

        Uses shared parsing module to avoid code duplication with mdtest.py.
        """
        for block in parse_markdown_file(file, include_name=True):
            if block.content.strip():
                yield cls(
                    file=file,
                    line=block.line_start,
                    content=block.content,
                    name=block.name or "Unnamed block",
                )

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
            error_msg += f"Timeout: Execution exceeded {timeout}s limit"
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
