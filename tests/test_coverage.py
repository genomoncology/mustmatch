"""Direct function tests for coverage.

The bash doc tests verify CLI behavior end-to-end.
These tests ensure internal code paths are covered.
"""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from outmatch import (
    ColorMode,
    CompareMode,
    CompareResult,
    ExpectConfig,
    NormalizeOptions,
    compare,
    main,
    preprocess,
)
from outmatch.cli import (
    _determine_mode,
    _get_expected,
    _parse_replacements,
    app,
    cli,
    version_callback,
)
from outmatch.compare import (
    _format_set_diff,
    _record_contained,
    compare_contains,
    compare_exact,
    compare_json,
    compare_jsonl,
    compare_jsonl_contains,
    compare_jsonl_key,
    compare_jsonl_set,
    compare_regex,
)
from outmatch.json_utils import (
    _navigate,
    _remove_single_path,
    normalize_json,
    parse_jsonl,
    remove_json_paths,
)
from outmatch.normalize import (
    apply_redactions,
    apply_replacements,
    collapse_whitespace,
    normalize_newlines,
    strip_ansi,
)
from outmatch.output import (
    colorize_diff,
    format_error,
    should_use_color,
    unified_diff,
)


# Normalize module tests
class TestNormalize:
    def test_strip_ansi(self):
        assert strip_ansi("\033[31mred\033[0m") == "red"
        assert strip_ansi("plain") == "plain"

    def test_normalize_newlines(self):
        assert normalize_newlines("a\r\nb\rc") == "a\nb\nc"

    def test_collapse_whitespace(self):
        assert collapse_whitespace("a   b\n\nc") == "a b c"

    def test_apply_replacements(self):
        result = apply_replacements("x123y", (("\\d+", "N"),))
        assert result == "xNy"

    def test_apply_redactions(self):
        result = apply_redactions("secret123", ("\\d+",))
        assert result == "secret<redacted>"

    def test_preprocess_all_options(self):
        opts = NormalizeOptions(
            strip_ansi=True,
            normalize_newlines=True,
            trim=True,
            collapse_whitespace=True,
            ignore_case=True,
            replacements=(("X", "Y"),),
            redactions=("Z",),
        )
        result = preprocess("  \033[31mX\033[0m Z  ", opts)
        assert result == "y <redacted>"


# JSON utils tests
class TestJsonUtils:
    def test_normalize_json_dict(self):
        result = normalize_json({"b": 2, "a": 1})
        assert list(result.keys()) == ["a", "b"]

    def test_normalize_json_nested(self):
        result = normalize_json({"x": {"b": 2, "a": 1}})
        assert list(result["x"].keys()) == ["a", "b"]

    def test_normalize_json_list(self):
        result = normalize_json([{"b": 2, "a": 1}])
        assert list(result[0].keys()) == ["a", "b"]

    def test_parse_jsonl(self):
        result = parse_jsonl('{"a":1}\n{"b":2}')
        assert result == [{"a": 1}, {"b": 2}]

    def test_parse_jsonl_blank_lines(self):
        result = parse_jsonl('{"a":1}\n\n{"b":2}')
        assert result == [{"a": 1}, {"b": 2}]

    def test_remove_json_paths_empty(self):
        obj = {"a": 1}
        assert remove_json_paths(obj, ()) == {"a": 1}

    def test_remove_json_paths_simple(self):
        obj = {"a": 1, "b": 2}
        result = remove_json_paths(obj, ("$.a",))
        assert result == {"b": 2}

    def test_remove_json_paths_nested(self):
        obj = {"x": {"a": 1, "b": 2}}
        result = remove_json_paths(obj, ("$.x.a",))
        assert result == {"x": {"b": 2}}

    def test_remove_json_paths_array(self):
        obj = {"x": [1, 2, 3]}
        result = remove_json_paths(obj, ("$.x[0]",))
        assert result == {"x": [2, 3]}

    def test_navigate_dict(self):
        assert _navigate({"a": 1}, "a") == 1

    def test_navigate_list(self):
        assert _navigate([1, 2, 3], "1") == 2

    def test_navigate_invalid_index(self):
        assert _navigate([1], "5") is None

    def test_navigate_not_dict(self):
        assert _navigate("string", "x") is None

    def test_remove_single_path_empty(self):
        obj = {}
        _remove_single_path(obj, "$")
        assert obj == {}

    def test_remove_single_path_missing(self):
        obj = {"a": 1}
        _remove_single_path(obj, "$.b.c")
        assert obj == {"a": 1}


