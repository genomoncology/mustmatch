"""Tests for doctest-expect CLI tool.

These tests verify the expect command works correctly for all comparison modes.
"""

import tempfile
from pathlib import Path

from doctest_expect import main


def run_expect(stdin: str, args: list[str]) -> tuple[int, str, str]:
    """Run expect command and return (exit_code, stdout, stderr).

    Uses the main() function directly with captured stdin/stdout/stderr
    for more reliable testing across different environments.
    """
    import io
    import sys

    # Capture stdin
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin)

    # Capture stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        exit_code = main(args)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 0
    finally:
        stdout_val = sys.stdout.getvalue()
        stderr_val = sys.stderr.getvalue()
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return exit_code, stdout_val, stderr_val


class TestExactMatch:
    """Tests for exact string matching (default mode)."""

    def test_exact_match_success(self):
        """Exact match should return 0 on match."""
        code, _, _ = run_expect("hello world", ["hello world"])
        assert code == 0

    def test_exact_match_with_newline(self):
        """Trailing newlines should be normalized."""
        code, _, _ = run_expect("hello world\n", ["hello world"])
        assert code == 0

    def test_exact_match_failure(self):
        """Exact match should return 1 on mismatch."""
        code, _, stderr = run_expect("hello world", ["goodbye world"])
        assert code == 1
        assert "FAIL" in stderr

    def test_exact_match_multiline(self):
        """Multi-line exact match should work."""
        code, _, _ = run_expect("line one\nline two", ["line one\nline two"])
        assert code == 0

    def test_exact_match_shows_diff(self):
        """Exact match failure should show unified diff."""
        code, _, stderr = run_expect("hello world", ["hello moon"])
        assert code == 1
        assert "---" in stderr or "expected" in stderr.lower()


class TestContainsMatch:
    """Tests for substring matching (--contains mode)."""

    def test_contains_success(self):
        """Contains should return 0 when substring present."""
        code, _, _ = run_expect("hello world", ["--contains", "world"])
        assert code == 0

    def test_contains_failure(self):
        """Contains should return 1 when substring absent."""
        code, _, stderr = run_expect("hello world", ["--contains", "goodbye"])
        assert code == 1
        assert "FAIL" in stderr

    def test_contains_case_sensitive(self):
        """Contains should be case sensitive by default."""
        code, _, _ = run_expect("Hello World", ["--contains", "hello"])
        assert code == 1


class TestRegexMatch:
    """Tests for regex matching (--regex mode)."""

    def test_regex_success(self):
        """Regex should match valid pattern."""
        code, _, _ = run_expect("finished in 1.23s", ["--regex", r"finished in \d+\.\d+s"])
        assert code == 0

    def test_regex_failure(self):
        """Regex should fail when pattern not found."""
        code, _, stderr = run_expect("completed", ["--regex", r"finished in \d+s"])
        assert code == 1
        assert "FAIL" in stderr

    def test_regex_multiline(self):
        """Regex should work across multiple lines."""
        code, _, _ = run_expect("line1\nline2\nline3", ["--regex", r"line1.*line3"])
        assert code == 0

    def test_regex_invalid_pattern(self):
        """Invalid regex should return error."""
        code, _, stderr = run_expect("test", ["--regex", r"[invalid"])
        assert code == 1
        assert "Invalid regex" in stderr


class TestJsonMatch:
    """Tests for JSON semantic matching (--json mode)."""

    def test_json_exact_match(self):
        """JSON should match identical objects."""
        code, _, _ = run_expect(
            '{"name": "alice", "age": 30}',
            ["--json", '{"name": "alice", "age": 30}'],
        )
        assert code == 0

    def test_json_field_order_independent(self):
        """JSON should match regardless of field order."""
        code, _, _ = run_expect(
            '{"name": "alice", "age": 30}',
            ["--json", '{"age": 30, "name": "alice"}'],
        )
        assert code == 0

    def test_json_nested_objects(self):
        """JSON should handle nested objects."""
        code, _, _ = run_expect(
            '{"user": {"name": "alice", "age": 30}}',
            ["--json", '{"user": {"age": 30, "name": "alice"}}'],
        )
        assert code == 0

    def test_json_arrays(self):
        """JSON should handle arrays."""
        code, _, _ = run_expect(
            '[1, 2, 3]',
            ["--json", '[1, 2, 3]'],
        )
        assert code == 0

    def test_json_invalid_actual(self):
        """Invalid actual JSON should fail gracefully."""
        code, _, stderr = run_expect(
            "not json",
            ["--json", '{"id": 1}'],
        )
        assert code == 1
        assert "not valid JSON" in stderr

    def test_json_mismatch(self):
        """JSON mismatch should show clear error."""
        code, _, stderr = run_expect(
            '{"name": "alice"}',
            ["--json", '{"name": "bob"}'],
        )
        assert code == 1
        assert "mismatch" in stderr.lower()


