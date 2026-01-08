"""
doctest-expect: CLI output assertion tool for documentation testing.

Pipe command output to `expect` to verify it matches expected values.
Designed for use with mktestdocs to test CLI examples in documentation.

Usage:
    # Exact match
    echo "hello world" | expect "hello world"

    # Contains (substring)
    python --help | expect --contains "usage:"

    # Regex match
    mycli run | expect --regex 'finished in \\d+\\.\\d+s'

    # JSONL - semantic comparison (field order independent)
    echo '{"name": "alice", "age": 30}' | expect --jsonl '{"age": 30, "name": "alice"}'

    # JSON - single JSON value semantic match
    mycli config | expect --json '{"debug": true}'

    # JSONL contains - check output contains expected records
    cat data.jsonl | expect --jsonl-contains '{"id": 1}'

    # JSONL set - order-independent multiset compare
    mycli list | expect --jsonl-set '{"id": 2}\\n{"id": 1}'

    # With normalization
    mycli status | expect --contains "OK" --strip-ansi --normalize-newlines

    # Expected from file
    mycli help | expect -f docs/expected/help.txt

Exit codes:
    0 - Match
    1 - Mismatch (prints diff to stderr)
    2 - Invalid arguments
"""

__version__ = "0.1.0"

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

# ANSI escape sequence pattern
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        Text with ANSI codes removed
    """
    return ANSI_ESCAPE.sub('', text)


def normalize_newlines(text: str) -> str:
    """Convert CRLF to LF.

    Args:
        text: Text with potential CRLF line endings

    Returns:
        Text with only LF line endings
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces.

    Args:
        text: Text with potential multiple whitespace

    Returns:
        Text with whitespace collapsed
    """
    return re.sub(r'\s+', ' ', text)


def apply_replacements(text: str, replacements: list[tuple[str, str]]) -> str:
    """Apply regex replacements to text.

    Args:
        text: Input text
        replacements: List of (pattern, replacement) tuples

    Returns:
        Text with all replacements applied
    """
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    return text


def apply_redactions(text: str, patterns: list[str]) -> str:
    """Redact patterns from text.

    Args:
        text: Input text
        patterns: List of regex patterns to redact

    Returns:
        Text with patterns replaced by <redacted>
    """
    for pattern in patterns:
        text = re.sub(pattern, '<redacted>', text)
    return text


def preprocess(
    text: str,
    *,
    do_strip_ansi: bool = False,
    do_normalize_newlines: bool = False,
    do_trim: bool = False,
    do_collapse_whitespace: bool = False,
    do_ignore_case: bool = False,
    replacements: list[tuple[str, str]] | None = None,
    redactions: list[str] | None = None,
) -> str:
    """Apply all preprocessing steps to text.

    Args:
        text: Input text
        do_strip_ansi: Remove ANSI escape sequences
        do_normalize_newlines: Convert CRLF to LF
        do_trim: Strip leading/trailing whitespace
        do_collapse_whitespace: Collapse whitespace runs
        do_ignore_case: Convert to lowercase
        replacements: Regex replacements to apply
        redactions: Regex patterns to redact

    Returns:
        Preprocessed text
    """
    if do_strip_ansi:
        text = strip_ansi(text)
    if do_normalize_newlines:
        text = normalize_newlines(text)
    if replacements:
        text = apply_replacements(text, replacements)
    if redactions:
        text = apply_redactions(text, redactions)
    if do_trim:
        text = text.strip()
    if do_collapse_whitespace:
        text = collapse_whitespace(text)
    if do_ignore_case:
        text = text.lower()
    return text


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


def parse_jsonl(text: str) -> list[Any]:
    """Parse JSONL text into list of values.

    Args:
        text: JSONL string (one JSON value per line)

    Returns:
        List of parsed JSON values

    Raises:
        json.JSONDecodeError: If any line is not valid JSON
    """
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    return [json.loads(line) for line in lines]


def remove_json_paths(obj: Any, paths: list[str]) -> Any:
    """Remove paths from JSON object (returns new object).

    Args:
        obj: JSON-like object
        paths: List of paths to remove

    Returns:
        New object with paths removed
    """
    if not paths:
        return obj

    obj = json.loads(json.dumps(obj))  # Deep copy

    for path in paths:
        # Remove leading $ if present
        if path.startswith('$.'):
            path = path[2:]
        elif path.startswith('$'):
            path = path[1:]

        parts = re.split(r'\.|\[(\d+)\]', path)
        parts = [p for p in parts if p]

        if not parts:
            continue

        # Navigate to parent
        current = obj
        for part in parts[:-1]:
            if current is None:
                break
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    current = None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                current = None

        # Remove the final key
        if current is not None:
            final = parts[-1]
            if final.isdigit() and isinstance(current, list):
                idx = int(final)
                if 0 <= idx < len(current):
                    current.pop(idx)
            elif isinstance(current, dict) and final in current:
                del current[final]

    return obj


def unified_diff(actual: str, expected: str, context: int = 3) -> str:
    """Generate unified diff between actual and expected.

    Args:
        actual: Actual output
        expected: Expected output
        context: Number of context lines

    Returns:
        Unified diff string
    """
    actual_lines = actual.splitlines(keepends=True)
    expected_lines = expected.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile='expected',
        tofile='actual',
        n=context,
    )
    return ''.join(diff)


def colorize_diff(diff: str, use_color: bool) -> str:
    """Add ANSI colors to unified diff.

    Args:
        diff: Unified diff string
        use_color: Whether to add colors

    Returns:
        Colored diff string (or original if use_color is False)
    """
    if not use_color:
        return diff

    lines = []
    for line in diff.splitlines(keepends=True):
        if line.startswith('+++') or line.startswith('---'):
            lines.append(f'\033[1m{line}\033[0m')  # Bold
        elif line.startswith('+'):
            lines.append(f'\033[32m{line}\033[0m')  # Green
        elif line.startswith('-'):
            lines.append(f'\033[31m{line}\033[0m')  # Red
        elif line.startswith('@@'):
            lines.append(f'\033[36m{line}\033[0m')  # Cyan
        else:
            lines.append(line)
    return ''.join(lines)


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
    diff = unified_diff(actual, expected)
    return False, f"Exact match failed.\n\n{diff}"


def compare_contains(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual contains expected substring.

    Args:
        actual: Actual output from command
        expected: Expected substring

    Returns:
        Tuple of (success, error_message)
    """
    expected_stripped = expected.strip()
    if expected_stripped in actual:
        return True, ""

    # Show a relevant excerpt of actual
    excerpt = actual[:500] + ('...' if len(actual) > 500 else '')
    return False, f"Expected to contain:\n{expected_stripped}\n\nActual output:\n{excerpt}"


def compare_regex(actual: str, expected: str) -> tuple[bool, str]:
    """Check if actual matches regex pattern.

    Args:
        actual: Actual output from command
        expected: Regex pattern

    Returns:
        Tuple of (success, error_message)
    """
    try:
        pattern = re.compile(expected, re.MULTILINE | re.DOTALL)
    except re.error as e:
        return False, f"Invalid regex pattern: {e}"

    if pattern.search(actual):
        return True, ""
    return False, f"Regex not found:\n{expected}\n\nActual:\n{actual}"


def compare_json(
    actual: str, expected: str, ignore_paths: list[str] | None = None
) -> tuple[bool, str]:
    """Compare single JSON values semantically.

    Args:
        actual: Actual JSON output
        expected: Expected JSON string
        ignore_paths: JSON paths to ignore in comparison

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_obj = json.loads(actual.strip())
    except json.JSONDecodeError as e:
        return False, f"Actual is not valid JSON: {e}"

    try:
        expected_obj = json.loads(expected.strip())
    except json.JSONDecodeError as e:
        return False, f"Expected is not valid JSON: {e}"

    if ignore_paths:
        actual_obj = remove_json_paths(actual_obj, ignore_paths)
        expected_obj = remove_json_paths(expected_obj, ignore_paths)

    if normalize_json(actual_obj) == normalize_json(expected_obj):
        return True, ""

    return False, (
        f"JSON mismatch:\n"
        f"Expected: {json.dumps(expected_obj, indent=2)}\n"
        f"Actual: {json.dumps(actual_obj, indent=2)}"
    )


def compare_jsonl(
    actual: str,
    expected: str,
    ignore_paths: list[str] | None = None,
) -> tuple[bool, str]:
    """Compare JSONL output semantically.

    Record order matters, but field order within records does not.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL string
        ignore_paths: JSON paths to ignore in comparison

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [remove_json_paths(r, ignore_paths) for r in expected_records]

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


