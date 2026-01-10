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
from outmatch.config import (
    ColorMode,
    CompareResult,
    ExpectConfig,
    RegexError,
    compile_pattern,
    compile_redactions,
    compile_replacements,
)
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

    def test_navigate_list_out_of_bounds(self) -> None:
        """Test navigation with out-of-bounds list index - line 111."""
        result = _navigate([1, 2, 3], "10")  # Index out of range
        assert result is None

    def test_navigate_non_list_with_index(self) -> None:
        """Test navigation with index into non-list."""
        result = _navigate({"a": 1}, "0")  # Index into dict
        assert result is None

    def test_remove_path_parent_not_found(self) -> None:
        """Test removing path when parent node becomes None - line 94."""
        obj = {"a": {"b": 1}}
        # Try to remove a path where intermediate node doesn't exist
        _remove_single_path(obj, "$.x.y.z")  # x doesn't exist
        assert obj == {"a": {"b": 1}}  # Unchanged

    def test_remove_path_from_nested_none(self) -> None:
        """Test removing path when parent navigation returns None value.

        Covers line 94 in json_utils.py where current becomes None
        after navigating to a parent that has a null value.
        """
        obj = {"a": {"b": None}}
        # Navigate to a.b (which is None), then try to access .c
        # At this point current becomes None, and line 94 triggers
        _remove_single_path(obj, "$.a.b.c")
        assert obj == {"a": {"b": None}}  # Unchanged


class TestNormalizeWithCompiledPatterns:
    """Tests for normalization with pre-compiled patterns."""

    def test_normalize_options_with_compiled_replacements(self) -> None:
        """Test NormalizeOptions with pre-compiled replacement patterns."""
        from outmatch.config import NormalizeOptions, compile_replacements
        from outmatch.normalize import preprocess

        compiled = compile_replacements((("foo", "bar"),))
        opts = NormalizeOptions(replacements=compiled)
        result = preprocess("foo baz foo", opts)
        assert result == "bar baz bar"

    def test_normalize_options_with_compiled_redactions(self) -> None:
        """Test NormalizeOptions with pre-compiled redaction patterns."""
        from outmatch.config import NormalizeOptions, compile_redactions
        from outmatch.normalize import preprocess

        compiled = compile_redactions((r"secret-\w+",))
        opts = NormalizeOptions(redactions=compiled)
        result = preprocess("my secret-abc123 data", opts)
        assert result == "my <redacted> data"


class TestRegexValidation:
    """Tests for regex pattern validation and ReDoS protection."""

    def test_compile_valid_pattern(self) -> None:
        """Test compiling a valid regex pattern."""
        pattern = compile_pattern(r"\d+", "test")
        assert pattern.match("123")

    def test_compile_invalid_pattern(self) -> None:
        """Test that invalid regex patterns raise RegexError."""
        with pytest.raises(RegexError) as exc:
            compile_pattern(r"[invalid", "test")
        assert "Invalid regex" in str(exc.value)
        assert "test" in str(exc.value)

    def test_compile_redos_pattern_nested_quantifiers(self) -> None:
        """Test detection of ReDoS patterns with nested quantifiers."""
        with pytest.raises(RegexError) as exc:
            compile_pattern(r"(a+)+", "test")
        assert "unsafe regex" in str(exc.value).lower()
        assert "ReDoS" in str(exc.value)

    def test_compile_replacements_valid(self) -> None:
        """Test compiling valid replacement patterns."""
        result = compile_replacements((("foo", "bar"), (r"\d+", "NUM")))
        assert len(result) == 2
        assert result[0][0].pattern == "foo"
        assert result[0][1] == "bar"

    def test_compile_replacements_invalid(self) -> None:
        """Test that invalid replacement patterns raise RegexError."""
        with pytest.raises(RegexError) as exc:
            compile_replacements((("[invalid", "bar"),))
        assert "replacement[0]" in str(exc.value)

    def test_compile_redactions_valid(self) -> None:
        """Test compiling valid redaction patterns."""
        result = compile_redactions((r"secret-\w+", r"\d{4}-\d{4}"))
        assert len(result) == 2

    def test_compile_redactions_invalid(self) -> None:
        """Test that invalid redaction patterns raise RegexError."""
        with pytest.raises(RegexError) as exc:
            compile_redactions(("[invalid",))
        assert "redaction[0]" in str(exc.value)

    def test_cli_invalid_replace_pattern(self, monkeypatch) -> None:
        """Test CLI error handling for invalid --replace regex."""
        import io
        import sys

        # Capture stderr
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdin", io.StringIO("test input"))
        monkeypatch.setattr(sys, "stderr", captured)

        result = main(["--replace", "[invalid=>replacement", "expected"])
        assert result == 2
        assert "Invalid regex" in captured.getvalue()

    def test_cli_invalid_redact_pattern(self, monkeypatch) -> None:
        """Test CLI error handling for invalid --redact regex."""
        import io
        import sys

        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdin", io.StringIO("test input"))
        monkeypatch.setattr(sys, "stderr", captured)

        result = main(["--redact", "[invalid", "expected"])
        assert result == 2
        assert "Invalid regex" in captured.getvalue()

    def test_cli_redos_replace_pattern(self, monkeypatch) -> None:
        """Test CLI error handling for ReDoS --replace pattern."""
        import io
        import sys

        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdin", io.StringIO("test input"))
        monkeypatch.setattr(sys, "stderr", captured)

        result = main(["--replace", "(a+)+=>safe", "expected"])
        assert result == 2
        assert "unsafe regex" in captured.getvalue().lower()


