"""Command execution mode for outmatch.

Runs a command and asserts on stdout, stderr, and exit code.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Annotated, Optional

import typer

from .compare import (
    compare_contains,
    compare_exact,
    compare_json,
    compare_not_contains,
    compare_not_regex,
    compare_regex,
)
from .config import ColorMode, CompareResult, ExpectConfig
from .output import format_error


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
        return ExecResult(
            stdout=e.stdout.decode() if e.stdout else "",
            stderr=e.stderr.decode() if e.stderr else "",
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


def exec_command(
    args: list[str],
    expected_exit_code: Annotated[
        Optional[int],
        typer.Option("--exit-code", help="Expected exit code"),
    ] = None,
    stdout: Annotated[
        Optional[str],
        typer.Option("--stdout", help="Expected stdout (exact match)"),
    ] = None,
    stdout_contains: Annotated[
        Optional[str],
        typer.Option("--stdout-contains", help="Stdout must contain"),
    ] = None,
    stdout_not_contains: Annotated[
        Optional[str],
        typer.Option("--stdout-not-contains", help="Stdout must NOT contain"),
    ] = None,
    stdout_regex: Annotated[
        Optional[str],
        typer.Option("--stdout-regex", help="Stdout must match regex"),
    ] = None,
    stdout_not_regex: Annotated[
        Optional[str],
        typer.Option("--stdout-not-regex", help="Stdout must NOT match regex"),
    ] = None,
    stderr: Annotated[
        Optional[str],
        typer.Option("--stderr", help="Expected stderr (exact match)"),
    ] = None,
    stderr_contains: Annotated[
        Optional[str],
        typer.Option("--stderr-contains", help="Stderr must contain"),
    ] = None,
    stderr_not_contains: Annotated[
        Optional[str],
        typer.Option("--stderr-not-contains", help="Stderr must NOT contain"),
    ] = None,
    stderr_regex: Annotated[
        Optional[str],
        typer.Option("--stderr-regex", help="Stderr must match regex"),
    ] = None,
    stderr_not_regex: Annotated[
        Optional[str],
        typer.Option("--stderr-not-regex", help="Stderr must NOT match regex"),
    ] = None,
    output_json: Annotated[
        Optional[str],
        typer.Option(
            "--output-json",
            help='Match combined JSON: {"stdout":..., "exit_code": N}',
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Suppress error output"),
    ] = False,
    color: Annotated[
        str,
        typer.Option(help="Color mode: auto, always, never"),
    ] = "auto",
    timeout: Annotated[
        Optional[float],
        typer.Option(help="Command timeout in seconds"),
    ] = None,
) -> None:
    """Execute a command and assert on its output.

    Example:
        outmatch exec --exit-code 0 -- ls /tmp
        outmatch exec --stdout-contains "hello" -- echo hello world
        outmatch exec --stderr "" -- cmd  # Assert stderr is empty
    """
    if not args:
        print("Error: no command specified", file=sys.stderr)
        raise typer.Exit(2)

    # Build config
    config = ExecConfig(
        expected_exit_code=expected_exit_code,
        stdout_exact=stdout,
        stdout_contains=stdout_contains,
        stdout_not_contains=stdout_not_contains,
        stdout_regex=stdout_regex,
        stdout_not_regex=stdout_not_regex,
        stderr_exact=stderr,
        stderr_contains=stderr_contains,
        stderr_not_contains=stderr_not_contains,
        stderr_regex=stderr_regex,
        stderr_not_regex=stderr_not_regex,
        output_json=output_json,
        quiet=quiet,
        color=ColorMode(color),
        timeout=timeout,
    )

    # Check if any assertion was specified
    has_assertion = any(
        [
            expected_exit_code is not None,
            stdout is not None,
            stdout_contains is not None,
            stdout_not_contains is not None,
            stdout_regex is not None,
            stdout_not_regex is not None,
            stderr is not None,
            stderr_contains is not None,
            stderr_not_contains is not None,
            stderr_regex is not None,
            stderr_not_regex is not None,
            output_json is not None,
        ]
    )

    if not has_assertion:
        print(
            "Error: at least one assertion required (--exit-code, --stdout, etc.)",
            file=sys.stderr,
        )
        raise typer.Exit(2)

    # Run the command
    try:
        result = run_command(args, timeout=config.timeout)
    except FileNotFoundError:
        print(f"Error: command not found: {args[0]}", file=sys.stderr)
        raise typer.Exit(2)

    # Check timeout
    if result.exit_code == -1 and config.timeout is not None:
        if not quiet:
            print(
                f"FAIL: Command timed out after {config.timeout}s",
                file=sys.stderr,
            )
        raise typer.Exit(1)

    # Check assertions
    failures = check_assertions(result, config)

    if not failures:
        raise typer.Exit(0)

    # Output failures
    if not quiet:
        for failure in failures:
            expect_config = ExpectConfig(quiet=quiet, color=config.color)
            print(format_error(failure, expect_config), file=sys.stderr)

    raise typer.Exit(1)