def compare_jsonl_set(
    actual: str,
    expected: str,
    ignore_paths: list[str] | None = None,
) -> tuple[bool, str]:
    """Compare JSONL output as unordered multiset.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL string
        ignore_paths: JSON paths to ignore in comparison

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [remove_json_paths(r, ignore_paths) for r in expected_records]

    # Normalize all records for comparison
    actual_normalized = [json.dumps(normalize_json(r), sort_keys=True) for r in actual_records]
    expected_normalized = [json.dumps(normalize_json(r), sort_keys=True) for r in expected_records]

    # Sort for multiset comparison
    actual_sorted = sorted(actual_normalized)
    expected_sorted = sorted(expected_normalized)

    if actual_sorted == expected_sorted:
        return True, ""

    # Find differences
    missing = []
    extra = []

    actual_counts: dict[str, int] = {}
    for r in actual_normalized:
        actual_counts[r] = actual_counts.get(r, 0) + 1

    expected_counts: dict[str, int] = {}
    for r in expected_normalized:
        expected_counts[r] = expected_counts.get(r, 0) + 1

    all_keys = set(actual_counts.keys()) | set(expected_counts.keys())
    for key in all_keys:
        act_count = actual_counts.get(key, 0)
        exp_count = expected_counts.get(key, 0)
        if act_count > exp_count:
            for _ in range(act_count - exp_count):
                extra.append(key)
        elif exp_count > act_count:
            for _ in range(exp_count - act_count):
                missing.append(key)

    msg_parts = ["JSONL set comparison failed:"]
    if missing:
        msg_parts.append(f"Missing {len(missing)} record(s):")
        for r in missing[:5]:  # Limit output
            msg_parts.append(f"  {r}")
        if len(missing) > 5:
            msg_parts.append(f"  ... and {len(missing) - 5} more")
    if extra:
        msg_parts.append(f"Extra {len(extra)} record(s):")
        for r in extra[:5]:
            msg_parts.append(f"  {r}")
        if len(extra) > 5:
            msg_parts.append(f"  ... and {len(extra) - 5} more")

    return False, '\n'.join(msg_parts)


def compare_jsonl_key(
    actual: str,
    expected: str,
    key_field: str,
    ignore_paths: list[str] | None = None,
) -> tuple[bool, str]:
    """Compare JSONL records by a key field.

    Records are matched by key field value, then compared.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL string
        key_field: Field to use as key for matching records
        ignore_paths: JSON paths to ignore in comparison

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = parse_jsonl(actual)
        expected_records = parse_jsonl(expected)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [remove_json_paths(r, ignore_paths) for r in expected_records]

    # Build dict by key
    actual_by_key: dict[Any, Any] = {}
    for r in actual_records:
        if isinstance(r, dict) and key_field in r:
            actual_by_key[r[key_field]] = r
        else:
            return False, f"Record missing key field '{key_field}': {json.dumps(r)}"

    expected_by_key: dict[Any, Any] = {}
    for r in expected_records:
        if isinstance(r, dict) and key_field in r:
            expected_by_key[r[key_field]] = r
        else:
            return False, f"Expected record missing key field '{key_field}': {json.dumps(r)}"

    # Check for missing and extra keys
    actual_keys = set(actual_by_key.keys())
    expected_keys = set(expected_by_key.keys())

    missing_keys = expected_keys - actual_keys
    extra_keys = actual_keys - expected_keys

    errors = []
    if missing_keys:
        errors.append(f"Missing keys: {sorted(missing_keys)}")
    if extra_keys:
        errors.append(f"Extra keys: {sorted(extra_keys)}")

    # Compare matching records
    for key in expected_keys & actual_keys:
        if normalize_json(actual_by_key[key]) != normalize_json(expected_by_key[key]):
            errors.append(
                f"Mismatch for key '{key}':\n"
                f"  Expected: {json.dumps(expected_by_key[key])}\n"
                f"  Actual: {json.dumps(actual_by_key[key])}"
            )

    if errors:
        return False, "JSONL key comparison failed:\n" + '\n'.join(errors)
    return True, ""


