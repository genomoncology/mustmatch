"""
CLI interface - thin layer that delegates to services.

Grammar:
    mustmatch [not] [like] EXPECTED
    mustmatch test PATHS
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .services.comparator import (
    CompareMode,
    compare,
    detect_mode,
    extract_regex_pattern,
)
from .services.normalizer import NormalizeOptions, normalize
from .version import __version__

HELP = """\
mustmatch - Assert CLI output matches expected value.

Usage:
    command | mustmatch [not] [like] EXPECTED
    mustmatch test [OPTIONS] PATHS

Match stdin against expected:
    echo "hello" | mustmatch "hello"
    echo "hello world" | mustmatch like "hello"
    echo "success" | mustmatch not like "error"
    echo '{"a":1}' | mustmatch '{"a":1}'
    echo "v1.2.3" | mustmatch '/v\\d+/'

Test markdown files:
    mustmatch test docs/
    mustmatch test -v README.md

Options:
    -i, --ignore-case    Case-insensitive comparison
    -q, --quiet          Suppress output
    --version            Show version

Test options:
    -v, --verbose        Show each test result
    -x, --fail-fast      Stop on first failure
    --timeout N          Timeout per block (default: 30)
    --lang LANG          Language: bash, python, all
    --memory             Share Python state between blocks
"""


def _run_match(
    expected: str,
    *,
    negate: bool = False,
    like: bool = False,
    ignore_case: bool = False,
    quiet: bool = False,
) -> int:
    """Run the match logic. Returns exit code."""
    actual = sys.stdin.read()

    norm_opts = NormalizeOptions(
        strip_ansi=True,
        normalize_newlines=True,
        trim=True,
        ignore_case=ignore_case,
    )
    actual = normalize(actual, norm_opts)
    expected = normalize(expected, norm_opts)

    mode = detect_mode(expected)

    if mode == CompareMode.REGEX:
        expected = extract_regex_pattern(expected)

    if like:
        if mode == CompareMode.JSON:
            subset = True
        else:
            mode = CompareMode.CONTAINS
            subset = False
    else:
        subset = False

    result = compare(
        actual,
        expected,
        mode=mode,
        subset=subset,
        ignore_case=ignore_case,
    )

    matches = result.matches
    if negate:
        matches = not matches

    if matches:
        return 0

    if not quiet:
        if negate:
            print("FAIL: Expected NOT to match, but it did", file=sys.stderr)
        else:
            print(result.message, file=sys.stderr)

    return 1


def _run_test(
    paths: list[Path],
    *,
    lang: str = "all",
    memory: bool = False,
    timeout: int = 30,
    verbose: bool = False,
    quiet: bool = False,
    fail_fast: bool = False,
) -> int:
    """Run markdown tests. Returns exit code."""
    from .services.parser import parse_markdown
    from .services.runner import create_python_namespace, run_bash, run_python

    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.md"))

    if not files:
        if not quiet:
            print("No markdown files found", file=sys.stderr)
        return 0

    passed = 0
    failed = 0
    skipped = 0

    for file in sorted(files):
        content = file.read_text()
        result = parse_markdown(content)

        blocks = [
            b for b in result.blocks
            if lang == "all" or b.language == lang
        ]

        if not blocks:
            continue

        namespace = create_python_namespace(parse_result=result) if memory else None

        for block in blocks:
            if "skip" in block.directives:
                skipped += 1
                if verbose:
                    print(f"SKIP {file}:{block.line_start} [{block.language}]")
                continue

            name = block.name or "unnamed"

            block_timeout = timeout
            if "timeout" in block.directives:
                try:
                    block_timeout = int(block.directives["timeout"])
                except ValueError:
                    pass

            if block.language == "bash":
                run_result = run_bash(
                    block.content,
                    cwd=file.parent,
                    timeout=float(block_timeout),
                )
            elif block.language == "python":
                if memory and namespace is not None:
                    run_result = run_python(
                        block.content,
                        globals_dict=namespace,
                    )
                else:
                    ns = create_python_namespace(
                        parse_result=result,
                        current_block=block,
                    )
                    run_result = run_python(block.content, globals_dict=ns)
            else:
                continue

            if run_result.exception is not None:
                failed += 1
                if not quiet:
                    print(
                        f"FAIL {file}:{block.line_start} {name} - "
                        f"timeout after {block_timeout}s",
                        file=sys.stderr,
                    )
                if fail_fast:
                    break
            elif run_result.exit_code != 0:
                failed += 1
                if not quiet:
                    msg = (
                        f"FAIL {file}:{block.line_start} {name} - "
                        f"exit {run_result.exit_code}"
                    )
                    print(msg, file=sys.stderr)
                    if verbose and run_result.stderr:
                        print(f"  {run_result.stderr}", file=sys.stderr)
                if fail_fast:
                    break
            else:
                passed += 1
                if verbose:
                    print(f"PASS {file}:{block.line_start} {name}")

        if fail_fast and failed > 0:
            break

    if not quiet:
        parts = []
        if passed:
            parts.append(f"{passed} passed")
        if failed:
            parts.append(f"{failed} failed")
        if skipped:
            parts.append(f"{skipped} skipped")
        print(", ".join(parts) or "no tests")

    return 1 if failed > 0 else 0


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    # Handle --version and --help early
    if args and args[0] in ("-h", "--help"):
        print(HELP)
        return 0

    if not args:
        # No args - if stdin is a tty, show help; otherwise error
        if sys.stdin.isatty():
            print(HELP)
            return 0
        else:
            print("Error: expected value required", file=sys.stderr)
            return 2

    if args[0] == "--version":
        print(f"mustmatch {__version__}")
        return 0

    # Route to test subcommand
    if args[0] == "test":
        return _main_test(args[1:])

    # Default: match command
    return _main_match(args)


def _main_match(args: list[str]) -> int:
    """Parse and run match command."""
    # Parse options first
    ignore_case = False
    quiet = False
    positional: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-i", "--ignore-case"):
            ignore_case = True
        elif arg in ("-q", "--quiet"):
            quiet = True
        elif arg in ("-h", "--help"):
            print(HELP)
            return 0
        elif arg.startswith("-"):
            print(f"Error: unknown option: {arg}", file=sys.stderr)
            return 2
        else:
            positional.append(arg)
        i += 1

    # Parse positional: [not] [like] EXPECTED
    negate = False
    like = False
    expected: str | None = None

    for arg in positional:
        if arg == "not" and not negate and expected is None:
            negate = True
        elif arg == "like" and not like and expected is None:
            like = True
        else:
            expected = arg
            break

    if expected is None:
        print("Error: expected value required", file=sys.stderr)
        return 2

    return _run_match(
        expected,
        negate=negate,
        like=like,
        ignore_case=ignore_case,
        quiet=quiet,
    )


def _main_test(args: list[str]) -> int:
    """Parse and run test command."""
    parser = argparse.ArgumentParser(
        prog="mustmatch test",
        description="Run code blocks in markdown files as tests.",
        add_help=True,
    )
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-x", "--fail-fast", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--lang", default="all")
    parser.add_argument("--memory", action="store_true")

    parsed = parser.parse_args(args)

    return _run_test(
        parsed.paths,
        lang=parsed.lang,
        memory=parsed.memory,
        timeout=parsed.timeout,
        verbose=parsed.verbose,
        quiet=parsed.quiet,
        fail_fast=parsed.fail_fast,
    )


def cli() -> None:
    """CLI entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
