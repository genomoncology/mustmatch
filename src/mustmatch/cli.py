"""CLI interface for mustmatch.

Grammar:
    mustmatch [-i] [not] [like] EXPECTED
    mustmatch test PATHS
    mustmatch exec -- CMD
"""

from __future__ import annotations

import sys
from pathlib import Path

from .compare import compare
from .config import ColorMode, CompareMode, MatchConfig
from .normalize import preprocess
from .output import format_error
from .version import __version__


def parse_args(args: list[str]) -> tuple[MatchConfig, str | None, Path | None]:
    """Parse command line arguments for main match command.

    Grammar: mustmatch [-i] [not] [like] EXPECTED

    Returns:
        Tuple of (config, expected_value, expected_file)
    """
    ignore_case = False
    negated = False
    partial = False  # "like" modifier
    expected: str | None = None
    expected_file: Path | None = None
    quiet = False
    color = ColorMode.AUTO
    json_ignore: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]

        # Flags
        if arg in ("-i", "--ignore-case"):
            ignore_case = True
            i += 1
            continue

        if arg in ("-q", "--quiet"):
            quiet = True
            i += 1
            continue

        if arg in ("-f", "--file"):
            if i + 1 >= len(args):
                print("Error: -f requires a file path", file=sys.stderr)
                sys.exit(2)
            expected_file = Path(args[i + 1])
            i += 2
            continue

        if arg == "--color":
            if i + 1 >= len(args):
                print("Error: --color requires a value", file=sys.stderr)
                sys.exit(2)
            try:
                color = ColorMode(args[i + 1])
            except ValueError:
                print(f"Error: invalid color mode: {args[i + 1]}", file=sys.stderr)
                sys.exit(2)
            i += 2
            continue

        if arg == "--ignore":
            if i + 1 >= len(args):
                print("Error: --ignore requires a JSON path", file=sys.stderr)
                sys.exit(2)
            json_ignore.append(args[i + 1])
            i += 2
            continue

        if arg == "--version":
            print(f"mustmatch {__version__}")
            sys.exit(0)

        if arg in ("-h", "--help"):
            print_help()
            sys.exit(0)

        # Modifiers (positional keywords)
        if arg == "not":
            negated = True
            i += 1
            continue

        if arg == "like":
            partial = True
            i += 1
            continue

        # Expected value (first non-flag, non-modifier argument)
        if not arg.startswith("-"):
            expected = arg
            i += 1
            # Consume remaining args as part of expected if quoted badly
            break

        # Unknown flag
        print(f"Error: unknown option: {arg}", file=sys.stderr)
        sys.exit(2)

    # Determine mode
    if negated and partial:
        mode = CompareMode.NOT_CONTAINS
    elif negated:
        mode = CompareMode.NOT_EXACT
    elif partial:
        mode = CompareMode.CONTAINS
    else:
        mode = CompareMode.EXACT

    config = MatchConfig(
        mode=mode,
        ignore_case=ignore_case,
        json_ignore_paths=tuple(json_ignore),
        quiet=quiet,
        color=color,
    )

    return config, expected, expected_file


def print_help() -> None:
    """Print help message."""
    print("""mustmatch - CLI output assertion tool

USAGE:
    command | mustmatch [OPTIONS] [not] [like] EXPECTED
    mustmatch test [OPTIONS] PATHS...
    mustmatch exec [OPTIONS] -- COMMAND...

MAIN COMMAND:
    Pipe output to mustmatch to verify it matches expected value.

    Modifiers:
        not         Negate the match (must NOT match)
        like        Partial match (contains/subset)

    Auto-detection:
        /pattern/   Treated as regex
        {...}       Treated as JSON object
        [...]       Treated as JSON array
        other       Treated as string

OPTIONS:
    -i, --ignore-case   Case-insensitive comparison
    -q, --quiet         Suppress error output
    -f, --file FILE     Read expected value from file
    --ignore PATH       Ignore JSON path (repeatable)
    --color MODE        Color mode: auto, always, never
    --version           Show version
    -h, --help          Show this help

EXAMPLES:
    echo "hello" | mustmatch "hello"
    echo "hello world" | mustmatch like "hello"
    echo "success" | mustmatch not like "error"
    echo '{"a":1}' | mustmatch '{"a":1}'
    echo "v1.2.3" | mustmatch "/v\\d+\\.\\d+/"

SUBCOMMANDS:
    test    Run code blocks in markdown files as tests
    exec    Execute command and assert on output

EXIT CODES:
    0       Match successful
    1       Match failed
    2       Invalid arguments
""")


