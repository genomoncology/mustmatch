"""Tests for doctest-expect CLI tool.

These tests verify the expect command works correctly for all comparison modes.
"""

import subprocess
import sys


def run_expect(stdin: str, args: list[str]) -> tuple[int, str, str]:
    """Run expect command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "doctest_expect"] + args,
        input=stdin,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


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
        """Contains should be case sensitive."""
        code, _, _ = run_expect("Hello World", ["--contains", "hello"])
        assert code == 1


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


class TestVersion:
    """Tests for version flag."""

    def test_version_flag(self):
        """--version should print version and exit."""
        result = subprocess.run(
            [sys.executable, "-m", "doctest_expect", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout
