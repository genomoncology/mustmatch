"""Tests for the outmatch pytest plugin."""

from pathlib import Path

import pytest

from outmatch.pytest import MarkdownTest


class TestMarkdownTestParsing:
    """Tests for MarkdownTest._parse_file()."""

    def test_parse_single_bash_block(self, tmp_path: Path) -> None:
        """Parses a single bash block."""
        md = tmp_path / "test.md"
        md.write_text("# Hello\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"
        assert tests[0].file == md
        assert tests[0].line == 4
        assert tests[0].name == "Hello"

    def test_parse_multiple_blocks(self, tmp_path: Path) -> None:
        """Parses multiple bash blocks."""
        md = tmp_path / "test.md"
        md.write_text(
            "# First\n\n```bash\necho first\n```\n\n"
            "# Second\n\n```bash\necho second\n```\n"
        )

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 2
        assert tests[0].content == "echo first"
        assert tests[0].name == "First"
        assert tests[1].content == "echo second"
        assert tests[1].name == "Second"

    def test_parse_sh_block(self, tmp_path: Path) -> None:
        """Parses ```sh blocks."""
        md = tmp_path / "test.md"
        md.write_text("```sh\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"

    def test_parse_shell_block(self, tmp_path: Path) -> None:
        """Parses ```shell blocks."""
        md = tmp_path / "test.md"
        md.write_text("```shell\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 1

    def test_ignores_other_blocks(self, tmp_path: Path) -> None:
        """Ignores non-bash code blocks."""
        md = tmp_path / "test.md"
        md.write_text("```python\nprint('hello')\n```\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"

    def test_empty_block_skipped(self, tmp_path: Path) -> None:
        """Skips empty bash blocks."""
        md = tmp_path / "test.md"
        md.write_text("```bash\n\n```\n\n```bash\necho hi\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 1
        assert tests[0].content == "echo hi"

    def test_whitespace_only_block_skipped(self, tmp_path: Path) -> None:
        """Skips whitespace-only blocks."""
        md = tmp_path / "test.md"
        md.write_text("```bash\n   \n  \n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert len(tests) == 0

    def test_find_name_from_heading(self, tmp_path: Path) -> None:
        """Finds block name from preceding heading."""
        md = tmp_path / "test.md"
        md.write_text("## Installation\n\n```bash\necho install\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert tests[0].name == "Installation"

    def test_find_name_from_comment(self, tmp_path: Path) -> None:
        """Finds block name from HTML comment."""
        md = tmp_path / "test.md"
        md.write_text("<!-- test block -->\n```bash\necho test\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert tests[0].name == "test block"

    def test_unnamed_block(self, tmp_path: Path) -> None:
        """Falls back to 'Unnamed block' when no name found."""
        md = tmp_path / "test.md"
        md.write_text("Some text.\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert tests[0].name == "Unnamed block"

    def test_multiline_content(self, tmp_path: Path) -> None:
        """Parses multiline content."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho line1\necho line2\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert tests[0].content == "echo line1\necho line2"

    def test_preserves_indentation(self, tmp_path: Path) -> None:
        """Preserves indentation."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nif true; then\n    echo indented\nfi\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        assert "    echo indented" in tests[0].content


class TestMarkdownTestRepr:
    """Tests for MarkdownTest.__repr__."""

    def test_repr(self, tmp_path: Path) -> None:
        """Repr includes file, line, and name."""
        md = tmp_path / "test.md"
        md.write_text("# Header\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        repr_str = repr(tests[0])
        assert str(md) in repr_str
        assert "Header" in repr_str


class TestMarkdownTestRun:
    """Tests for MarkdownTest.run()."""

    def test_run_success(self, tmp_path: Path) -> None:
        """Successful command passes."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho hello\n```\n")

        tests = list(MarkdownTest._parse_file(md))
        tests[0].run()

    def test_run_failure(self, tmp_path: Path) -> None:
        """Failed command raises AssertionError."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nexit 1\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert "Exit code: 1" in str(exc_info.value)

    def test_run_with_env(self, tmp_path: Path) -> None:
        """Environment variables are passed."""
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$MY_VAR" = "hello"\n```\n')

        tests = list(MarkdownTest._parse_file(md))
        tests[0].run(env={"MY_VAR": "hello"})

    def test_run_with_cwd(self, tmp_path: Path) -> None:
        """Working directory is respected."""
        md = tmp_path / "test.md"
        marker = tmp_path / "marker.txt"
        marker.write_text("found")
        md.write_text("```bash\ntest -f marker.txt\n```\n")

        tests = list(MarkdownTest._parse_file(md))
        tests[0].run(cwd=tmp_path)

    def test_run_timeout(self, tmp_path: Path) -> None:
        """Timeout raises TimeoutError."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nsleep 10\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(TimeoutError) as exc_info:
            tests[0].run(timeout=0.1)

        assert "timed out" in str(exc_info.value)

    def test_run_stderr_in_error(self, tmp_path: Path) -> None:
        """Stderr is included in error."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho error >&2; exit 1\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert "Stderr:" in str(exc_info.value)

    def test_run_stdout_in_error(self, tmp_path: Path) -> None:
        """Stdout is included in error."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho output; exit 1\n```\n")

        tests = list(MarkdownTest._parse_file(md))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert "Stdout:" in str(exc_info.value)


class TestPluginImports:
    """Tests for plugin imports."""

    def test_import_from_pytest_module(self) -> None:
        """Can import MarkdownTest from outmatch.pytest."""
        from outmatch.pytest import MarkdownTest as MT
        assert MT is not None

    def test_import_from_main_module(self) -> None:
        """Can import MarkdownTest from outmatch."""
        from outmatch import MarkdownTest as MT
        assert MT is not None

    def test_import_from_plugin(self) -> None:
        """Can import from pytest_plugin module."""
        from outmatch.pytest_plugin import MarkdownTest as MT
        assert MT is not None