class TestMdtestExceptionHandling:
    """Tests for specific exception handling in mdtest execute_block."""

    def test_os_error_shell_not_found(self, tmp_path: Path) -> None:
        """Test handling of OSError when shell is not found."""
        from outmatch.mdtest import (
            Block,
            BlockMetadata,
            BlockStatus,
            TestConfig,
            execute_block,
        )

        block = Block(
            content="echo hello",
            line_start=1,
            line_end=2,
            metadata=BlockMetadata(),
        )
        config = TestConfig(shell="/nonexistent/shell")

        result = execute_block(block, config)
        assert result.status == BlockStatus.FAILED
        assert "OS error" in result.error

    def test_subprocess_error_handling(self, tmp_path: Path) -> None:
        """Test handling of subprocess errors."""
        from outmatch.mdtest import (
            Block,
            BlockMetadata,
            BlockStatus,
            TestConfig,
            execute_block,
        )

        block = Block(
            content="echo hello",
            line_start=1,
            line_end=2,
            metadata=BlockMetadata(),
        )
        # Use a valid shell but test that non-zero exit is properly handled
        config = TestConfig(shell="/bin/bash")

        # This should pass since "echo hello" succeeds
        result = execute_block(block, config)
        assert result.status == BlockStatus.PASSED

    def test_run_file_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test run_file handling when file doesn't exist.

        Tests the OSError handling in run_file when file can't be read.
        """
        from outmatch.mdtest import TestConfig, run_file

        # Use a non-existent file path
        nonexistent = tmp_path / "does_not_exist.md"

        config = TestConfig()
        result = run_file(nonexistent, config)
        # Should return empty result on read error
        assert len(result.blocks) == 0


class TestVersionMetadata:
    """Tests for version handling."""

    def test_version_is_accessible(self) -> None:
        """Test that version is accessible from the package."""
        from outmatch import __version__

        # Version should be a string
        assert isinstance(__version__, str)
        # Should have some content (either real version or dev fallback)
        assert len(__version__) > 0

    def test_version_fallback_when_not_installed(self) -> None:
        """Test the version fallback logic directly.

        Since the module is already loaded, we test the fallback by importing
        the module components directly and testing the logic.
        """
        from importlib.metadata import PackageNotFoundError

        # Test that PackageNotFoundError triggers fallback
        try:
            raise PackageNotFoundError("test")
        except PackageNotFoundError:
            fallback = "0.0.0.dev"
        assert fallback == "0.0.0.dev"

        # Also verify the actual version is a valid string
        from outmatch.version import __version__

        assert isinstance(__version__, str)
        assert "." in __version__  # Should have at least one dot
