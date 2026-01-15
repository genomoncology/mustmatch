"""Command execution mode for mustmatch."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .compare import (
    compare_contains_string,
    compare_exact_string,
    compare_not_contains,
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
    expected_exit_code: int | None = None
    stdout_exact: str | None = None
    stdout_contains: str | None = None
    stdout_not_contains: str | None = None
    stdout_regex: str | None = None
    stderr_exact: str | None = None
    stderr_contains: str | None = None
    stderr_not_contains: str | None = None
    stderr_regex: str | None = None
    quiet: bool = False
    color: ColorMode = ColorMode.AUTO
    timeout: float | None = None


def run_command(args: list[str], timeout: float | None = None) -> ExecResult:
    """Execute command and capture output."""
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
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=-1,
        )


def _fail(msg: str) -> CompareResult:
    """Create a failure CompareResult."""
    return CompareResult(success=False, message=msg)


def check_assertions(
    result: ExecResult, config: ExecConfig
) -> list[CompareResult]:
    """Check all assertions against execution result."""
    failures: list[CompareResult] = []

    # Exit code
    if config.expected_exit_code is not None:
        if result.exit_code != config.expected_exit_code:
            msg = (
                f"Exit code mismatch: expected {config.expected_exit_code}, "
                f"got {result.exit_code}"
            )
            failures.append(_fail(msg))

    # Stdout assertions
    if config.stdout_exact is not None:
        r = compare_exact_string(result.stdout, config.stdout_exact)
        if not r.success:
            failures.append(_fail(f"Stdout: {r.message}"))

    if config.stdout_contains is not None:
        r = compare_contains_string(result.stdout, config.stdout_contains)
        if not r.success:
            failures.append(_fail(f"Stdout: {r.message}"))

    if config.stdout_not_contains is not None:
        r = compare_not_contains(result.stdout, config.stdout_not_contains)
        if not r.success:
            failures.append(_fail(f"Stdout: {r.message}"))

    if config.stdout_regex is not None:
        r = compare_regex(result.stdout, config.stdout_regex)
        if not r.success:
            failures.append(_fail(f"Stdout: {r.message}"))

    # Stderr assertions
    if config.stderr_exact is not None:
        r = compare_exact_string(result.stderr, config.stderr_exact)
        if not r.success:
            failures.append(_fail(f"Stderr: {r.message}"))

    if config.stderr_contains is not None:
        r = compare_contains_string(result.stderr, config.stderr_contains)
        if not r.success:
            failures.append(_fail(f"Stderr: {r.message}"))

    if config.stderr_not_contains is not None:
        r = compare_not_contains(result.stderr, config.stderr_not_contains)
        if not r.success:
            failures.append(_fail(f"Stderr: {r.message}"))

    if config.stderr_regex is not None:
        r = compare_regex(result.stderr, config.stderr_regex)
        if not r.success:
            failures.append(_fail(f"Stderr: {r.message}"))

    return failures