class TestJsonlMatch:
    """Tests for JSONL semantic matching (--jsonl mode)."""

    def test_jsonl_exact_match(self):
        """JSONL should match identical records."""
        code, _, _ = run_expect(
            '{"name": "alice", "age": 30}',
            ["--jsonl", '{"name": "alice", "age": 30}'],
        )
        assert code == 0

    def test_jsonl_field_order_independent(self):
        """JSONL should match regardless of field order."""
        code, _, _ = run_expect(
            '{"name": "alice", "age": 30}',
            ["--jsonl", '{"age": 30, "name": "alice"}'],
        )
        assert code == 0

    def test_jsonl_multiple_records(self):
        """JSONL should match multiple records in order."""
        code, _, _ = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl", '{"id": 1}\n{"id": 2}'],
        )
        assert code == 0

    def test_jsonl_record_order_matters(self):
        """JSONL record order should matter."""
        code, _, _ = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl", '{"id": 2}\n{"id": 1}'],
        )
        assert code == 1

    def test_jsonl_count_mismatch(self):
        """JSONL should fail when record counts differ."""
        code, _, stderr = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl", '{"id": 1}'],
        )
        assert code == 1
        assert "count mismatch" in stderr.lower()

    def test_jsonl_nested_objects(self):
        """JSONL should handle nested objects."""
        code, _, _ = run_expect(
            '{"user": {"name": "alice", "age": 30}}',
            ["--jsonl", '{"user": {"age": 30, "name": "alice"}}'],
        )
        assert code == 0

    def test_jsonl_invalid_json(self):
        """JSONL should fail gracefully on invalid JSON."""
        code, _, stderr = run_expect(
            "not json",
            ["--jsonl", '{"id": 1}'],
        )
        assert code == 1
        assert "JSON parse error" in stderr


class TestJsonlSetMatch:
    """Tests for JSONL set matching (--jsonl-set mode)."""

    def test_jsonl_set_order_independent(self):
        """JSONL set should match regardless of order."""
        code, _, _ = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl-set", '{"id": 2}\n{"id": 1}'],
        )
        assert code == 0

    def test_jsonl_set_duplicate_handling(self):
        """JSONL set should handle duplicates correctly."""
        code, _, _ = run_expect(
            '{"id": 1}\n{"id": 1}',
            ["--jsonl-set", '{"id": 1}\n{"id": 1}'],
        )
        assert code == 0

    def test_jsonl_set_missing_record(self):
        """JSONL set should fail when record missing."""
        code, _, stderr = run_expect(
            '{"id": 1}',
            ["--jsonl-set", '{"id": 1}\n{"id": 2}'],
        )
        assert code == 1
        assert "Missing" in stderr

    def test_jsonl_set_extra_record(self):
        """JSONL set should fail when extra record present."""
        code, _, stderr = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl-set", '{"id": 1}'],
        )
        assert code == 1
        assert "Extra" in stderr


class TestJsonlKeyMatch:
    """Tests for JSONL key-based matching (--jsonl-key mode)."""

    def test_jsonl_key_order_independent(self):
        """JSONL key should match by key field."""
        code, _, _ = run_expect(
            '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}',
            ["--jsonl-key", "id", '{"id": 2, "name": "bob"}\n{"id": 1, "name": "alice"}'],
        )
        assert code == 0

    def test_jsonl_key_missing_key_field(self):
        """JSONL key should fail when key field missing."""
        code, _, stderr = run_expect(
            '{"name": "alice"}',
            ["--jsonl-key", "id", '{"id": 1}'],
        )
        assert code == 1
        assert "missing key field" in stderr.lower()

    def test_jsonl_key_mismatch(self):
        """JSONL key should detect value mismatch."""
        code, _, stderr = run_expect(
            '{"id": 1, "name": "alice"}',
            ["--jsonl-key", "id", '{"id": 1, "name": "bob"}'],
        )
        assert code == 1
        assert "Mismatch" in stderr


class TestJsonlContainsMatch:
    """Tests for JSONL subset matching (--jsonl-contains mode)."""

    def test_jsonl_contains_single_record(self):
        """JSONL contains should find matching record."""
        code, _, _ = run_expect(
            '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}',
            ["--jsonl-contains", '{"id": 1}'],
        )
        assert code == 0

    def test_jsonl_contains_multiple_expected(self):
        """JSONL contains should find all expected records."""
        code, _, _ = run_expect(
            '{"id": 1}\n{"id": 2}\n{"id": 3}',
            ["--jsonl-contains", '{"id": 1}\n{"id": 3}'],
        )
        assert code == 0

    def test_jsonl_contains_missing_record(self):
        """JSONL contains should fail when expected record missing."""
        code, _, stderr = run_expect(
            '{"id": 1}\n{"id": 2}',
            ["--jsonl-contains", '{"id": 999}'],
        )
        assert code == 1
        assert "Missing" in stderr

    def test_jsonl_contains_partial_match(self):
        """JSONL contains should match on subset of fields."""
        code, _, _ = run_expect(
            '{"id": 1, "name": "alice", "age": 30}',
            ["--jsonl-contains", '{"name": "alice"}'],
        )
        assert code == 0


