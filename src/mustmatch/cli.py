"""
CLI interface - delegates to Rust core via _core module.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .runtime import create_python_namespace, run_bash, run_python
from .version import __version__

HELP = """\
mustmatch - Assert CLI output matches expected value.

Usage:
    command | mustmatch [not] [like] EXPECTED
    mustmatch test [OPTIONS] PATHS
    mustmatch verify-matrix [OPTIONS] DESIGN
    mustmatch lint [OPTIONS] SPEC

Match stdin against expected:
    echo "hello" | mustmatch "hello"
    echo "hello world" | mustmatch like "hello"
    echo "success" | mustmatch not like "error"
    echo '{"a":1}' | mustmatch '{"a":1}'
    echo "v1.2.3" | mustmatch '/v\\d+/'

Test markdown files:
    mustmatch test docs/
    mustmatch test -v README.md

Verify proof-matrix references:
    mustmatch verify-matrix .march/design-final.md --repo-root .

Lint markdown specs:
    mustmatch lint docs/02-cli-assertions.md

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

Verify-matrix options:
    --repo-root PATH     Repo root used to resolve proof references
    --json               Emit structured JSON

Lint options:
    --min-like-len N     Flag mustmatch like literals shorter than this length
    --json               Emit structured JSON
"""

TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
CODE_RE = re.compile(r"`([^`]+)`")
MUSTMATCH_JSON_RE = re.compile(r"\|\s*mustmatch\s+json\b")
SHORT_LIKE_RE = re.compile(r'\|\s*mustmatch\s+like\s+("([^"]*)"|\'([^\']*)\')')
FENCE_RE = re.compile(r"^```(?P<info>.*)$")
REPO_ROOT_FILE_NAMES = {
    "CLAUDE.md",
    "Cargo.lock",
    "Cargo.toml",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "rustfmt.toml",
    "uv.lock",
}
REPO_FILE_EXTENSIONS = {
    ".json",
    ".lock",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
    ".zig",
}
REPO_PATH_PREFIXES = (
    ".march/",
    "bench/",
    "crates/",
    "docs/",
    "lib/",
    "scripts/",
    "spec/",
    "src/",
    "test/",
    "tests/",
)


def looks_like_repo_path(value: str) -> bool:
    """Return True when a backticked table value looks like a repo file path."""
    value = value.strip()
    if not value:
        return False
    if any(ch.isspace() for ch in value):
        return False
    if any(token in value for token in ("://", "${", "&&", "||", ";", "|", ">", "<")):
        return False
    if value.startswith(("~", "$")):
        return False

    candidate = Path(value)

    if value in REPO_ROOT_FILE_NAMES:
        return True
    if candidate.is_absolute():
        return (
            candidate.suffix in REPO_FILE_EXTENSIONS
            or candidate.name in REPO_ROOT_FILE_NAMES
        )
    if value.startswith(REPO_PATH_PREFIXES):
        return True
    return candidate.suffix in REPO_FILE_EXTENSIONS


def collect_table_refs(text: str) -> list[tuple[int, str]]:
    """Collect backticked repo-like references from markdown table rows."""
    refs: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not TABLE_ROW_RE.match(line):
            continue
        for code in CODE_RE.findall(line):
            if looks_like_repo_path(code):
                refs.append((lineno, code))
    return refs


def collect_shell_blocks(text: str) -> list[tuple[int, str, str]]:
    """Collect fenced shell blocks without depending on the Rust extension."""
    blocks: list[tuple[int, str, str]] = []
    current_lang: str | None = None
    current_start: int | None = None
    current_lines: list[str] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        if current_lang is None:
            match = FENCE_RE.match(line)
            if not match:
                continue

            info = match.group("info").strip()
            current_lang = info.split(maxsplit=1)[0].lower() if info else ""
            current_start = lineno + 1
            current_lines = []
            continue

        if line.strip() == "```":
            blocks.append(
                (current_start or lineno, current_lang, "\n".join(current_lines))
            )
            current_lang = None
            current_start = None
            current_lines = []
            continue

        current_lines.append(line)

    return blocks


def lint_spec_file(spec: Path, *, min_like_len: int = 10) -> dict[str, object]:
    """Lint markdown assertions and shell blocks without executing the spec."""
    findings: list[dict[str, object]] = []
    text = spec.read_text()

    for lineno, line in enumerate(text.splitlines(), start=1):
        if MUSTMATCH_JSON_RE.search(line):
            findings.append(
                {
                    "line": lineno,
                    "rule": "invalid-mustmatch-mode",
                    "message": "uses unsupported `mustmatch json` syntax",
                    "text": line.strip(),
                }
            )

        match = SHORT_LIKE_RE.search(line)
        if match:
            literal = match.group(2) if match.group(2) is not None else match.group(3)
            if literal is not None and len(literal) < min_like_len:
                findings.append(
                    {
                        "line": lineno,
                        "rule": "short-like-pattern",
                        "message": (
                            f'uses short `mustmatch like` literal "{literal}" '
                            f"({len(literal)} chars)"
                        ),
                        "text": line.strip(),
                    }
                )

    for start_line, language, block in collect_shell_blocks(text):
        if language not in {"bash", "sh", "shell", "zsh"}:
            continue

        try:
            result = subprocess.run(
                ["bash", "-n"],
                input=block,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("bash is required to lint shell code blocks") from exc

        if result.returncode != 0:
            findings.append(
                {
                    "line": start_line,
                    "rule": "invalid-shell-syntax",
                    "message": result.stderr.strip() or "bash -n failed",
                    "text": block.splitlines()[0] if block.splitlines() else "",
                }
            )

    return {
        "spec": str(spec),
        "finding_count": len(findings),
        "status": "fail" if findings else "pass",
        "findings": findings,
    }


def _run_match(
    expected: str,
    *,
    negate: bool = False,
    like: bool = False,
    ignore_case: bool = False,
    quiet: bool = False,
) -> int:
    """Run the match logic. Returns exit code."""
    from ._core import compare, detect_mode, normalize

    actual = sys.stdin.read()

    actual = normalize(actual, strip_ansi=True, normalize_newlines=True, trim=True)
    expected = normalize(expected, strip_ansi=True, normalize_newlines=True, trim=True)

    mode = detect_mode(expected)

    if like:
        if mode == "json":
            subset = True
            if detect_mode(actual) == "jsonl":
                mode = "jsonl"
        else:
            mode = "contains"
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
    from ._core import create_md_fixture, get_table_for_block, parse_markdown

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
                table = get_table_for_block(result, block)
                table_data: list[dict[str, str]] | None = None
                if table is not None:
                    table_data = [
                        dict(zip(table.headers, row))
                        for row in table.rows
                    ]
                if memory and namespace is not None:
                    if table_data is None:
                        namespace.pop("table", None)
                    else:
                        namespace["table"] = table_data
                    namespace["md"] = create_md_fixture(result, block)
                    run_result = run_python(
                        block.content,
                        globals_dict=namespace,
                        timeout=float(block_timeout),
                    )
                else:
                    ns = create_python_namespace(
                        table=table_data,
                        parse_result=result,
                        current_block=block,
                    )
                    run_result = run_python(
                        block.content,
                        globals_dict=ns,
                        timeout=float(block_timeout),
                    )
            else:
                continue

            timed_out = isinstance(
                run_result.exception,
                (subprocess.TimeoutExpired, TimeoutError),
            )

            if timed_out:
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
    if args[0] == "verify-matrix":
        return _main_verify_matrix(args[1:])
    if args[0] == "lint":
        return _main_lint(args[1:])

    # Default: match command
    return _main_match(args)


def _main_match(args: list[str]) -> int:
    """Parse and run match command."""
    # Parse options first
    ignore_case = False
    quiet = False
    positional: list[str] = []
    expected_separator: int | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if not positional and arg in ("-i", "--ignore-case"):
            ignore_case = True
        elif not positional and arg in ("-q", "--quiet"):
            quiet = True
        elif arg in ("-h", "--help"):
            print(HELP)
            return 0
        elif arg == "--":
            expected_separator = len(positional)
            positional.extend(args[i + 1 :])
            break
        elif not positional and arg.startswith("-"):
            print(f"Error: unknown option: {arg}", file=sys.stderr)
            return 2
        else:
            positional.append(arg)
        i += 1

    # Parse positional grammar:
    #   mustmatch [not] [like] EXPECTED
    #   mustmatch [not] [like] -- EXPECTED
    negate = False
    like = False

    if expected_separator is not None:
        tokens = positional[:expected_separator]
        expected_tokens = positional[expected_separator:]
        if len(expected_tokens) != 1:
            print("Error: expected value required", file=sys.stderr)
            return 2
        expected = expected_tokens[0]
    else:
        tokens = positional
        expected = ""

    j = 0
    if j < len(tokens) and tokens[j] == "not":
        negate = True
        j += 1
    if j < len(tokens) and tokens[j] == "like":
        like = True
        j += 1

    if expected_separator is not None:
        if j != len(tokens):
            print("Error: invalid arguments", file=sys.stderr)
            return 2
    else:
        if j >= len(tokens):
            print("Error: expected value required", file=sys.stderr)
            return 2
        expected = tokens[j]
        j += 1
        if j != len(tokens):
            print("Error: too many arguments", file=sys.stderr)
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


def _main_verify_matrix(args: list[str]) -> int:
    """Parse and run proof-matrix verification."""
    parser = argparse.ArgumentParser(
        prog="mustmatch verify-matrix",
        description="Verify proof-matrix file references resolve inside a repo.",
        add_help=True,
    )
    parser.add_argument("design", type=Path, help="Markdown design file to inspect")
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Repo root used to resolve backticked file references",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of human-readable lines",
    )

    parsed = parser.parse_args(args)

    if not parsed.design.is_file():
        print(f"Error: design file not found: {parsed.design}", file=sys.stderr)
        return 2
    if not parsed.repo_root.is_dir():
        print(f"Error: repo root not found: {parsed.repo_root}", file=sys.stderr)
        return 2

    design = parsed.design.resolve()
    repo_root = parsed.repo_root.resolve()
    refs = collect_table_refs(design.read_text())

    checked: list[dict[str, object]] = []
    failure_count = 0

    for lineno, ref in refs:
        reference_path = Path(ref)
        if reference_path.is_absolute():
            resolved_path = reference_path.resolve()
            status = "invalid"
        else:
            resolved_path = (repo_root / reference_path).resolve()
            if not resolved_path.is_relative_to(repo_root):
                status = "invalid"
            elif resolved_path.exists():
                status = "ok"
            else:
                status = "missing"

        if status != "ok":
            failure_count += 1

        checked.append(
            {
                "line": lineno,
                "reference": ref,
                "resolved_path": str(resolved_path),
                "status": status,
            }
        )

    result = {
        "design": str(design),
        "repo_root": str(repo_root),
        "references_checked": len(checked),
        "failure_count": failure_count,
        "status": "fail" if failure_count else "pass",
        "results": checked,
    }

    if parsed.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for item in checked:
            print(
                f"{str(item['status']).upper()} line {item['line']}: "
                f"{item['reference']} -> {item['resolved_path']}"
            )

    return 1 if failure_count else 0


def _main_lint(args: list[str]) -> int:
    """Parse and run spec assertion lint."""
    parser = argparse.ArgumentParser(
        prog="mustmatch lint",
        description="Lint markdown spec assertions without executing them.",
        add_help=True,
    )
    parser.add_argument("spec", type=Path, help="Markdown spec file to inspect")
    parser.add_argument(
        "--min-like-len",
        type=int,
        default=10,
        help="Flag mustmatch like literals shorter than this length",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of human-readable lines",
    )

    parsed = parser.parse_args(args)

    if not parsed.spec.is_file():
        print(f"Error: spec file not found: {parsed.spec}", file=sys.stderr)
        return 2

    try:
        result = lint_spec_file(
            parsed.spec.resolve(),
            min_like_len=parsed.min_like_len,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if parsed.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"spec={result['spec']}")
        print(f"findings={result['finding_count']}")
        for finding in result["findings"]:
            print(
                f"FAIL line {finding['line']} {finding['rule']}: "
                f"{finding['message']}"
            )

    return 1 if result["finding_count"] else 0


def cli() -> None:
    """CLI entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
