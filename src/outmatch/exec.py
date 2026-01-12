"""Command execution mode for outmatch.

Runs a command and asserts on stdout, stderr, and exit code.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from .compare import (
    compare_contains,
    compare_exact,
    compare_json,
    compare_not_contains,
    compare_not_regex,
    compare_regex,
)
from .config import ColorMode, CompareResult


@dataclass
class ExecResult:
    """Result of command execution."""

    stdout: str
    stderr: str
    exit_code: int


@dataclass
class ExecConfig:
    """Configuration for exec assertions."""

    # Exit code assertion
    expected_exit_code: int | None = None

    # Stdout assertions
    stdout_exact: str | None = None
    stdout_contains: str | None = None
    stdout_not_contains: str | None = None
    stdout_regex: str | None = None
    stdout_not_regex: str | None = None

    # Stderr assertions
    stderr_exact: str | None = None
    stderr_contains: str | None = None
    stderr_not_contains: str | None = None
    stderr_regex: str | None = None
    stderr_not_regex: str | None = None

    # Combined JSON assertion
    output_json: str | None = None

    # Options
    quiet: bool = False
    color: ColorMode = ColorMode.AUTO
    timeout: float | None = None


def run_command(args: list[str], timeout: float | None = None) -> ExecResult:
    """Execute command and capture output.

    Args:
        args: Command and arguments as list.
        timeout: Optional timeout in seconds.

    Returns:
        ExecResult with stdout, stderr, and exit code.

    Raises:
        subprocess.TimeoutExpired: If command times out.
        FileNotFoundError: If command not found.
    """
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired as e:
        # Return partial output on timeout
        # With text=True, stdout/stderr are already strings (or None)
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=-1,  # Special code for timeout
        )


def check_assertions(result: ExecResult, config: ExecConfig) -> list[CompareResult]:
    """Check all assertions against execution result.

    Returns list of failed assertions (empty if all pass).
    """
    failures = []

    # Exit code check
    if config.expected_exit_code is not None:
        if result.exit_code != config.expected_exit_code:
            failures.append(
                CompareResult(
                    success=False,
                    message=(
                        f"Exit code mismatch: expected {config.expected_exit_code}, "
                        f"got {result.exit_code}"
                    ),
                )
            )

    # Stdout assertions
    if config.stdout_exact is not None:
        r = compare_exact(result.stdout, config.stdout_exact)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stdout: {r.message}")
            )

    if config.stdout_contains is not None:
        r = compare_contains(result.stdout, config.stdout_contains)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stdout: {r.message}")
            )

    if config.stdout_not_contains is not None:
        r = compare_not_contains(result.stdout, config.stdout_not_contains)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stdout: {r.message}")
            )

    if config.stdout_regex is not None:
        r = compare_regex(result.stdout, config.stdout_regex)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stdout: {r.message}")
            )

    if config.stdout_not_regex is not None:
        r = compare_not_regex(result.stdout, config.stdout_not_regex)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stdout: {r.message}")
            )

    # Stderr assertions
    if config.stderr_exact is not None:
        r = compare_exact(result.stderr, config.stderr_exact)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stderr: {r.message}")
            )

    if config.stderr_contains is not None:
        r = compare_contains(result.stderr, config.stderr_contains)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stderr: {r.message}")
            )

    if config.stderr_not_contains is not None:
        r = compare_not_contains(result.stderr, config.stderr_not_contains)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stderr: {r.message}")
            )

    if config.stderr_regex is not None:
        r = compare_regex(result.stderr, config.stderr_regex)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stderr: {r.message}")
            )

    if config.stderr_not_regex is not None:
        r = compare_not_regex(result.stderr, config.stderr_not_regex)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Stderr: {r.message}")
            )

    # Combined JSON assertion
    if config.output_json is not None:
        actual_json = json.dumps(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }
        )
        r = compare_json(actual_json, config.output_json)
        if not r.success:
            failures.append(
                CompareResult(success=False, message=f"Output JSON: {r.message}")
            )

    return failures
