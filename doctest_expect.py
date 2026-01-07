#!/usr/bin/env python3
"""
doctest-expect: Assert CLI output matches expected value.

Usage in documentation:

    # Exact match
    findterms --version | doctest-expect "findterms 0.1.0"

    # Contains (substring)
    findterms --help | doctest-expect --contains "Usage:"

    # JSONL - each line is valid JSON, compare semantically
    echo '{"text": "hello"}' | findterms extract | doctest-expect --jsonl '{"term": "hello"}'

    # JSONL contains - actual output contains expected records
    findterms scan doc.txt | doctest-expect --jsonl-contains '{"entity_id": "D001234"}'

    # Multi-line expected (heredoc)
    findterms scan doc.txt | doctest-expect --jsonl <<'EOF'
    {"entity_id": "D001234", "term": "diabetes"}
    {"entity_id": "D005678", "term": "insulin"}
    EOF

Exit codes:
    0 - Match
    1 - Mismatch (prints diff)
    2 - Invalid arguments
"""

import argparse
import json
import sys
from typing import Any


def normalize_json(obj: Any) -> Any:
    """Recursively sort dicts for comparison."""
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [normalize_json(v) for v in obj]
    return obj


def parse_jsonl(text: str) -> list[dict]:
    """Parse JSONL text into list of dicts."""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    return [json.loads(line) for line in lines]


def compare_exact(actual: str, expected: str) -> tuple[bool, str]:
    """Exact string comparison."""
    actual = actual.rstrip('\n')
    expected = expected.rstrip('\n')
    if actual == expected:
        return True, ""
    return False, f"Expected:\n{expected}\n\nActual:\n{actual}"


def compare_contains(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual contains expected substring."""
    if expected.strip() in actual:
        return True, ""
    return False, f"Expected to contain:\n{expected}\n\nActual:\n{actual}"


def compare_jsonl(actual: str, expected: str) -> tuple[bool, str]:
    """Compare JSONL output semantically (order matters, field order doesn't)."""
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if len(actual_records) != len(expected_records):
        return False, f"Record count mismatch: expected {len(expected_records)}, got {len(actual_records)}"

    for i, (act, exp) in enumerate(zip(actual_records, expected_records)):
        if normalize_json(act) != normalize_json(exp):
            return False, f"Record {i} mismatch:\nExpected: {json.dumps(exp)}\nActual: {json.dumps(act)}"

    return True, ""


def compare_jsonl_contains(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual JSONL contains all expected records (subset match)."""
    try:
        actual_records = [normalize_json(r) for r in parse_jsonl(actual)]
        expected_records = [normalize_json(r) for r in parse_jsonl(expected)]
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    missing = []
    for exp in expected_records:
        # Check if expected record matches any actual record (partial match on fields)
        found = False
        for act in actual_records:
            if all(act.get(k) == v for k, v in exp.items() if not isinstance(exp, dict) or k in exp):
                found = True
                break
        if not found:
            missing.append(exp)

    if missing:
        return False, f"Missing expected records:\n" + "\n".join(json.dumps(m) for m in missing)

    return True, ""


def main():
    parser = argparse.ArgumentParser(
        description="Assert CLI output matches expected value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("expected", nargs="?", help="Expected output (or use stdin heredoc)")
    parser.add_argument("--contains", action="store_true", help="Check substring containment")
    parser.add_argument("--jsonl", action="store_true", help="Compare as JSONL (semantic)")
    parser.add_argument("--jsonl-contains", action="store_true", help="Check JSONL contains expected records")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress diff output on failure")

    args = parser.parse_args()

    # Read actual output from stdin
    actual = sys.stdin.read()

    # Get expected from argument
    if args.expected is None:
        print("Error: expected value required", file=sys.stderr)
        sys.exit(2)

    expected = args.expected

    # Choose comparison mode
    if args.jsonl_contains:
        ok, msg = compare_jsonl_contains(actual, expected)
    elif args.jsonl:
        ok, msg = compare_jsonl(actual, expected)
    elif args.contains:
        ok, msg = compare_contains(actual, expected)
    else:
        ok, msg = compare_exact(actual, expected)

    if ok:
        sys.exit(0)
    else:
        if not args.quiet:
            print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
