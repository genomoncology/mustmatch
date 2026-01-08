"""Tests for the outmatch pytest plugin."""

from pathlib import Path

import pytest

from outmatch.pytest import MarkdownTest


class TestMarkdownTestDiscovery:
    """Tests for MarkdownTest.discover() method."""

    def test_discover_empty_dir(self, tmp_path: Path) -> None:
        """Discovery on empty directory yields no tests."""
        tests = list(MarkdownTest.discover(tmp_path))
        assert tests == []

    def test_discover_nonexistent_dir(self, tmp_path: Path) -> None:
        """Discovery on non-existent directory yields no tests."""
        tests = list(MarkdownTest.discover(tmp_path / "nonexistent"))
        assert tests == []

    def test_discover_single_bash_block(self, tmp_path: Path) -> None:
        """Discovers a single bash block."""
        md = tmp_path / "test.md"
        md.write_text("# Hello\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"
        assert tests[0].file == md
        assert tests[0].line == 4
        assert tests[0].name == "Hello"

    def test_discover_multiple_blocks(self, tmp_path: Path) -> None:
        """Discovers multiple bash blocks in a file."""
        md = tmp_path / "test.md"
        md.write_text(
            "# First\n\n```bash\necho first\n```\n\n"
            "# Second\n\n```bash\necho second\n```\n"
        )

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 2
        assert tests[0].content == "echo first"
        assert tests[0].name == "First"
        assert tests[1].content == "echo second"
        assert tests[1].name == "Second"

    def test_discover_multiple_files(self, tmp_path: Path) -> None:
        """Discovers blocks across multiple files."""
        (tmp_path / "a.md").write_text("```bash\necho a\n```\n")
        (tmp_path / "b.md").write_text("```bash\necho b\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 2

    def test_discover_nested_dirs(self, tmp_path: Path) -> None:
        """Discovers blocks in nested directories."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (tmp_path / "top.md").write_text("```bash\necho top\n```\n")
        (subdir / "nested.md").write_text("```bash\necho nested\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 2

    def test_discover_with_exclude(self, tmp_path: Path) -> None:
        """Excludes files matching exclude patterns."""
        (tmp_path / "keep.md").write_text("```bash\necho keep\n```\n")
        (tmp_path / "skip_this.md").write_text("```bash\necho skip\n```\n")

        tests = list(MarkdownTest.discover(tmp_path, exclude=["skip_this"]))

        assert len(tests) == 1
        assert "keep" in str(tests[0].file)

    def test_discover_custom_pattern(self, tmp_path: Path) -> None:
        """Uses custom glob pattern."""
        (tmp_path / "test.md").write_text("```bash\necho md\n```\n")
        (tmp_path / "test.txt").write_text("```bash\necho txt\n```\n")

        tests = list(MarkdownTest.discover(tmp_path, pattern="*.txt"))

        assert len(tests) == 1
        assert tests[0].file.suffix == ".txt"

    def test_discover_sh_block(self, tmp_path: Path) -> None:
        """Discovers ```sh blocks."""
        md = tmp_path / "test.md"
        md.write_text("```sh\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"

    def test_discover_shell_block(self, tmp_path: Path) -> None:
        """Discovers ```shell blocks."""
        md = tmp_path / "test.md"
        md.write_text("```shell\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"

    def test_discover_ignores_other_blocks(self, tmp_path: Path) -> None:
        """Ignores non-bash code blocks."""
        md = tmp_path / "test.md"
        md.write_text("```python\nprint('hello')\n```\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 1
        assert tests[0].content == "echo hello"

    def test_discover_empty_block_skipped(self, tmp_path: Path) -> None:
        """Skips empty bash blocks."""
        md = tmp_path / "test.md"
        content = "# Header\n\n```bash\n\n```\n\n# Other\n\n```bash\necho hi\n```\n"
        md.write_text(content)

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 1
        assert tests[0].content == "echo hi"

    def test_discover_whitespace_only_block_skipped(self, tmp_path: Path) -> None:
        """Skips whitespace-only bash blocks."""
        md = tmp_path / "test.md"
        md.write_text("```bash\n   \n  \n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert len(tests) == 0


class TestMarkdownTestParsing:
    """Tests for markdown parsing details."""

    def test_find_name_from_heading(self, tmp_path: Path) -> None:
        """Finds block name from preceding heading."""
        md = tmp_path / "test.md"
        md.write_text("## Installation\n\n```bash\necho install\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert tests[0].name == "Installation"

    def test_find_name_from_h3(self, tmp_path: Path) -> None:
        """Finds block name from h3 heading."""
        md = tmp_path / "test.md"
        md.write_text("### Quick Start\n\n```bash\necho start\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert tests[0].name == "Quick Start"

    def test_find_name_from_comment(self, tmp_path: Path) -> None:
        """Finds block name from HTML comment."""
        md = tmp_path / "test.md"
        md.write_text("<!-- test block -->\n```bash\necho test\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert tests[0].name == "test block"

    def test_unnamed_block(self, tmp_path: Path) -> None:
        """Falls back to 'Unnamed block' when no name found."""
        md = tmp_path / "test.md"
        # Block with no preceding heading or comment
        md.write_text("Some text that isn't a heading.\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        # Should fall back to "Unnamed block"
        assert tests[0].name == "Unnamed block"

    def test_multiline_content(self, tmp_path: Path) -> None:
        """Parses multiline bash content correctly."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho line1\necho line2\necho line3\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert tests[0].content == "echo line1\necho line2\necho line3"

    def test_preserves_indentation(self, tmp_path: Path) -> None:
        """Preserves indentation in bash blocks."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nif true; then\n    echo indented\nfi\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert "    echo indented" in tests[0].content


class TestMarkdownTestId:
    """Tests for MarkdownTest.id property."""

    def test_id_format(self, tmp_path: Path) -> None:
        """ID format is file:line."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        assert tests[0].id == f"{md}:2"

    def test_unique_ids(self, tmp_path: Path) -> None:
        """Each block has a unique ID."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho 1\n```\n\n```bash\necho 2\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        ids = [t.id for t in tests]
        assert len(ids) == len(set(ids))


class TestMarkdownTestRepr:
    """Tests for MarkdownTest.__repr__ method."""

    def test_repr(self, tmp_path: Path) -> None:
        """Repr includes file, line, and name."""
        md = tmp_path / "test.md"
        md.write_text("# Header\n\n```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        repr_str = repr(tests[0])
        assert str(md) in repr_str
        assert "Header" in repr_str


class TestMarkdownTestRun:
    """Tests for MarkdownTest.run() method."""

    def test_run_success(self, tmp_path: Path) -> None:
        """Successful command passes."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho hello\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        # Should not raise
        tests[0].run()

    def test_run_failure(self, tmp_path: Path) -> None:
        """Failed command raises AssertionError."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nexit 1\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert str(md) in str(exc_info.value)
        assert "Exit code: 1" in str(exc_info.value)

    def test_run_with_env(self, tmp_path: Path) -> None:
        """Environment variables are passed to command."""
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$MY_VAR" = "hello"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        # Should pass with env var
        tests[0].run(env={"MY_VAR": "hello"})

    def test_run_with_cwd(self, tmp_path: Path) -> None:
        """Working directory is respected."""
        md = tmp_path / "test.md"
        marker = tmp_path / "marker.txt"
        marker.write_text("found")
        md.write_text("```bash\ntest -f marker.txt\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        # Should pass when run from tmp_path
        tests[0].run(cwd=tmp_path)

    def test_run_timeout(self, tmp_path: Path) -> None:
        """Timeout raises TimeoutError."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nsleep 10\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(TimeoutError) as exc_info:
            tests[0].run(timeout=0.1)

        assert "timed out" in str(exc_info.value)

    def test_run_stderr_in_error(self, tmp_path: Path) -> None:
        """Stderr is included in error message."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho error >&2; exit 1\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert "error" in str(exc_info.value)
        assert "Stderr:" in str(exc_info.value)

    def test_run_stdout_in_error(self, tmp_path: Path) -> None:
        """Stdout is included in error message."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho output; exit 1\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(AssertionError) as exc_info:
            tests[0].run()

        assert "output" in str(exc_info.value)
        assert "Stdout:" in str(exc_info.value)

    def test_run_bash_e_flag(self, tmp_path: Path) -> None:
        """bash -e causes early exit on error."""
        md = tmp_path / "test.md"
        md.write_text("```bash\nfalse\necho should not reach\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(AssertionError):
            tests[0].run()

    def test_run_bash_u_flag(self, tmp_path: Path) -> None:
        """bash -u errors on undefined variables."""
        md = tmp_path / "test.md"
        md.write_text('```bash\necho "$UNDEFINED_VAR_12345"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        with pytest.raises(AssertionError):
            tests[0].run()


class TestMarkdownTestRunWithFixture:
    """Tests for MarkdownTest.run_with_fixture() method."""

    def test_run_with_fixture_dict(self, tmp_path: Path) -> None:
        """Dict fixture values become env vars."""
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$KEY" = "value"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        tests[0].run_with_fixture({"KEY": "value"})

    def test_run_with_fixture_string(self, tmp_path: Path) -> None:
        """String fixture becomes FIXTURE_VALUE."""
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$FIXTURE_VALUE" = "hello"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        tests[0].run_with_fixture("hello")

    def test_run_with_fixture_path(self, tmp_path: Path) -> None:
        """Path fixture becomes FIXTURE_VALUE string."""
        md = tmp_path / "test.md"
        marker = tmp_path / "marker.txt"
        marker.write_text("content")
        md.write_text('```bash\ncat "$FIXTURE_VALUE"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        tests[0].run_with_fixture(marker)

    def test_run_with_fixture_other(self, tmp_path: Path) -> None:
        """Other types are converted to string."""
        md = tmp_path / "test.md"
        md.write_text('```bash\ntest "$FIXTURE_VALUE" = "42"\n```\n')

        tests = list(MarkdownTest.discover(tmp_path))

        tests[0].run_with_fixture(42)


class TestPytestIntegration:
    """Tests for pytest integration patterns."""

    def test_parametrize_pattern(self, tmp_path: Path) -> None:
        """Standard parametrize pattern works."""
        md = tmp_path / "test.md"
        content = (
            "# Test 1\n\n```bash\necho test1\n```\n\n"
            "# Test 2\n\n```bash\necho test2\n```\n"
        )
        md.write_text(content)

        tests = list(MarkdownTest.discover(tmp_path))

        # Simulating what pytest.mark.parametrize does
        for test in tests:
            test.run()

    def test_ids_work_with_parametrize(self, tmp_path: Path) -> None:
        """IDs are suitable for pytest parametrize."""
        md = tmp_path / "test.md"
        md.write_text("```bash\necho test\n```\n")

        tests = list(MarkdownTest.discover(tmp_path))

        # IDs should be valid strings for pytest
        ids = [t.id for t in tests]
        for id_ in ids:
            assert isinstance(id_, str)
            assert len(id_) > 0


class TestPluginImports:
    """Tests for plugin module imports."""

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


class TestDiscoverDocsFolder:
    """Integration test using actual docs folder."""

    def test_discover_project_docs(self) -> None:
        """Can discover bash blocks in project docs."""
        docs_path = Path(__file__).parent.parent / "docs"
        if not docs_path.exists():
            pytest.skip("docs folder not found")

        tests = list(MarkdownTest.discover(docs_path))

        # Should find some tests
        assert len(tests) > 0

        # All should have valid properties
        for test in tests:
            assert test.file.exists()
            assert test.line > 0
            assert test.content
            assert test.id
