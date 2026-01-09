"""Minimal tests for code paths that can't be covered by documentation tests.

These tests exist because:
1. Subprocess execution (doc tests run outmatch as subprocess, can't measure coverage)
2. Terminal-dependent behavior (colors, TTY detection)
3. Error conditions that would break doc test execution
4. Internal methods not exposed via CLI

Goal: Keep this file as small as possible. If a feature CAN be tested via
docs, it SHOULD be tested via docs instead.
"""

from pathlib import Path

import pytest

from outmatch.cli import main
from outmatch.config import ColorMode, CompareResult, ExpectConfig
from outmatch.json_utils import _navigate, _remove_single_path
from outmatch.output import colorize_diff, format_error
from outmatch.pytest import MarkdownTest


class TestMarkdownTestInternals:
    """Tests for MarkdownTest methods not reachable via CLI subprocess."""

    def test_repr(self, tmp_path: Path) -> None:
        """Test __repr__ - line 31.

        Can't test via CLI because repr() is only called when debugging/printing
        test objects, not during normal test execution.
        """
        test = MarkdownTest(tmp_path / "test.md", 10, "echo hi", "My Test")
        result = repr(test)
        assert "test.md" in result
        assert "10" in result
        assert "My Test" in result

    def test_html_comment_name(self, tmp_path: Path) -> None:
        """Test HTML comment name extraction - line 78.

        Can't test via CLI because we'd need a doc that uses HTML comments
        for naming, and the name is only used in error output.
        """
        md = tmp_path / "test.md"
        md.write_text("<!-- custom name -->\n```bash\necho hi\n```\n")
        tests = list(MarkdownTest._parse_file(md))
        assert tests[0].name == "custom name"

    def test_run_with_env(self, tmp_path: Path) -> None:
        """Test env dict handling - line 92.

        Can't test via CLI because env vars are passed via pytest fixtures,
        not CLI arguments in our doc tests.
        """
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$MY_VAR" = "hello"\n```\n')
        tests = list(MarkdownTest._parse_file(md))
        tests[0].run(env={"MY_VAR": "hello"})  # Should not raise

    def test_timeout_error(self, tmp_path: Path) -> None:
        """Test timeout handling - lines 103-107.

        Can't test via CLI because timeouts would make doc tests too slow.
        This verifies the TimeoutError message format.
        """
        md = tmp_path / "test.md"
        md.write_text("```bash\nsleep 10\n```\n")
        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(TimeoutError) as exc:
            tests[0].run(timeout=0.01)

        assert "timed out" in str(exc.value)

    def test_error_formatting(self, tmp_path: Path) -> None:
        """Test error message formatting - lines 110-117.

        Can't test via CLI because errors terminate the subprocess with
        exit code 1, we can only check stderr contains "FAIL".
        """
        md = tmp_path / "test.md"
        md.write_text("```bash\necho stdout; echo stderr >&2; exit 1\n```\n")
        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(AssertionError) as exc:
            tests[0].run()

        msg = str(exc.value)
        assert "Stdout:" in msg
        assert "Stderr:" in msg
        assert "Exit code: 1" in msg

    def test_indent_helper(self) -> None:
        """Test _indent static method - line 122.

        Internal helper, not exposed via CLI.
        """
        result = MarkdownTest._indent("line1\nline2")
        assert result == "  line1\n  line2"


class TestOutputColorization:
    """Tests for terminal color output that can't be tested via subprocess."""

    def test_colorize_diff_additions(self) -> None:
        """Test green colorization for '+' lines - line 31.

        Can't test via CLI because:
        1. Subprocess output doesn't preserve ANSI codes in our test capture
        2. Color is only applied when stderr.isatty() or --color=always
        """
        diff = "--- expected\n+++ actual\n@@ -1 +1 @@\n-old\n+new\n"
        result = colorize_diff(diff)
        # Green escape code for the +new line
        assert "\033[32m+new" in result

    def test_format_error_without_diff(self) -> None:
        """Test red FAIL prefix when message has no diff - line 59.

        Can't test via CLI because subprocess captures don't preserve
        ANSI codes, and this specific branch needs color=ALWAYS with
        a message that doesn't contain '---'.
        """
        result = CompareResult(success=False, message="simple error")
        config = ExpectConfig(color=ColorMode.ALWAYS)
        output = format_error(result, config)
        # Red escape code for FAIL:
        assert "\033[31mFAIL:\033[0m" in output


class TestOutmatchTestCommand:
    """Tests for the 'outmatch test' subcommand - lines 315-387 in cli.py.

    Can't test via doc tests because:
    1. Doc tests ARE the tests, running 'outmatch test' on docs would be circular
    2. The test command is an alternative to pytest, not used within pytest
    """

    def test_basic_pass(self, tmp_path: Path, monkeypatch) -> None:
        """Test outmatch test runs markdown tests - covers _run_mdtest."""
        md = tmp_path / "test.md"
        md.write_text("# Test\n\n```bash\necho hello\n```\n")
        monkeypatch.chdir(tmp_path)

        result = main(["test", str(md)])
        assert result == 0

    def test_failing_test(self, tmp_path: Path, monkeypatch) -> None:
        """Test outmatch test reports failures."""
        md = tmp_path / "test.md"
        md.write_text("# Test\n\n```bash\nexit 1\n```\n")
        monkeypatch.chdir(tmp_path)

        result = main(["test", str(md)])
        assert result == 1

    def test_quiet_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test outmatch test --quiet."""
        md = tmp_path / "test.md"
        md.write_text("# Test\n\n```bash\necho hi\n```\n")
        monkeypatch.chdir(tmp_path)

        result = main(["test", "-q", str(md)])
        assert result == 0

    def test_verbose_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test outmatch test --verbose."""
        md = tmp_path / "test.md"
        md.write_text("# Test\n\n```bash\necho hi\n```\n")
        monkeypatch.chdir(tmp_path)

        result = main(["test", "-v", str(md)])
        assert result == 0


class TestJsonPathEdgeCases:
    """Tests for JSON path navigation edge cases."""

    def test_empty_path(self) -> None:
        """Test handling of empty/invalid path - line 47.

        Can't test via CLI because we validate paths before calling
        remove_json_paths. This tests the defensive code.
        """
        obj = {"a": 1}
        _remove_single_path(obj, "$")  # Path becomes empty after stripping $
        assert obj == {"a": 1}  # Object unchanged

    def test_navigate_into_nonexistent(self) -> None:
        """Test navigation when parent doesn't exist - line 58.

        Can't easily test via CLI because --json-ignore with non-existent
        deep paths just silently succeeds.
        """
        obj = {"a": 1}
        _remove_single_path(obj, "$.x.y.z")  # x doesn't exist
        assert obj == {"a": 1}  # Object unchanged

    def test_navigate_list_index(self) -> None:
        """Test list index navigation - lines 72-75.

        This tests _navigate with numeric index into a list.
        """
        result = _navigate([1, 2, 3], "1")
        assert result == 2

    def test_navigate_into_non_dict(self) -> None:
        """Test navigation into non-dict/non-list - line 78.

        Tests the final return None when obj is neither dict nor list.
        """
        result = _navigate("string", "key")
        assert result is None