# Compare module tests
class TestCompare:
    def test_compare_exact_success(self):
        result = compare_exact("hello", "hello")
        assert result.success

    def test_compare_exact_newline_normalization(self):
        result = compare_exact("hello\n", "hello")
        assert result.success

    def test_compare_exact_failure(self):
        result = compare_exact("hello", "world")
        assert not result.success
        assert "Exact match failed" in result.message

    def test_compare_exact_diff_context(self):
        # Test that context parameter affects diff output
        actual = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nCHANGED\nline9"
        expected = "line1\nline2\nline3\nline4\nline5\nline6\nline7\noriginal\nline9"
        result_ctx1 = compare_exact(actual, expected, context=1)
        result_ctx5 = compare_exact(actual, expected, context=5)
        # With smaller context, fewer surrounding lines shown
        assert result_ctx1.message.count("line") < result_ctx5.message.count("line")

    def test_compare_contains_success(self):
        result = compare_contains("hello world", "world")
        assert result.success

    def test_compare_contains_failure(self):
        result = compare_contains("hello", "world")
        assert not result.success

    def test_compare_contains_long_output(self):
        result = compare_contains("x" * 600, "y")
        assert not result.success
        assert "..." in result.message

    def test_compare_regex_success(self):
        result = compare_regex("abc123", r"\d+")
        assert result.success

    def test_compare_regex_failure(self):
        result = compare_regex("abc", r"\d+")
        assert not result.success

    def test_compare_regex_invalid(self):
        result = compare_regex("test", "[invalid")
        assert not result.success
        assert "Invalid regex" in result.message

    def test_compare_json_success(self):
        result = compare_json('{"a":1}', '{"a":1}')
        assert result.success

    def test_compare_json_field_order(self):
        result = compare_json('{"b":2,"a":1}', '{"a":1,"b":2}')
        assert result.success

    def test_compare_json_invalid_actual(self):
        result = compare_json("not json", '{"a":1}')
        assert not result.success
        assert "Actual is not valid JSON" in result.message

    def test_compare_json_invalid_expected(self):
        result = compare_json('{"a":1}', "not json")
        assert not result.success
        assert "Expected is not valid JSON" in result.message

    def test_compare_json_mismatch(self):
        result = compare_json('{"a":1}', '{"a":2}')
        assert not result.success
        assert "mismatch" in result.message.lower()

    def test_compare_json_with_ignore(self):
        result = compare_json('{"a":1,"ts":"x"}', '{"a":1}', ("$.ts",))
        assert result.success

    def test_compare_jsonl_success(self):
        result = compare_jsonl('{"a":1}', '{"a":1}')
        assert result.success

    def test_compare_jsonl_count_mismatch(self):
        result = compare_jsonl('{"a":1}\n{"b":2}', '{"a":1}')
        assert not result.success
        assert "count mismatch" in result.message

    def test_compare_jsonl_record_mismatch(self):
        result = compare_jsonl('{"a":1}', '{"a":2}')
        assert not result.success
        assert "Record 0 mismatch" in result.message

    def test_compare_jsonl_invalid(self):
        result = compare_jsonl("not json", '{"a":1}')
        assert not result.success
        assert "JSON parse error" in result.message

    def test_compare_jsonl_with_ignore(self):
        result = compare_jsonl('{"a":1,"ts":"x"}', '{"a":1}', ("$.ts",))
        assert result.success

    def test_compare_jsonl_set_success(self):
        result = compare_jsonl_set('{"a":1}\n{"b":2}', '{"b":2}\n{"a":1}')
        assert result.success

    def test_compare_jsonl_set_missing(self):
        result = compare_jsonl_set('{"a":1}', '{"a":1}\n{"b":2}')
        assert not result.success
        assert "Missing" in result.message

    def test_compare_jsonl_set_extra(self):
        result = compare_jsonl_set('{"a":1}\n{"b":2}', '{"a":1}')
        assert not result.success
        assert "Extra" in result.message

    def test_compare_jsonl_set_invalid(self):
        result = compare_jsonl_set("not json", '{"a":1}')
        assert not result.success

    def test_compare_jsonl_set_with_ignore(self):
        result = compare_jsonl_set('{"a":1,"ts":"x"}', '{"a":1}', ("$.ts",))
        assert result.success

    def test_compare_jsonl_key_success(self):
        actual = '{"id":1,"name":"a"}\n{"id":2,"name":"b"}'
        expected = '{"id":2,"name":"b"}\n{"id":1,"name":"a"}'
        result = compare_jsonl_key(actual, expected, "id")
        assert result.success

    def test_compare_jsonl_key_missing(self):
        result = compare_jsonl_key('{"name":"a"}', '{"id":1}', "id")
        assert not result.success
        assert "missing key field" in result.message

    def test_compare_jsonl_key_mismatch(self):
        result = compare_jsonl_key('{"id":1,"name":"a"}', '{"id":1,"name":"b"}', "id")
        assert not result.success
        assert "Mismatch" in result.message

    def test_compare_jsonl_key_invalid(self):
        result = compare_jsonl_key("not json", '{"id":1}', "id")
        assert not result.success

    def test_compare_jsonl_key_with_ignore(self):
        result = compare_jsonl_key('{"id":1,"ts":"x"}', '{"id":1}', "id", ("$.ts",))
        assert result.success

    def test_compare_jsonl_key_extra_keys(self):
        result = compare_jsonl_key('{"id":1}\n{"id":2}', '{"id":1}', "id")
        assert not result.success
        assert "Extra keys" in result.message

    def test_compare_jsonl_key_missing_keys(self):
        result = compare_jsonl_key('{"id":1}', '{"id":1}\n{"id":2}', "id")
        assert not result.success
        assert "Missing keys" in result.message

    def test_compare_jsonl_key_duplicate_actual(self):
        result = compare_jsonl_key('{"id":1}\n{"id":1}', '{"id":1}', "id")
        assert not result.success
        assert "Duplicate key" in result.message
        assert "actual" in result.message.lower()

    def test_compare_jsonl_key_duplicate_expected(self):
        result = compare_jsonl_key('{"id":1}', '{"id":1}\n{"id":1}', "id")
        assert not result.success
        assert "Duplicate key" in result.message
        assert "expected" in result.message.lower()

    def test_compare_jsonl_contains_success(self):
        result = compare_jsonl_contains('{"a":1,"b":2}', '{"a":1}')
        assert result.success

    def test_compare_jsonl_contains_missing(self):
        result = compare_jsonl_contains('{"a":1}', '{"b":2}')
        assert not result.success
        assert "Missing" in result.message

    def test_compare_jsonl_contains_invalid(self):
        result = compare_jsonl_contains("not json", '{"a":1}')
        assert not result.success

    def test_compare_jsonl_contains_with_ignore(self):
        result = compare_jsonl_contains('{"a":1,"ts":"x"}', '{"a":1}', ("$.ts",))
        assert result.success

    def test_record_contained_dict(self):
        assert _record_contained({"a": 1}, [{"a": 1, "b": 2}])

    def test_record_contained_exact(self):
        assert _record_contained(1, [1, 2, 3])

    def test_record_contained_not_found(self):
        assert not _record_contained({"a": 1}, [{"b": 2}])

    def test_format_set_diff_many_missing(self):
        result = _format_set_diff([], ['{"x":' + str(i) + "}" for i in range(10)])
        assert "... and 5 more" in result.message

    def test_format_set_diff_many_extra(self):
        result = _format_set_diff(['{"x":' + str(i) + "}" for i in range(10)], [])
        assert "... and 5 more" in result.message

    def test_compare_dispatcher(self):
        config = ExpectConfig(mode=CompareMode.EXACT)
        result = compare("hello", "hello", config)
        assert result.success

    def test_compare_dispatcher_all_modes(self):
        modes = [
            (CompareMode.EXACT, "hello", "hello"),
            (CompareMode.CONTAINS, "hello world", "world"),
            (CompareMode.REGEX, "abc123", r"\d+"),
            (CompareMode.JSON, '{"a":1}', '{"a":1}'),
            (CompareMode.JSONL, '{"a":1}', '{"a":1}'),
            (CompareMode.JSONL_SET, '{"a":1}', '{"a":1}'),
            (CompareMode.JSONL_CONTAINS, '{"a":1}', '{"a":1}'),
        ]
        for mode, actual, expected in modes:
            config = ExpectConfig(mode=mode)
            result = compare(actual, expected, config)
            assert result.success, f"Mode {mode} failed"

    def test_compare_jsonl_key_mode(self):
        config = ExpectConfig(mode=CompareMode.JSONL_KEY, jsonl_key_field="id")
        result = compare('{"id":1}', '{"id":1}', config)
        assert result.success


