"""
mustmatch pytest plugin for testing markdown documentation.

Provides native pytest integration for testing bash and Python blocks in markdown files.
"""

from __future__ import annotations

import io
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

from .parsing import parse_markdown_file

# Pattern to detect simple piping to mustmatch (no bash operators after)
# Only matches: <prefix> | mustmatch <args>
# Does NOT match if there's || or && or ; after mustmatch (those need bash)
MUSTMATCH_PIPE_PATTERN = re.compile(
    r'^(.*?)\s*\|\s*mustmatch\s+(.+)$',
    re.DOTALL
)


class MarkdownTest:
    """Represents a single code block from markdown."""

    def __init__(
        self,
        file: Path,
        line: int,
        content: str,
        name: str,
        lang: str = "bash",
    ) -> None:
        self.file = file
        self.line = line
        self.content = content
        self.name = name
        self.lang = lang

    def __repr__(self) -> str:
        return f"MarkdownTest({self.file}:{self.line} - {self.name} [{self.lang}])"

    @classmethod
    def _parse_file(
        cls,
        file: Path,
        lang: str = "bash",
    ) -> Iterator[MarkdownTest]:
        """Parse markdown file and yield code blocks.

        Args:
            file: Path to markdown file.
            lang: Language to parse: "bash", "python", or "all".

        Uses shared parsing module to avoid code duplication with mdtest.py.
        """
        for block in parse_markdown_file(file, include_name=True, lang=lang):
            if block.content.strip():
                yield cls(
                    file=file,
                    line=block.line_start,
                    content=block.content,
                    name=block.name or "Unnamed block",
                    lang=block.lang,
                )

    def run(
        self,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        timeout: float = 30.0,
        namespace: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute the code block.

        Args:
            env: Environment variables for bash blocks.
            cwd: Working directory.
            timeout: Timeout in seconds.
            namespace: Shared namespace for Python memory mode.

        Returns:
            Updated namespace for Python blocks (for memory mode), None for bash.

        Raises:
            AssertionError: If block execution fails.
            TimeoutError: If block times out.
        """
        if self.lang == "python":
            return self._run_python(namespace)
        else:
            self._run_bash(env=env, cwd=cwd, timeout=timeout)
            return None

    def _run_bash(
        self,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Execute a bash block.

        If the command pipes to mustmatch, we intercept and call mustmatch
        directly via Python to enable code coverage.
        """
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Check if this is a simple pipe to mustmatch
        result = self._try_run_mustmatch_direct(
            env=exec_env, cwd=cwd, timeout=timeout
        )
        if result is not None:
            return  # Successfully ran via direct Python call

        # Fall back to subprocess for complex commands
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

    def _try_run_mustmatch_direct(
        self,
        *,
        env: dict[str, str],
        cwd: Path | None,
        timeout: float,
    ) -> bool | None:
        """Try to run mustmatch commands directly via Python.

        Returns:
            True if successfully ran directly, None if not applicable.

        Raises:
            AssertionError: If mustmatch assertion fails.
        """
        # Look for pattern: <command> | mustmatch <args>
        match = MUSTMATCH_PIPE_PATTERN.match(self.content.strip())
        if not match:
            return None

        prefix_cmd = match.group(1).strip()
        mustmatch_args_str = match.group(2).strip()

        # Don't handle complex cases:
        # - Multiple pipes in prefix
        # - Bash operators after mustmatch (||, &&, ;)
        # - Redirections
        if '|' in prefix_cmd:
            return None
        if any(op in mustmatch_args_str for op in ('||', '&&', ';', '>')):
            return None

        # Run the prefix command to get input
        try:
            proc = subprocess.run(
                ["bash", "-e", "-u", "-c", prefix_cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired as e:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {prefix_cmd}\n\n"
            error_msg += f"Timeout: Execution exceeded {timeout}s limit"
            raise TimeoutError(error_msg) from e

        if proc.returncode != 0:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {self._indent(prefix_cmd)}\n\n"
            if proc.stdout:
                error_msg += f"Stdout:\n  {self._indent(proc.stdout)}\n\n"
            if proc.stderr:
                error_msg += f"Stderr:\n  {self._indent(proc.stderr)}\n"
            error_msg += f"\nExit code: {proc.returncode}"
            raise AssertionError(error_msg)

        # Parse mustmatch args
        try:
            args = shlex.split(mustmatch_args_str)
        except ValueError:
            # Can't parse args, fall back to subprocess
            return None

        # Call mustmatch directly
        from .cli import main

        # Capture stdin/stdout/stderr
        old_stdin = sys.stdin
        old_stderr = sys.stderr
        captured_stderr = io.StringIO()

        try:
            sys.stdin = io.StringIO(proc.stdout)
            sys.stderr = captured_stderr

            exit_code = main(args)
        finally:
            sys.stdin = old_stdin
            sys.stderr = old_stderr

        if exit_code != 0:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n  {self._indent(self.content)}\n\n"
            stderr_output = captured_stderr.getvalue()
            if stderr_output:
                error_msg += f"Stderr:\n  {self._indent(stderr_output)}\n"
            error_msg += f"\nExit code: {exit_code}"
            raise AssertionError(error_msg)

        return True

    def _run_python(
        self,
        namespace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a Python block.

        Args:
            namespace: Shared namespace for memory mode.

        Returns:
            Updated namespace.

        Raises:
            AssertionError: If execution fails.
        """
        from .python_exec import execute_python

        filename = f"{self.file}:{self.line}"
        result, namespace = execute_python(self.content, namespace, filename)

        if not result.success:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Code:\n  {self._indent(self.content)}\n\n"
            if result.output:
                error_msg += f"Output:\n  {self._indent(result.output)}\n\n"
            error_msg += f"Error:\n  {result.error}"
            raise AssertionError(error_msg)

        return namespace

    @staticmethod
    def _indent(text: str, prefix: str = "  ") -> str:
        """Indent all lines in text."""
        return "\n".join(prefix + line for line in text.split("\n"))