class TestJsonIgnore:
    """Tests for JSON path ignore (--json-ignore)."""

    def test_json_ignore_field(self):
        """JSON ignore should ignore specified field."""
        code, _, _ = run_expect(
            '{"id": 1, "timestamp": "2024-01-01"}',
            ["--json", "--json-ignore", "$.timestamp", '{"id": 1, "timestamp": "ignored"}'],
        )
        assert code == 0

    def test_json_ignore_nested(self):
        """JSON ignore should work with nested paths."""
        code, _, _ = run_expect(
            '{"user": {"name": "alice", "created_at": "2024-01-01"}}',
            ["--json", "--json-ignore", "$.user.created_at", '{"user": {"name": "alice"}}'],
        )
        assert code == 0

    def test_json_ignore_multiple(self):
        """Multiple JSON ignore paths should work."""
        code, _, _ = run_expect(
            '{"id": 1, "ts": "x", "hash": "y"}',
            ["--json", "--json-ignore", "$.ts", "--json-ignore", "$.hash", '{"id": 1}'],
        )
        assert code == 0

    def test_jsonl_ignore_field(self):
        """JSONL ignore should work with JSONL mode."""
        code, _, _ = run_expect(
            '{"id": 1, "ts": "x"}',
            ["--jsonl", "--json-ignore", "$.ts", '{"id": 1}'],
        )
        assert code == 0


class TestNormalization:
    """Tests for normalization options."""

    def test_strip_ansi(self):
        """Strip ANSI should remove color codes."""
        code, _, _ = run_expect(
            "\033[31mred\033[0m",
            ["--strip-ansi", "red"],
        )
        assert code == 0

    def test_normalize_newlines(self):
        """Normalize newlines should convert CRLF to LF."""
        code, _, _ = run_expect(
            "line1\r\nline2",
            ["--normalize-newlines", "line1\nline2"],
        )
        assert code == 0

    def test_trim(self):
        """Trim should strip leading/trailing whitespace."""
        code, _, _ = run_expect(
            "  hello world  \n",
            ["--trim", "hello world"],
        )
        assert code == 0

    def test_collapse_whitespace(self):
        """Collapse whitespace should merge spaces."""
        code, _, _ = run_expect(
            "hello    world\n\nfoo",
            ["--collapse-whitespace", "hello world foo"],
        )
        assert code == 0

    def test_ignore_case(self):
        """Ignore case should match case-insensitively."""
        code, _, _ = run_expect(
            "Hello World",
            ["--ignore-case", "hello world"],
        )
        assert code == 0

    def test_ignore_case_short_flag(self):
        """Short -i flag should work."""
        code, _, _ = run_expect(
            "HELLO",
            ["-i", "hello"],
        )
        assert code == 0

    def test_combined_normalization(self):
        """Multiple normalization flags should work together."""
        code, _, _ = run_expect(
            "\033[32m  HELLO   WORLD  \033[0m",
            ["--strip-ansi", "--trim", "--collapse-whitespace", "--ignore-case", "hello world"],
        )
        assert code == 0


class TestPatternTransformation:
    """Tests for pattern transformation (--replace, --redact)."""

    def test_replace_basic(self):
        """Replace should substitute patterns."""
        code, _, _ = run_expect(
            "finished in 1.23s",
            ["--replace", r"\d+\.\d+s", "<time>", "finished in <time>"],
        )
        assert code == 0

    def test_replace_multiple(self):
        """Multiple replacements should work."""
        code, _, _ = run_expect(
            "user: alice, id: 12345",
            [
                "--replace", r"\d+", "<id>",
                "--replace", r"alice", "<user>",
                "user: <user>, id: <id>",
            ],
        )
        assert code == 0

    def test_redact(self):
        """Redact should replace with <redacted>."""
        code, _, _ = run_expect(
            "token: abc123xyz",
            ["--redact", r"abc\w+xyz", "token: <redacted>"],
        )
        assert code == 0

    def test_redact_multiple(self):
        """Multiple redactions should work."""
        code, _, _ = run_expect(
            "key=secret1 pass=secret2",
            ["--redact", r"secret\d", "key=<redacted> pass=<redacted>"],
        )
        assert code == 0