# Output module tests
class TestOutput:
    def test_unified_diff(self):
        result = unified_diff("hello", "world")
        assert "---" in result
        assert "+++" in result

    def test_colorize_diff(self):
        diff = "--- expected\n+++ actual\n@@ line @@\n-old\n+new\n context"
        result = colorize_diff(diff)
        assert "\033[" in result

    def test_should_use_color_always(self):
        assert should_use_color(ColorMode.ALWAYS)

    def test_should_use_color_never(self):
        assert not should_use_color(ColorMode.NEVER)

    def test_format_error_with_diff(self):
        result = CompareResult(success=False, message="--- expected\n+++ actual")
        config = ExpectConfig(color=ColorMode.ALWAYS)
        output = format_error(result, config)
        assert "FAIL:" in output

    def test_format_error_without_diff(self):
        result = CompareResult(success=False, message="simple error")
        config = ExpectConfig(color=ColorMode.ALWAYS)
        output = format_error(result, config)
        assert "FAIL:" in output

    def test_format_error_no_color(self):
        result = CompareResult(success=False, message="error")
        config = ExpectConfig(color=ColorMode.NEVER)
        output = format_error(result, config)
        assert "\033[" not in output


# Config tests
class TestConfig:
    def test_normalize_options_defaults(self):
        opts = NormalizeOptions()
        assert not opts.strip_ansi
        assert not opts.trim
        assert opts.replacements == ()
        assert opts.redactions == ()

    def test_compare_result_defaults(self):
        result = CompareResult(success=True)
        assert result.message == ""

    def test_expect_config_defaults(self):
        config = ExpectConfig()
        assert config.mode == CompareMode.EXACT
        assert config.quiet is False
        assert config.color == ColorMode.AUTO


