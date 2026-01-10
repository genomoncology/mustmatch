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
        contains, regex, json_mode, jsonl, jsonl_set, jsonl_key, jsonl_contains
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
) -> CompareMode:
    """Determine comparison mode from flags."""
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

    # Handle special case where "test" is the first argument
    # We need to explicitly route to test command since Typer captures it
    # as the expected argument value
    if args and args[0] == "test":
        test_args = args[1:]
        try:
            _run_mdtest(test_args)
            return 0
        except typer.Exit as e:
            return e.exit_code

    try:
        result = app(args, standalone_mode=False)
        return result if result is not None else 0
    except typer.Exit as e:
        return e.exit_code


def _run_mdtest(args: list[str]) -> None:
    """Direct entry point for test command."""
    import argparse
    from pathlib import Path

    from .mdtest import TestConfig, test_command

    parser = argparse.ArgumentParser(description="Run bash blocks in markdown files")
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--shell", default="/bin/bash")
    parser.add_argument("--include")
    parser.add_argument("--exclude")
    parser.add_argument("--line", type=int)
    parser.add_argument("--junit-xml", type=Path)
    parser.add_argument("--json", type=Path, dest="json_out")
    parser.add_argument("--tap", action="store_true")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--cwd", type=Path)

    parsed = parser.parse_args(args)

    # Parse env variables
    env_dict: dict[str, str] = {}
    for item in parsed.env:
        if "=" in item:
            key, val = item.split("=", 1)
            env_dict[key] = val

    config = TestConfig(
        quiet=parsed.quiet,
        verbose=parsed.verbose,
        fail_fast=parsed.fail_fast,
        parallel=parsed.parallel,
        timeout=parsed.timeout,
        shell=parsed.shell,
        include_pattern=parsed.include,
        exclude_pattern=parsed.exclude,
        line_filter=parsed.line,
        env=env_dict,
        cwd=parsed.cwd,
        junit_xml=parsed.junit_xml,
        json_output=parsed.json_out,
        tap_output=parsed.tap,
    )

    exit_code = test_command(parsed.paths or [], config)
    raise typer.Exit(exit_code)


def cli() -> None:
    """CLI entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