def run_match(args: list[str]) -> int:
    """Run the main match command."""
    config, expected, expected_file = parse_args(args)

    # Read actual from stdin
    if sys.stdin.isatty():
        print("Error: no input (pipe command output to mustmatch)", file=sys.stderr)
        return 2

    actual = sys.stdin.read()

    # Get expected value
    if expected_file:
        if not expected_file.exists():
            print(f"Error: file not found: {expected_file}", file=sys.stderr)
            return 2
        try:
            expected = expected_file.read_text()
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 2
        except UnicodeDecodeError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 2
    elif expected is None:
        print("Error: expected value required", file=sys.stderr)
        return 2

    # Preprocess
    actual = preprocess(actual)
    expected = preprocess(expected)

    # Apply ignore_case
    if config.ignore_case:
        actual = actual.lower()
        expected = expected.lower()

    # Compare
    result = compare(actual, expected, config)

    if result.success:
        return 0

    if not config.quiet:
        print(format_error(result, config), file=sys.stderr)

    return 1


def run_test(args: list[str]) -> int:
    """Run the test subcommand."""
    from .mdtest import TestConfig, run_command

    # Parse test-specific args
    quiet = False
    verbose = False
    fail_fast = False
    parallel = 4
    timeout = 30
    shell = "/bin/bash"
    include_pattern = None
    exclude_pattern = None
    line_filter = None
    env: dict[str, str] = {}
    cwd = None
    junit_xml = None
    json_output = None
    tap_output = False
    lang = "bash"
    memory = False
    paths: list[Path] = []

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ("-q", "--quiet"):
            quiet = True
        elif arg in ("-v", "--verbose"):
            verbose = True
        elif arg == "--fail-fast":
            fail_fast = True
        elif arg == "--parallel" and i + 1 < len(args):
            parallel = int(args[i + 1])
            i += 1
        elif arg == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 1
        elif arg == "--shell" and i + 1 < len(args):
            shell = args[i + 1]
            i += 1
        elif arg == "--include" and i + 1 < len(args):
            include_pattern = args[i + 1]
            i += 1
        elif arg == "--exclude" and i + 1 < len(args):
            exclude_pattern = args[i + 1]
            i += 1
        elif arg == "--line" and i + 1 < len(args):
            line_filter = int(args[i + 1])
            i += 1
        elif arg == "--env" and i + 1 < len(args):
            key, val = args[i + 1].split("=", 1)
            env[key] = val
            i += 1
        elif arg == "--cwd" and i + 1 < len(args):
            cwd = Path(args[i + 1])
            i += 1
        elif arg == "--junit-xml" and i + 1 < len(args):
            junit_xml = Path(args[i + 1])
            i += 1
        elif arg == "--json" and i + 1 < len(args):
            json_output = Path(args[i + 1])
            i += 1
        elif arg == "--tap":
            tap_output = True
        elif arg == "--lang" and i + 1 < len(args):
            lang = args[i + 1]
            i += 1
        elif arg == "--memory":
            memory = True
        elif arg in ("-h", "--help"):
            print_test_help()
            return 0
        elif not arg.startswith("-"):
            paths.append(Path(arg))
        else:
            print(f"Error: unknown option: {arg}", file=sys.stderr)
            return 2

        i += 1

    config = TestConfig(
        quiet=quiet,
        verbose=verbose,
        fail_fast=fail_fast,
        parallel=parallel,
        timeout=timeout,
        shell=shell,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
        line_filter=line_filter,
        env=env,
        cwd=cwd,
        junit_xml=junit_xml,
        json_output=json_output,
        tap_output=tap_output,
        lang=lang,
        memory=memory,
    )

    return run_command(paths, config)


def print_test_help() -> None:
    """Print test subcommand help."""
    print("""mustmatch test - Run code blocks in markdown files

USAGE:
    mustmatch test [OPTIONS] PATHS...

OPTIONS:
    -q, --quiet         Minimal output (summary only)
    -v, --verbose       Verbose output (show all tests)
    --fail-fast         Stop on first failure
    --parallel N        Number of parallel workers (default: 4)
    --timeout N         Timeout per block in seconds (default: 30)
    --shell PATH        Shell to use (default: /bin/bash)
    --include PATTERN   Include blocks matching pattern
    --exclude PATTERN   Exclude blocks matching pattern
    --line N            Run only block at line N
    --env KEY=VALUE     Set environment variable
    --cwd PATH          Working directory
    --junit-xml PATH    Write JUnit XML report
    --json PATH         Write JSON report
    --tap               Output in TAP format
    --lang LANG         Language: bash, python, all (default: bash)
    --memory            Share state between Python blocks
    -h, --help          Show this help

EXAMPLES:
    mustmatch test docs/
    mustmatch test -v README.md
    mustmatch test --lang python --memory docs/tutorial.md
""")