# CLI tests
class TestCli:
    runner = CliRunner()

    def test_exact_match(self):
        result = self.runner.invoke(app, ["hello"], input="hello\n")
        assert result.exit_code == 0

    def test_exact_mismatch(self):
        result = self.runner.invoke(app, ["hello"], input="world\n")
        assert result.exit_code == 1

    def test_contains_mode(self):
        result = self.runner.invoke(app, ["--contains", "world"], input="hello world\n")
        assert result.exit_code == 0

    def test_regex_mode(self):
        result = self.runner.invoke(app, ["--regex", r"\d+"], input="abc123\n")
        assert result.exit_code == 0

    def test_json_mode(self):
        result = self.runner.invoke(app, ["--json", '{"a":1}'], input='{"a":1}\n')
        assert result.exit_code == 0

    def test_jsonl_mode(self):
        result = self.runner.invoke(app, ["--jsonl", '{"a":1}'], input='{"a":1}\n')
        assert result.exit_code == 0

    def test_jsonl_set_mode(self):
        result = self.runner.invoke(
            app, ["--jsonl-set", '{"a":1}'], input='{"a":1}\n'
        )
        assert result.exit_code == 0

    def test_jsonl_key_mode(self):
        result = self.runner.invoke(
            app, ["--jsonl-key", "id", '{"id":1}'], input='{"id":1}\n'
        )
        assert result.exit_code == 0

    def test_jsonl_contains_mode(self):
        result = self.runner.invoke(
            app, ["--jsonl-contains", '{"a":1}'], input='{"a":1,"b":2}\n'
        )
        assert result.exit_code == 0

    def test_strip_ansi(self):
        result = self.runner.invoke(
            app, ["--strip-ansi", "red"], input="\033[31mred\033[0m\n"
        )
        assert result.exit_code == 0

    def test_normalize_newlines(self):
        result = self.runner.invoke(
            app, ["--normalize-newlines", "a\nb"], input="a\r\nb\n"
        )
        assert result.exit_code == 0

    def test_trim(self):
        result = self.runner.invoke(app, ["--trim", "hello"], input="  hello  \n")
        assert result.exit_code == 0

    def test_collapse_whitespace(self):
        result = self.runner.invoke(
            app, ["--collapse-whitespace", "--trim", "a b"], input="a   b\n"
        )
        assert result.exit_code == 0

    def test_ignore_case(self):
        result = self.runner.invoke(
            app, ["-i", "hello"], input="HELLO\n"
        )
        assert result.exit_code == 0

    def test_replace(self):
        result = self.runner.invoke(
            app, ["--replace", r"\d+", "--replace", "N", "xNy"], input="x123y\n"
        )
        assert result.exit_code == 0

    def test_redact(self):
        result = self.runner.invoke(
            app, ["--redact", r"\d+", "secret<redacted>"], input="secret123\n"
        )
        assert result.exit_code == 0

    def test_json_ignore(self):
        result = self.runner.invoke(
            app,
            ["--json", "--json-ignore", "$.ts", '{"a":1}'],
            input='{"a":1,"ts":"x"}\n',
        )
        assert result.exit_code == 0

    def test_quiet_mode(self):
        result = self.runner.invoke(app, ["-q", "hello"], input="world\n")
        assert result.exit_code == 1
        assert result.output == ""

    def test_color_never(self):
        result = self.runner.invoke(app, ["--color", "never", "hello"], input="world\n")
        assert result.exit_code == 1
        assert "\033[" not in result.output

    def test_color_always(self):
        result = self.runner.invoke(
            app, ["--color", "always", "hello"], input="world\n"
        )
        assert result.exit_code == 1

    def test_expected_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello")
            f.flush()
            result = self.runner.invoke(app, ["-f", f.name], input="hello\n")
            assert result.exit_code == 0

    def test_expected_file_not_found(self):
        result = self.runner.invoke(app, ["-f", "/nonexistent.txt"], input="hello\n")
        assert result.exit_code == 2

    def test_update_mode(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("old")
            f.flush()
            result = self.runner.invoke(
                app, ["--update", "-f", f.name], input="new\n"
            )
            assert result.exit_code == 0
            assert Path(f.name).read_text() == "new\n"

    def test_update_mode_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "new.txt"
            result = self.runner.invoke(
                app, ["--update", "-f", str(path)], input="content\n"
            )
            assert result.exit_code == 0
            assert path.read_text() == "content\n"

    def test_no_expected_value(self):
        result = self.runner.invoke(app, [], input="hello\n")
        assert result.exit_code == 2
        assert "expected value required" in result.output

    def test_version(self):
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "outmatch" in result.output

    def test_main_function(self):
        # Test the main() function for backwards compatibility
        import sys
        from io import StringIO
        old_stdin = sys.stdin
        sys.stdin = StringIO("hello\n")
        try:
            result = main(["hello"])
            assert result == 0
        finally:
            sys.stdin = old_stdin

    def test_cli_entry_point(self):
        # Test cli() raises SystemExit
        try:
            import sys
            from io import StringIO
            old_stdin = sys.stdin
            sys.stdin = StringIO("hello\n")
            cli()
        except SystemExit:
            pass
        finally:
            sys.stdin = old_stdin


# Helper function tests
class TestHelperFunctions:
    def test_determine_mode_exact(self):
        result = _determine_mode(False, False, False, False, False, None, False)
        assert result == CompareMode.EXACT

    def test_determine_mode_contains(self):
        result = _determine_mode(True, False, False, False, False, None, False)
        assert result == CompareMode.CONTAINS

    def test_determine_mode_regex(self):
        result = _determine_mode(False, True, False, False, False, None, False)
        assert result == CompareMode.REGEX

    def test_determine_mode_json(self):
        result = _determine_mode(False, False, True, False, False, None, False)
        assert result == CompareMode.JSON

    def test_determine_mode_jsonl(self):
        result = _determine_mode(False, False, False, True, False, None, False)
        assert result == CompareMode.JSONL

    def test_determine_mode_jsonl_set(self):
        result = _determine_mode(False, False, False, False, True, None, False)
        assert result == CompareMode.JSONL_SET

    def test_determine_mode_jsonl_key(self):
        result = _determine_mode(False, False, False, False, False, "id", False)
        assert result == CompareMode.JSONL_KEY

    def test_determine_mode_jsonl_contains(self):
        result = _determine_mode(False, False, False, False, False, None, True)
        assert result == CompareMode.JSONL_CONTAINS

    def test_parse_replacements_empty(self):
        assert _parse_replacements([]) == ()

    def test_parse_replacements_pairs(self):
        result = _parse_replacements(["a", "b", "c", "d"])
        assert result == (("a", "b"), ("c", "d"))

    def test_parse_replacements_odd(self):
        # This should raise typer.Exit
        import typer
        with pytest.raises(typer.Exit):
            _parse_replacements(["a", "b", "c"])

    def test_get_expected_arg(self):
        result = _get_expected("hello", None, False)
        assert result == "hello"

    def test_get_expected_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("content")
            f.flush()
            result = _get_expected(None, Path(f.name), False)
            assert result == "content"

    def test_get_expected_file_update_mode(self):
        # In update mode, missing file returns empty string
        result = _get_expected(None, Path("/nonexistent.txt"), True)
        assert result == ""

    def test_version_callback_true(self):
        import typer
        with pytest.raises(typer.Exit):
            version_callback(True)

    def test_version_callback_false(self):
        # Should not raise
        version_callback(False)

    def test_get_expected_file_oserror(self):
        # Test OSError handling (other than FileNotFoundError)
        import typer
        # Create a path that will fail with OSError
        with pytest.raises(typer.Exit):
            # Reading a directory as a file triggers OSError on some systems
            _get_expected(None, Path("/dev/null/nonexistent"), False)


# Additional edge case tests for coverage
class TestEdgeCases:
    runner = CliRunner()

    def test_main_exception_handler(self):
        # Test the generic exception handler in main()
        import sys
        from io import StringIO
        old_stdin = sys.stdin
        sys.stdin = StringIO("test\n")
        try:
            # Invalid color mode triggers exception
            result = main(["--color", "invalid", "test"])
            assert result == 2
        finally:
            sys.stdin = old_stdin

    def test_main_typer_exit_nonzero(self):
        # Test typer.Exit with non-zero exit code through main()
        import sys
        from io import StringIO
        old_stdin = sys.stdin
        sys.stdin = StringIO("hello\n")
        try:
            # Mismatch triggers exit code 1
            result = main(["world"])
            assert result == 1
        finally:
            sys.stdin = old_stdin

    def test_jsonl_key_expected_missing_key(self):
        # Test when expected record is missing the key field
        from outmatch.compare import compare_jsonl_key
        result = compare_jsonl_key('{"id":1}', '{"name":"test"}', "id")
        assert not result.success
        assert "missing key" in result.message.lower()

    def test_remove_path_intermediate_none(self):
        # Test early return when navigating through None
        from outmatch.json_utils import _remove_single_path
        obj = {"a": {"b": 1}}
        _remove_single_path(obj, "$.x.y.z")  # x doesn't exist
        assert obj == {"a": {"b": 1}}  # Unchanged

    def test_navigate_deep_none(self):
        # Navigate through missing intermediate path
        from outmatch.json_utils import remove_json_paths
        obj = {"a": 1}
        result = remove_json_paths(obj, ("$.b.c.d",))  # b doesn't exist
        assert result == {"a": 1}
