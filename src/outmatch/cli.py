"""CLI interface using Typer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from .compare import compare
from .config import (
    ColorMode,
    CompareMode,
    DiffFormat,
    ExpectConfig,
    NormalizeOptions,
    RegexError,
    compile_redactions,
    compile_replacements,
)
from .normalize import preprocess
from .output import format_error
from .version import __version__

app = typer.Typer(
    help="Assert CLI output matches expected value.",
    add_completion=False,
    no_args_is_help=False,
)



def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"outmatch {__version__}")
        raise typer.Exit()


def _run_expect(
    expected: str | None,
    expected_file: Path | None,
    contains: bool,
    regex: bool,
    json_mode: bool,
    jsonl: bool,
    jsonl_set: bool,
    jsonl_key: str | None,
    jsonl_contains: bool,
    not_contains: bool,
    not_regex: bool,
    strip_ansi: bool,
    normalize_newlines_opt: bool,
    trim: bool,
    collapse_whitespace_opt: bool,
    ignore_case: bool,
    replace: list[str] | None,
    redact: list[str] | None,
    json_ignore: list[str] | None,
    quiet: bool,
    color: str,
    diff_context: int,
    diff_format: str,
    update: bool,
) -> None:
    """Run the expect (match) command logic."""
    # Read actual from stdin
    actual = sys.stdin.read()

    # Get expected value
    expected_text = _get_expected(expected, expected_file, update)
    if expected_text is None:
        print(
            "Error: expected value required (argument or -f FILE)",
            file=sys.stderr,
        )
        raise typer.Exit(2)

    # Build config
    mode = _determine_mode(
        contains, regex, json_mode, jsonl, jsonl_set, jsonl_key, jsonl_contains,
        not_contains, not_regex
    )

    # Parse and compile regex patterns with validation
    try:
        raw_replacements = _parse_replacements(replace or [])
        compiled_replacements = compile_replacements(raw_replacements)
        compiled_redactions = compile_redactions(tuple(redact or []))
    except RegexError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(2)

    norm_opts = NormalizeOptions(
        strip_ansi=strip_ansi,
        normalize_newlines=normalize_newlines_opt,
        trim=trim,
        collapse_whitespace=collapse_whitespace_opt,
        ignore_case=ignore_case,
        replacements=compiled_replacements,
        redactions=compiled_redactions,
    )
    config = ExpectConfig(
        mode=mode,
        normalize=norm_opts,
        json_ignore_paths=tuple(json_ignore or []),
        jsonl_key_field=jsonl_key,
        quiet=quiet,
        color=ColorMode(color),
        diff_context=diff_context,
        diff_format=DiffFormat(diff_format),
        update_file=update,
    )

    # Preprocess
    actual_processed = preprocess(actual, norm_opts)
    expected_processed = preprocess(expected_text, norm_opts)

    # Compare
    result = compare(actual_processed, expected_processed, config)

    if result.success:
        raise typer.Exit(0)

    # Handle update mode
    if update and expected_file:
        expected_file.write_text(actual)
        print(f"Updated: {expected_file}", file=sys.stderr)
        raise typer.Exit(0)

    # Output error
    if not quiet:
        print(format_error(result, config), file=sys.stderr)
    raise typer.Exit(1)


@app.callback(
    invoke_without_command=True,
    context_settings={"allow_interspersed_args": False},
)
def callback(
    ctx: typer.Context,
    # Expected value sources
    expected: Annotated[
        Optional[str],
        typer.Argument(help="Expected output"),
    ] = None,
    expected_file: Annotated[
        Optional[Path],
        typer.Option(
            "-f",
            "--expected-file",
            help="Read expected from file",
        ),
    ] = None,
    # Comparison modes
    contains: Annotated[
        bool,
        typer.Option(help="Check substring containment"),
    ] = False,
    regex: Annotated[
        bool,
        typer.Option(help="Match against regex pattern"),
    ] = False,
    json_mode: Annotated[
        bool,
        typer.Option("--json", help="Compare as JSON (semantic)"),
    ] = False,
    jsonl: Annotated[
        bool,
        typer.Option(help="Compare as JSONL (semantic)"),
    ] = False,
    jsonl_set: Annotated[
        bool,
        typer.Option(help="Compare JSONL as unordered set"),
    ] = False,
    jsonl_key: Annotated[
        Optional[str],
        typer.Option(help="Compare JSONL by key field"),
    ] = None,
    jsonl_contains: Annotated[
        bool,
        typer.Option(help="Check JSONL contains expected records"),
    ] = False,
    # Negative assertions
    not_contains: Annotated[
        bool,
        typer.Option(help="Assert substring is NOT present"),
    ] = False,
    not_regex: Annotated[
        bool,
        typer.Option(help="Assert regex does NOT match"),
    ] = False,
    # Normalization options
    strip_ansi: Annotated[
        bool,
        typer.Option(help="Remove ANSI escape sequences"),
    ] = False,
    normalize_newlines_opt: Annotated[
        bool,
        typer.Option("--normalize-newlines", help="Convert CRLF to LF"),
    ] = False,
    trim: Annotated[
        bool,
        typer.Option(help="Strip leading/trailing whitespace"),
    ] = False,
    collapse_whitespace_opt: Annotated[
        bool,
        typer.Option("--collapse-whitespace", help="Collapse whitespace runs"),
    ] = False,
    ignore_case: Annotated[
        bool,
        typer.Option("-i", "--ignore-case", help="Case-insensitive"),
    ] = False,
    # Pattern transformation
    replace: Annotated[
        Optional[list[str]],
        typer.Option(help="Replace REGEX=>REPL (repeatable)"),
    ] = None,
    redact: Annotated[
        Optional[list[str]],
        typer.Option(help="Replace REGEX with <redacted>"),
    ] = None,
    # JSON options
    json_ignore: Annotated[
        Optional[list[str]],
        typer.Option(help="Ignore JSON path (repeatable)"),
    ] = None,
    # Output options
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Suppress error output"),
    ] = False,
    color: Annotated[
        str,
        typer.Option(help="Color mode: auto, always, never"),
    ] = "auto",
    diff_context: Annotated[
        int,
        typer.Option(help="Diff context lines"),
    ] = 3,
    diff_format: Annotated[
        str,
        typer.Option(help="Diff format: unified, side-by-side, inline, none"),
    ] = "unified",
    # Update mode
    update: Annotated[
        bool,
        typer.Option(help="Update expected file on mismatch"),
    ] = False,
    # Version
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
    """Assert CLI output matches expected value."""
    # If a subcommand is invoked, don't run the default expect behavior
    if ctx.invoked_subcommand is not None:
        return

    # Run expect logic
    _run_expect(
        expected,
        expected_file,
        contains,
        regex,
        json_mode,
        jsonl,
        jsonl_set,
        jsonl_key,
        jsonl_contains,
        not_contains,
        not_regex,
        strip_ansi,
        normalize_newlines_opt,
        trim,
        collapse_whitespace_opt,
        ignore_case,
        replace,
        redact,
        json_ignore,
        quiet,
        color,
        diff_context,
        diff_format,
        update,
    )


def _get_expected(
    arg: str | None,
    file_path: Path | None,
    update_mode: bool,
) -> str | None:
    """Get expected value from argument or file."""
    if file_path:
        if not file_path.exists():
            if update_mode:
                return ""  # Will create on update
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            raise typer.Exit(2)
        try:
            return file_path.read_text()
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            raise typer.Exit(2)
    return arg


def _determine_mode(
    contains: bool,
    regex: bool,
    json_mode: bool,
    jsonl: bool,
    jsonl_set: bool,
    jsonl_key: str | None,
    jsonl_contains: bool,
    not_contains: bool,
    not_regex: bool,
) -> CompareMode:
    """Determine comparison mode from flags."""
    if not_contains:
        return CompareMode.NOT_CONTAINS
    if not_regex:
        return CompareMode.NOT_REGEX
    if jsonl_key:
        return CompareMode.JSONL_KEY
    if jsonl_set:
        return CompareMode.JSONL_SET
    if jsonl_contains:
        return CompareMode.JSONL_CONTAINS
    if jsonl:
        return CompareMode.JSONL
    if json_mode:
        return CompareMode.JSON
    if regex:
        return CompareMode.REGEX
    if contains:
        return CompareMode.CONTAINS
    return CompareMode.EXACT


def _parse_replacements(args: list[str]) -> tuple[tuple[str, str], ...]:
    """Parse --replace arguments (REGEX=>REPL format) into tuples."""
    result = []
    for arg in args:
        if "=>" not in arg:
            print(f"Error: --replace needs REGEX=>REPL: {arg}", file=sys.stderr)
            raise typer.Exit(2)
        pattern, repl = arg.split("=>", 1)
        result.append((pattern, repl))
    return tuple(result)


def main(args: list[str] | None = None) -> int:
    """Main entry point for backwards compatibility."""
    # Use sys.argv if args not provided
    if args is None:
        args = sys.argv[1:]

    # Handle "test" subcommand - routed manually because Typer's callback
    # with positional expected argument conflicts with subcommand detection
    if args and args[0] == "test":
        try:
            _run_test_command(args[1:])
            return 0
        except typer.Exit as e:
            return e.exit_code

    # Handle "exec" subcommand
    if args and args[0] == "exec":
        try:
            _run_exec_command(args[1:])
            return 0
        except typer.Exit as e:
            return e.exit_code

    try:
        result = app(args, standalone_mode=False)
        return result if result is not None else 0
    except typer.Exit as e:
        return e.exit_code


# Separate Typer apps for subcommands - used to provide consistent help and parsing
# These are invoked via manual routing in main() because the main app's callback
# has a positional expected argument that conflicts with subcommand detection

exec_app = typer.Typer(
    help="Execute command and assert on output.",
    add_completion=False,
)

test_app = typer.Typer(
    help="Run bash blocks in markdown files as tests.",
    add_completion=False,
    context_settings={"allow_interspersed_args": True},
)


@exec_app.callback(invoke_without_command=True)
def _exec_callback(
    ctx: typer.Context,
    exit_code: Annotated[
        Optional[int],
        typer.Option("--exit-code", help="Expected exit code"),
    ] = None,
    stdout: Annotated[
        Optional[str],
        typer.Option(help="Expected stdout (exact)"),
    ] = None,
    stdout_contains: Annotated[
        Optional[str],
        typer.Option(help="Stdout must contain"),
    ] = None,
    stdout_not_contains: Annotated[
        Optional[str],
        typer.Option(help="Stdout must NOT contain"),
    ] = None,
    stdout_regex: Annotated[
        Optional[str],
        typer.Option(help="Stdout must match regex"),
    ] = None,
    stdout_not_regex: Annotated[
        Optional[str],
        typer.Option(help="Stdout must NOT match regex"),
    ] = None,
    stderr: Annotated[
        Optional[str],
        typer.Option(help="Expected stderr (exact)"),
    ] = None,
    stderr_contains: Annotated[
        Optional[str],
        typer.Option(help="Stderr must contain"),
    ] = None,
    stderr_not_contains: Annotated[
        Optional[str],
        typer.Option(help="Stderr must NOT contain"),
    ] = None,
    stderr_regex: Annotated[
        Optional[str],
        typer.Option(help="Stderr must match regex"),
    ] = None,
    stderr_not_regex: Annotated[
        Optional[str],
        typer.Option(help="Stderr must NOT match regex"),
    ] = None,
    output_json: Annotated[
        Optional[str],
        typer.Option(help='Match output as JSON: {"stdout":..., "exit_code": N}'),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option("-q", "--quiet", help="Suppress output"),
    ] = False,
    color: Annotated[
        str,
        typer.Option(help="Color mode: auto, always, never"),
    ] = "auto",
    timeout: Annotated[
        Optional[float],
        typer.Option(help="Command timeout in seconds"),
    ] = None,
    command: Annotated[
        Optional[list[str]],
        typer.Argument(help="Command to execute (after --)"),
    ] = None,
) -> None:
    """Execute command and assert on output."""
    from .exec import ExecConfig, check_assertions, run_command

    # Extract command (skip leading -- if present)
    cmd = list(command) if command else []
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if not cmd:
        print("Error: no command specified", file=sys.stderr)
        raise typer.Exit(2)

    # Build config
    config = ExecConfig(
        expected_exit_code=exit_code,
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
            exit_code is not None,
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
        result = run_command(cmd, timeout=config.timeout)
    except FileNotFoundError:
        print(f"Error: command not found: {cmd[0]}", file=sys.stderr)
        raise typer.Exit(2)

    # Check timeout
    if result.exit_code == -1 and config.timeout is not None:
        if not config.quiet:
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
    if not config.quiet:
        for failure in failures:
            expect_config = ExpectConfig(quiet=config.quiet, color=config.color)
            print(format_error(failure, expect_config), file=sys.stderr)

    raise typer.Exit(1)


@test_app.callback(invoke_without_command=True)
def _test_callback(
    ctx: typer.Context,
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
        typer.Option("--fail-fast", help="Stop on first failure"),
    ] = False,
    parallel: Annotated[
        int,
        typer.Option(help="Number of parallel workers"),
    ] = 4,
    timeout: Annotated[
        int,
        typer.Option(help="Timeout per block in seconds"),
    ] = 30,
    shell: Annotated[
        str,
        typer.Option(help="Shell to use for execution"),
    ] = "/bin/bash",
    include: Annotated[
        Optional[str],
        typer.Option(help="Include pattern for blocks"),
    ] = None,
    exclude: Annotated[
        Optional[str],
        typer.Option(help="Exclude pattern for blocks"),
    ] = None,
    line: Annotated[
        Optional[int],
        typer.Option(help="Run only block at this line"),
    ] = None,
    junit_xml: Annotated[
        Optional[Path],
        typer.Option(help="Write JUnit XML report"),
    ] = None,
    json_out: Annotated[
        Optional[Path],
        typer.Option("--json", help="Write JSON report"),
    ] = None,
    tap: Annotated[
        bool,
        typer.Option("--tap", help="Output in TAP format"),
    ] = False,
    env: Annotated[
        Optional[list[str]],
        typer.Option(help="Environment variable (KEY=VALUE)"),
    ] = None,
    cwd: Annotated[
        Optional[Path],
        typer.Option(help="Working directory"),
    ] = None,
) -> None:
    """Run bash blocks in markdown files as tests."""
    from .mdtest import TestConfig, test_command

    # Parse env variables
    env_dict: dict[str, str] = {}
    for item in env or []:
        if "=" in item:
            key, val = item.split("=", 1)
            env_dict[key] = val

    config = TestConfig(
        quiet=quiet,
        verbose=verbose,
        fail_fast=fail_fast,
        parallel=parallel,
        timeout=timeout,
        shell=shell,
        include_pattern=include,
        exclude_pattern=exclude,
        line_filter=line,
        env=env_dict,
        cwd=cwd,
        junit_xml=junit_xml,
        json_output=json_out,
        tap_output=tap,
    )

    exit_code = test_command(list(paths) if paths else [], config)
    raise typer.Exit(exit_code)


def _run_exec_command(args: list[str]) -> None:
    """Route exec subcommand to dedicated Typer app."""
    try:
        result = exec_app(args, standalone_mode=False)
        # Typer returns exit code when standalone_mode=False
        if result is not None:
            raise typer.Exit(result)
    except SystemExit as e:
        # Typer may raise SystemExit, convert to typer.Exit
        raise typer.Exit(e.code if e.code is not None else 0)


def _run_test_command(args: list[str]) -> None:
    """Route test subcommand to dedicated Typer app."""
    try:
        result = test_app(args, standalone_mode=False)
        # Typer returns exit code when standalone_mode=False
        if result is not None:
            raise typer.Exit(result)
    except SystemExit as e:
        # Typer may raise SystemExit, convert to typer.Exit
        raise typer.Exit(e.code if e.code is not None else 0)


def cli() -> None:
    """CLI entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
