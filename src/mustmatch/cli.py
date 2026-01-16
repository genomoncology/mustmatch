"""
CLI interface - thin layer that delegates to services.

Grammar:
    mustmatch [-i] [not] [like] EXPECTED
    mustmatch test PATHS
    mustmatch exec -- CMD
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from .services.comparator import (
    CompareMode,
    compare,
    detect_mode,
    extract_regex_pattern,
)
from .services.normalizer import NormalizeOptions, normalize
from .version import __version__


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"mustmatch {__version__}")
        raise typer.Exit()


def _run_match(
    expected: str,
    *,
    negate: bool = False,
    like: bool = False,
    ignore_case: bool = False,
    quiet: bool = False,
    expected_file: Path | None = None,
    ignore_paths: list[str] | None = None,
    update: bool = False,
) -> int:
    """Run the match logic using services layer. Returns exit code."""
    # Read actual from stdin
    actual = sys.stdin.read()

    # Normalize both (ANSI stripping and newline normalization are always on)
    norm_opts = NormalizeOptions(
        strip_ansi=True,
        normalize_newlines=True,
        trim=True,
        ignore_case=ignore_case,
    )
    actual = normalize(actual, norm_opts)
    expected = normalize(expected, norm_opts)

    # Detect mode from syntax
    mode = detect_mode(expected)

    # Handle regex pattern extraction
    if mode == CompareMode.REGEX:
        expected = extract_regex_pattern(expected)

    # Override mode if 'like' is specified
    if like:
        if mode == CompareMode.JSON:
            # JSON subset match
            subset = True
        else:
            mode = CompareMode.CONTAINS
            subset = False
    else:
        subset = False

    # Run comparison
    result = compare(
        actual,
        expected,
        mode=mode,
        subset=subset,
        ignore_paths=ignore_paths,
        ignore_case=ignore_case,
    )

    # Handle negation
    matches = result.matches
    if negate:
        matches = not matches

    if matches:
        return 0

    # Handle update mode
    if update and expected_file:
        expected_file.write_text(actual)
        if not quiet:
            print(f"Updated: {expected_file}", file=sys.stderr)
        return 0

    # Output error
    if not quiet:
        if negate:
            print("FAIL: Expected NOT to match, but it did", file=sys.stderr)
        else:
            print(result.message, file=sys.stderr)

    return 1


# ============================================================================
# Main match app
# ============================================================================

match_app = typer.Typer(
    help="Assert CLI output matches expected value.",
    add_completion=False,
    no_args_is_help=False,
)


@match_app.callback(invoke_without_command=True)
def match_callback(
    ctx: typer.Context,
    args: Annotated[
        Optional[list[str]],
        typer.Argument(help="[not] [like] EXPECTED"),
    ] = None,
    ignore_case: Annotated[
        bool,
        typer.Option("-i", "--ignore-case", help="Case-insensitive comparison"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Suppress error output"),
    ] = False,
    expected_file: Annotated[
        Optional[Path],
        typer.Option("-f", "--file", help="Read expected from file"),
    ] = None,
    ignore: Annotated[
        Optional[list[str]],
        typer.Option("--ignore", help="Ignore JSON path (e.g., $.timestamp)"),
    ] = None,
    update: Annotated[
        bool,
        typer.Option("--update", help="Update expected file on mismatch"),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version",
        ),
    ] = None,
) -> None:
    """Assert CLI output matches expected value.

    Grammar: mustmatch [-i] [not] [like] EXPECTED

    Examples:
        echo "hello" | mustmatch "hello"
        echo "hello world" | mustmatch like "hello"
        echo "v1.2.3" | mustmatch "/v\\d+\\.\\d+/"
        echo '{"a":1}' | mustmatch '{"a":1}'
        echo "ok" | mustmatch not like "error"
    """
    # Parse positional args: [not] [like] EXPECTED
    args = args or []
    negate = False
    like = False
    expected: str | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "not" and not negate and expected is None:
            negate = True
        elif arg == "like" and not like and expected is None:
            like = True
        else:
            expected = arg
            break
        i += 1

    # Get expected from file if specified
    if expected_file:
        if not expected_file.exists():
            if update:
                expected = ""
            else:
                print(f"Error: file not found: {expected_file}", file=sys.stderr)
                raise typer.Exit(2)
        else:
            expected = expected_file.read_text()

    if expected is None:
        print(
            "Error: expected value required (argument or -f FILE)",
            file=sys.stderr,
        )
        raise typer.Exit(2)

    exit_code = _run_match(
        expected,
        negate=negate,
        like=like,
        ignore_case=ignore_case,
        quiet=quiet,
        expected_file=expected_file,
        ignore_paths=ignore,
        update=update,
    )
    raise typer.Exit(exit_code)


# ============================================================================
# Test app
# ============================================================================

test_app = typer.Typer(
    help="Run code blocks in markdown files as tests.",
    add_completion=False,
)


@test_app.callback(invoke_without_command=True)
def test_callback(
    paths: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Files or directories to test"),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Minimal output"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Verbose output"),
    ] = False,
    fail_fast: Annotated[
        bool,
        typer.Option("--fail-fast", "-x", help="Stop on first failure"),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(help="Timeout per block in seconds"),
    ] = 30,
    lang: Annotated[
        str,
        typer.Option("--lang", help="Language to test: bash, python, all"),
    ] = "all",
    memory: Annotated[
        bool,
        typer.Option("--memory", help="Share state between Python blocks"),
    ] = False,
) -> None:
    """Run code blocks in markdown files as tests."""
    import subprocess

    cmd = ["python", "-m", "pytest"]

    if quiet:
        cmd.append("-q")
    if verbose:
        cmd.append("-v")
    if fail_fast:
        cmd.append("-x")

    cmd.extend([f"--mustmatch-lang={lang}"])
    cmd.extend([f"--mustmatch-timeout={timeout}"])
    if memory:
        cmd.append("--mustmatch-memory")

    if paths:
        cmd.extend(str(p) for p in paths)
    else:
        cmd.append(".")

    result = subprocess.run(cmd)
    raise typer.Exit(result.returncode)


# ============================================================================
# Exec app
# ============================================================================

exec_app = typer.Typer(
    help="Execute command and assert on output.",
    add_completion=False,
)


@exec_app.callback(invoke_without_command=True)
def exec_callback(
    command: Annotated[
        list[str],
        typer.Argument(help="Command to execute (after --)"),
    ],
    exit_code: Annotated[
        Optional[int],
        typer.Option("--exit-code", help="Expected exit code"),
    ] = None,
    stdout: Annotated[
        Optional[str],
        typer.Option("--stdout", help="Expected stdout (exact)"),
    ] = None,
    stdout_like: Annotated[
        Optional[str],
        typer.Option("--stdout-like", help="Stdout must contain"),
    ] = None,
    stdout_not_like: Annotated[
        Optional[str],
        typer.Option("--stdout-not-like", help="Stdout must NOT contain"),
    ] = None,
    stderr: Annotated[
        Optional[str],
        typer.Option("--stderr", help="Expected stderr (exact)"),
    ] = None,
    stderr_like: Annotated[
        Optional[str],
        typer.Option("--stderr-like", help="Stderr must contain"),
    ] = None,
    stderr_not_like: Annotated[
        Optional[str],
        typer.Option("--stderr-not-like", help="Stderr must NOT contain"),
    ] = None,
    timeout: Annotated[
        Optional[float],
        typer.Option(help="Command timeout in seconds"),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Suppress output"),
    ] = False,
) -> None:
    """Execute command and assert on output."""
    from .services.runner import run_bash

    # Skip leading -- if present
    cmd = list(command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if not cmd:
        print("Error: no command specified", file=sys.stderr)
        raise typer.Exit(2)

    # Check if any assertion was specified
    has_assertion = any([
        exit_code is not None,
        stdout is not None,
        stdout_like is not None,
        stdout_not_like is not None,
        stderr is not None,
        stderr_like is not None,
        stderr_not_like is not None,
    ])

    if not has_assertion:
        print(
            "Error: at least one assertion required (--exit-code, --stdout, etc.)",
            file=sys.stderr,
        )
        raise typer.Exit(2)

    # Run command
    code = " ".join(cmd)
    result = run_bash(code, timeout=timeout)

    # Check timeout
    if result.exception is not None and timeout is not None:
        if not quiet:
            print(f"FAIL: Command timed out after {timeout}s", file=sys.stderr)
        raise typer.Exit(1)

    # Normalize output
    norm_opts = NormalizeOptions(strip_ansi=True, normalize_newlines=True, trim=True)
    actual_stdout = normalize(result.stdout, norm_opts)
    actual_stderr = normalize(result.stderr, norm_opts)

    failures: list[str] = []

    # Check exit code
    if exit_code is not None and result.exit_code != exit_code:
        failures.append(
            f"Exit code: expected {exit_code}, got {result.exit_code}"
        )

    # Check stdout
    if stdout is not None:
        expected = normalize(stdout, norm_opts)
        if actual_stdout != expected:
            failures.append(f"Stdout mismatch:\n  Expected: {expected!r}\n  Got: {actual_stdout!r}")

    if stdout_like is not None and stdout_like not in actual_stdout:
        failures.append(f"Stdout does not contain: {stdout_like!r}")

    if stdout_not_like is not None and stdout_not_like in actual_stdout:
        failures.append(f"Stdout should NOT contain: {stdout_not_like!r}")

    # Check stderr
    if stderr is not None:
        expected = normalize(stderr, norm_opts)
        if actual_stderr != expected:
            failures.append(f"Stderr mismatch:\n  Expected: {expected!r}\n  Got: {actual_stderr!r}")

    if stderr_like is not None and stderr_like not in actual_stderr:
        failures.append(f"Stderr does not contain: {stderr_like!r}")

    if stderr_not_like is not None and stderr_not_like in actual_stderr:
        failures.append(f"Stderr should NOT contain: {stderr_not_like!r}")

    if not failures:
        raise typer.Exit(0)

    if not quiet:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)

    raise typer.Exit(1)


# ============================================================================
# Entry points
# ============================================================================


def main(args: list[str] | None = None) -> int:
    """Main entry point with manual subcommand routing."""
    if args is None:
        args = sys.argv[1:]

    try:
        # Route to appropriate app based on first argument
        if args and args[0] == "test":
            result = test_app(args[1:], standalone_mode=False)
        elif args and args[0] == "exec":
            result = exec_app(args[1:], standalone_mode=False)
        else:
            result = match_app(args, standalone_mode=False)

        if isinstance(result, int):
            return result
        return 0
    except typer.Exit as e:
        return e.exit_code
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0


def cli() -> None:
    """CLI entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
