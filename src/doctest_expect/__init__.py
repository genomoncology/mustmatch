"""
doctest-expect: CLI output assertion tool for documentation testing.

Pipe command output to `expect` to verify it matches expected values.
Designed for use with mktestdocs to test CLI examples in documentation.

Usage:
    # Exact match
    echo "hello world" | expect "hello world"

    # Contains (substring)
    python --help | expect --contains "usage:"

    # JSONL - semantic comparison (field order independent)
    echo '{"name": "alice", "age": 30}' | expect --jsonl '{"age": 30, "name": "alice"}'

    # JSONL contains - check output contains expected records
    cat data.jsonl | expect --jsonl-contains '{"id": 1}'

Exit codes:
    0 - Match
    1 - Mismatch (prints diff to stderr)
    2 - Invalid arguments
"""

__version__ = "0.1.0"

import argparse
import json
import sys
from typing import Any


def normalize_json(obj: Any) -> Any:
    """Recursively sort dicts for stable comparison.

    Args:
        obj: Any JSON-compatible value

    Returns:
        The same structure with all dicts sorted by key
    """
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [normalize_json(v) for v in obj]
    return obj


def parse_jsonl(text: str) -> list[dict]:
    """Parse JSONL text into list of dicts.

    Args:
        text: JSONL string (one JSON object per line)

    Returns:
        List of parsed JSON objects

    Raises:
        json.JSONDecodeError: If any line is not valid JSON
    """
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    return [json.loads(line) for line in lines]


def compare_exact(actual: str, expected: str) -> tuple[bool, str]:
    """Exact string comparison.

    Args:
        actual: Actual output from command
        expected: Expected output string

    Returns:
        Tuple of (success, error_message)
    """
    actual = actual.rstrip('\n')
    expected = expected.rstrip('\n')
    if actual == expected:
        return True, ""
    return False, f"Expected:\n{expected}\n\nActual:\n{actual}"


def compare_contains(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual contains expected substring.

    Args:
        actual: Actual output from command
        expected: Expected substring

    Returns:
        Tuple of (success, error_message)
    """
    if expected.strip() in actual:
        return True, ""
    return False, f"Expected to contain:\n{expected}\n\nActual:\n{actual}"


def compare_jsonl(actual: str, expected: str) -> tuple[bool, str]:
    """Compare JSONL output semantically.

    Record order matters, but field order within records does not.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL string

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if len(actual_records) != len(expected_records):
        return False, (
            f"Record count mismatch: expected {len(expected_records)}, "
            f"got {len(actual_records)}"
        )

    for i, (act, exp) in enumerate(zip(actual_records, expected_records)):
        if normalize_json(act) != normalize_json(exp):
            return False, (
                f"Record {i} mismatch:\n"
                f"Expected: {json.dumps(exp)}\n"
                f"Actual: {json.dumps(act)}"
            )

    return True, ""


def compare_jsonl_contains(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual JSONL contains all expected records.

    Each expected record must match at least one actual record.
    Matching is done by checking all fields in expected exist in actual.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL records (subset)

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = [normalize_json(r) for r in parse_jsonl(actual)]
        expected_records = [normalize_json(r) for r in parse_jsonl(expected)]
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    missing = []
    for exp in expected_records:
        found = False
        for act in actual_records:
            if isinstance(exp, dict) and isinstance(act, dict):
                if all(act.get(k) == v for k, v in exp.items()):
                    found = True
                    break
            elif exp == act:
                found = True
                break
        if not found:
            missing.append(exp)

    if missing:
        return False, "Missing expected records:\n" + "\n".join(json.dumps(m) for m in missing)

    return True, ""


def main(args: list[str] | None = None) -> int:
    """Main entry point for the expect CLI.

    Args:
        args: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0=match, 1=mismatch, 2=error)
    """
    parser = argparse.ArgumentParser(
        prog="expect",
        description="Assert CLI output matches expected value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("expected", nargs="?", help="Expected output")
    parser.add_argument("--contains", action="store_true",
                        help="Check substring containment")
    parser.add_argument("--jsonl", action="store_true",
                        help="Compare as JSONL (semantic, field order independent)")
    parser.add_argument("--jsonl-contains", action="store_true",
                        help="Check JSONL contains expected records")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress diff output on failure")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    parsed = parser.parse_args(args)

    # Read actual output from stdin
    actual = sys.stdin.read()

    # Get expected from argument
    if parsed.expected is None:
        print("Error: expected value required", file=sys.stderr)
        return 2

    expected = parsed.expected

    # Choose comparison mode
    if parsed.jsonl_contains:
        ok, msg = compare_jsonl_contains(actual, expected)
    elif parsed.jsonl:
        ok, msg = compare_jsonl(actual, expected)
    elif parsed.contains:
        ok, msg = compare_contains(actual, expected)
    else:
        ok, msg = compare_exact(actual, expected)

    if ok:
        return 0
    else:
        if not parsed.quiet:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1


def cli() -> None:
    """CLI entry point that exits with the return code."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