def run_exec(args: list[str]) -> int:
    """Run the exec subcommand."""
    from .exec import ExecConfig, check_assertions, run_command

    # Parse exec-specific args
    exit_code = None
    stdout_exact = None
    stdout_contains = None
    stdout_not_contains = None
    stdout_regex = None
    stderr_exact = None
    stderr_contains = None
    stderr_not_contains = None
    stderr_regex = None
    quiet = False
    color = ColorMode.AUTO
    timeout = None
    command: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--":
            command = args[i + 1:]
            break
        elif arg == "--exit-code" and i + 1 < len(args):
            exit_code = int(args[i + 1])
            i += 1
        elif arg == "--stdout" and i + 1 < len(args):
            stdout_exact = args[i + 1]
            i += 1
        elif arg == "--stdout-like" and i + 1 < len(args):
            stdout_contains = args[i + 1]
            i += 1
        elif arg == "--stdout-not-like" and i + 1 < len(args):
            stdout_not_contains = args[i + 1]
            i += 1
        elif arg == "--stdout-regex" and i + 1 < len(args):
            stdout_regex = args[i + 1]
            i += 1
        elif arg == "--stderr" and i + 1 < len(args):
            stderr_exact = args[i + 1]
            i += 1
        elif arg == "--stderr-like" and i + 1 < len(args):
            stderr_contains = args[i + 1]
            i += 1
        elif arg == "--stderr-not-like" and i + 1 < len(args):
            stderr_not_contains = args[i + 1]
            i += 1
        elif arg == "--stderr-regex" and i + 1 < len(args):
            stderr_regex = args[i + 1]
            i += 1
        elif arg in ("-q", "--quiet"):
            quiet = True
        elif arg == "--color" and i + 1 < len(args):
            color = ColorMode(args[i + 1])
            i += 1
        elif arg == "--timeout" and i + 1 < len(args):
            timeout = float(args[i + 1])
            i += 1
        elif arg in ("-h", "--help"):
            print_exec_help()
            return 0
        else:
            print(f"Error: unknown option: {arg}", file=sys.stderr)
            return 2

        i += 1

    if not command:
        print("Error: no command specified (use -- before command)", file=sys.stderr)
        return 2

    # Check at least one assertion
    has_assertion = any([
        exit_code is not None,
        stdout_exact is not None,
        stdout_contains is not None,
        stdout_not_contains is not None,
        stdout_regex is not None,
        stderr_exact is not None,
        stderr_contains is not None,
        stderr_not_contains is not None,
        stderr_regex is not None,
    ])

    if not has_assertion:
        print("Error: at least one assertion required", file=sys.stderr)
        return 2

    config = ExecConfig(
        expected_exit_code=exit_code,
        stdout_exact=stdout_exact,
        stdout_contains=stdout_contains,
        stdout_not_contains=stdout_not_contains,
        stdout_regex=stdout_regex,
        stderr_exact=stderr_exact,
        stderr_contains=stderr_contains,
        stderr_not_contains=stderr_not_contains,
        stderr_regex=stderr_regex,
        quiet=quiet,
        color=color,
        timeout=timeout,
    )

    try:
        result = run_command(command, timeout=timeout)
    except FileNotFoundError:
        print(f"Error: command not found: {command[0]}", file=sys.stderr)
        return 2

    if result.exit_code == -1 and timeout is not None:
        if not quiet:
            print(f"FAIL: Command timed out after {timeout}s", file=sys.stderr)
        return 1

    failures = check_assertions(result, config)

    if not failures:
        return 0

    if not quiet:
        match_config = MatchConfig(quiet=quiet, color=color)
        for failure in failures:
            print(format_error(failure, match_config), file=sys.stderr)

    return 1


def print_exec_help() -> None:
    """Print exec subcommand help."""
    print("""mustmatch exec - Execute command and assert on output

USAGE:
    mustmatch exec [OPTIONS] -- COMMAND...

OPTIONS:
    --exit-code N       Expected exit code
    --stdout VALUE      Expected stdout (exact)
    --stdout-like VALUE Stdout must contain
    --stdout-not-like   Stdout must NOT contain
    --stdout-regex PAT  Stdout must match regex
    --stderr VALUE      Expected stderr (exact)
    --stderr-like VALUE Stderr must contain
    --stderr-not-like   Stderr must NOT contain
    --stderr-regex PAT  Stderr must match regex
    --timeout N         Command timeout in seconds
    -q, --quiet         Suppress error output
    --color MODE        Color mode: auto, always, never
    -h, --help          Show this help

EXAMPLES:
    mustmatch exec --exit-code 0 -- echo hello
    mustmatch exec --stdout-like "ok" -- curl localhost
""")


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    if not args:
        print_help()
        return 0

    # Route to subcommands
    if args[0] == "test":
        return run_test(args[1:])
    if args[0] == "exec":
        return run_exec(args[1:])

    # Main match command
    return run_match(args)


def cli() -> None:
    """CLI entry point."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