def compare_jsonl_contains(
    actual: str,
    expected: str,
    ignore_paths: list[str] | None = None,
) -> tuple[bool, str]:
    """Check if actual JSONL contains all expected records.

    Each expected record must match at least one actual record.
    Matching is done by checking all fields in expected exist in actual.

    Args:
        actual: Actual JSONL output
        expected: Expected JSONL records (subset)
        ignore_paths: JSON paths to ignore in comparison

    Returns:
        Tuple of (success, error_message)
    """
    try:
        actual_records = [normalize_json(r) for r in parse_jsonl(actual)]
        expected_records = [normalize_json(r) for r in parse_jsonl(expected)]
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if ignore_paths:
        actual_records = [remove_json_paths(r, ignore_paths) for r in actual_records]
        expected_records = [remove_json_paths(r, ignore_paths) for r in expected_records]

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

    # Expected value source
    parser.add_argument("expected", nargs="?", help="Expected output (or use -f for file)")
    parser.add_argument("-f", "--expected-file", metavar="FILE",
                        help="Read expected output from file")

    # Comparison modes (mutually exclusive group)
    mode_group = parser.add_argument_group("comparison modes")
    mode_group.add_argument("--contains", action="store_true",
                            help="Check substring containment")
    mode_group.add_argument("--regex", action="store_true",
                            help="Match against regex pattern")
    mode_group.add_argument("--json", action="store_true",
                            help="Compare as JSON (semantic, field order independent)")
    mode_group.add_argument("--jsonl", action="store_true",
                            help="Compare as JSONL (semantic, field order independent)")
    mode_group.add_argument("--jsonl-contains", action="store_true",
                            help="Check JSONL contains expected records")
    mode_group.add_argument("--jsonl-set", action="store_true",
                            help="Compare JSONL as unordered set")
    mode_group.add_argument("--jsonl-key", metavar="FIELD",
                            help="Compare JSONL records by key field")

    # Normalization options
    norm_group = parser.add_argument_group("normalization options")
    norm_group.add_argument("--strip-ansi", action="store_true",
                            help="Remove ANSI escape sequences (colors)")
    norm_group.add_argument("--normalize-newlines", action="store_true",
                            help="Convert CRLF to LF")
    norm_group.add_argument("--trim", action="store_true",
                            help="Strip leading/trailing whitespace")
    norm_group.add_argument("--collapse-whitespace", action="store_true",
                            help="Collapse runs of whitespace to single spaces")
    norm_group.add_argument("--ignore-case", "-i", action="store_true",
                            help="Case-insensitive comparison")

    # Pattern transformation
    transform_group = parser.add_argument_group("pattern transformation")
    transform_group.add_argument("--replace", nargs=2, action="append",
                                 metavar=("REGEX", "REPL"), default=[],
                                 help="Replace regex with string (repeatable)")
    transform_group.add_argument("--redact", action="append", metavar="REGEX", default=[],
                                 help="Replace regex with <redacted> (repeatable)")

    # JSON options
    json_group = parser.add_argument_group("JSON options")
    json_group.add_argument("--json-ignore", action="append", metavar="PATH", default=[],
                            help="Ignore JSON path (e.g., $.timestamp) (repeatable)")

    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument("--quiet", "-q", action="store_true",
                              help="Suppress diff output on failure")
    output_group.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                              help="Colorize output (default: auto)")
    output_group.add_argument("--diff-context", type=int, default=3, metavar="N",
                              help="Lines of context in diff (default: 3)")

    # Snapshot mode
    parser.add_argument("--update", action="store_true",
                        help="Update expected file on mismatch (requires -f)")

    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    parsed = parser.parse_args(args)

    # Read actual output from stdin
    actual = sys.stdin.read()

    # Get expected from argument or file
    if parsed.expected_file:
        try:
            expected = Path(parsed.expected_file).read_text()
        except FileNotFoundError:
            if parsed.update:
                # File doesn't exist yet, will create it
                expected = ""
            else:
                print(f"Error: expected file not found: {parsed.expected_file}", file=sys.stderr)
                return 2
        except OSError as e:
            print(f"Error reading expected file: {e}", file=sys.stderr)
            return 2
    elif parsed.expected is not None:
        expected = parsed.expected
    else:
        print("Error: expected value required (positional argument or -f FILE)", file=sys.stderr)
        return 2

    # Determine color usage
    use_color = parsed.color == "always" or (
        parsed.color == "auto" and sys.stderr.isatty()
    )

    # Apply preprocessing to both actual and expected
    preprocess_opts = {
        "do_strip_ansi": parsed.strip_ansi,
        "do_normalize_newlines": parsed.normalize_newlines,
        "do_trim": parsed.trim,
        "do_collapse_whitespace": parsed.collapse_whitespace,
        "do_ignore_case": parsed.ignore_case,
        "replacements": parsed.replace if parsed.replace else None,
        "redactions": parsed.redact if parsed.redact else None,
    }

    actual_processed = preprocess(actual, **preprocess_opts)
    expected_processed = preprocess(expected, **preprocess_opts)

    # Collect JSON ignore paths
    json_ignore = parsed.json_ignore if parsed.json_ignore else None

    # Choose comparison mode
    if parsed.jsonl_key:
        ok, msg = compare_jsonl_key(
            actual_processed, expected_processed, parsed.jsonl_key, json_ignore
        )
    elif parsed.jsonl_set:
        ok, msg = compare_jsonl_set(actual_processed, expected_processed, json_ignore)
    elif parsed.jsonl_contains:
        ok, msg = compare_jsonl_contains(actual_processed, expected_processed, json_ignore)
    elif parsed.jsonl:
        ok, msg = compare_jsonl(actual_processed, expected_processed, json_ignore)
    elif parsed.json:
        ok, msg = compare_json(actual_processed, expected_processed, json_ignore)
    elif parsed.regex:
        ok, msg = compare_regex(actual_processed, expected_processed)
    elif parsed.contains:
        ok, msg = compare_contains(actual_processed, expected_processed)
    else:
        ok, msg = compare_exact(actual_processed, expected_processed)

    if ok:
        return 0
    else:
        # Handle --update mode
        if parsed.update and parsed.expected_file:
            try:
                # Write actual output (with preprocessing applied) to expected file
                Path(parsed.expected_file).write_text(actual)
                print(f"Updated: {parsed.expected_file}", file=sys.stderr)
                return 0
            except OSError as e:
                print(f"Error writing expected file: {e}", file=sys.stderr)
                return 2

        if not parsed.quiet:
            # Colorize if applicable
            if use_color and "diff" not in msg.lower():
                # For non-diff output, just use red for "FAIL:"
                print(f"\033[31mFAIL:\033[0m {msg}", file=sys.stderr)
            elif use_color:
                msg = colorize_diff(msg, use_color)
                print(f"FAIL: {msg}", file=sys.stderr)
            else:
                print(f"FAIL: {msg}", file=sys.stderr)
        return 1


def cli() -> None:
    """CLI entry point that exits with the return code."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