class TestExpectedFile:
    """Tests for expected file input (-f/--expected-file)."""

    def test_expected_file_success(self):
        """Expected file should work for matching."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello world")
            f.flush()
            code, _, _ = run_expect("hello world", ["-f", f.name])
            assert code == 0
            Path(f.name).unlink()

    def test_expected_file_failure(self):
        """Expected file mismatch should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("expected")
            f.flush()
            code, _, stderr = run_expect("actual", ["-f", f.name])
            assert code == 1
            assert "FAIL" in stderr
            Path(f.name).unlink()

    def test_expected_file_not_found(self):
        """Missing expected file should return error."""
        code, _, stderr = run_expect("test", ["-f", "/nonexistent/path.txt"])
        assert code == 2
        assert "not found" in stderr.lower()

    def test_expected_file_long_flag(self):
        """Long --expected-file flag should work."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            f.flush()
            code, _, _ = run_expect("test", ["--expected-file", f.name])
            assert code == 0
            Path(f.name).unlink()


class TestUpdateMode:
    """Tests for update/snapshot mode (--update)."""

    def test_update_creates_file(self):
        """Update mode should create expected file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "expected.txt"
            code, _, stderr = run_expect("new content", ["-f", str(filepath), "--update"])
            assert code == 0
            assert "Updated" in stderr
            assert filepath.read_text() == "new content"

    def test_update_overwrites_file(self):
        """Update mode should overwrite existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("old content")
            f.flush()
            code, _, stderr = run_expect("new content", ["-f", f.name, "--update"])
            assert code == 0
            assert Path(f.name).read_text() == "new content"
            Path(f.name).unlink()


class TestColorOutput:
    """Tests for color output options."""

    def test_color_never(self):
        """Color never should not include ANSI codes."""
        code, _, stderr = run_expect("hello", ["--color", "never", "world"])
        assert code == 1
        assert "\033[" not in stderr

    def test_color_always(self):
        """Color always should include ANSI codes."""
        code, _, stderr = run_expect("hello", ["--color", "always", "world"])
        assert code == 1
        assert "\033[" in stderr


class TestQuietMode:
    """Tests for quiet mode (-q/--quiet)."""

    def test_quiet_suppresses_output(self):
        """Quiet mode should suppress error messages."""
        code, _, stderr = run_expect("hello", ["--quiet", "goodbye"])
        assert code == 1
        assert stderr == ""

    def test_quiet_short_flag(self):
        """Short -q flag should work."""
        code, _, stderr = run_expect("hello", ["-q", "goodbye"])
        assert code == 1
        assert stderr == ""


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_expected_value(self):
        """Should return error code 2 when expected value missing."""
        code, _, stderr = run_expect("hello", [])
        assert code == 2
        assert "expected value required" in stderr.lower()

    def test_expected_file_or_argument(self):
        """Should accept either file or argument."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            f.flush()
            # File takes precedence
            code, _, _ = run_expect("test", ["-f", f.name])
            assert code == 0
            Path(f.name).unlink()


class TestVersion:
    """Tests for version flag."""

    def test_version_flag(self):
        """--version should print version and exit."""
        import io
        import sys

        from doctest_expect import __version__

        # Verify version string is correct
        assert __version__ == "0.1.0"

        # Test that --version flag works
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            main(["--version"])
        except SystemExit as e:
            assert e.code == 0
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        assert "0.1.0" in output


class TestContainsWithNormalization:
    """Tests for contains mode with normalization."""

    def test_contains_ignore_case(self):
        """Contains with ignore-case should work."""
        code, _, _ = run_expect("Hello World", ["--contains", "--ignore-case", "hello"])
        assert code == 0

    def test_contains_strip_ansi(self):
        """Contains with strip-ansi should work."""
        code, _, _ = run_expect(
            "\033[32mSuccess\033[0m",
            ["--contains", "--strip-ansi", "Success"],
        )
        assert code == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_input(self):
        """Empty input should work."""
        code, _, _ = run_expect("", [""])
        assert code == 0

    def test_empty_expected(self):
        """Empty expected should match empty input."""
        code, _, _ = run_expect("", [""])
        assert code == 0

    def test_unicode_content(self):
        """Unicode content should work."""
        code, _, _ = run_expect("Hello 世界 🌍", ["Hello 世界 🌍"])
        assert code == 0

    def test_special_characters(self):
        """Special characters should work."""
        code, _, _ = run_expect('{"key": "value"}', ['{"key": "value"}'])
        assert code == 0

    def test_large_output(self):
        """Large output should be handled."""
        large = "x" * 10000
        code, _, _ = run_expect(large, [large])
        assert code == 0
