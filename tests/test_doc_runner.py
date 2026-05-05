from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from mustmatch.doc_runner import run_markdown_tests


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).strip() + "\n")
    return path


def test_named_run_substitution_supports_nested_json_and_lists(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "workflow.md",
        r"""
        # Workflow

        ```bash run id=search
        printf '{"items":[{"id":"widget-123"}],"meta":{"count":1}}\n'
        ```

        ```bash run id=detail uses=search
        printf 'Detail {{search.items.0.id}} count={{search.meta.count}}\n'
        ```

        ```text expect=detail contains
        Detail widget-123 count=1
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="bash", quiet=True)

    assert summary.failed == 0
    assert summary.passed == 3


def test_console_block_runs_visible_command_and_checks_output(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "console.md",
        r"""
        # Console Workflow

        ```console mustmatch
        $ printf '# Widget\n\nStatus: active\nOwner: platform-team\n'
        # Widget

        Status: active
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed == 0
    assert summary.passed == 1


def test_console_block_reports_missing_output(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "console.md",
        r"""
        # Console Workflow

        ```console mustmatch
        $ printf 'Status: active\n'
        Status: inactive
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed == 1
    assert "Output did not contain expected text" in summary.failures[0]


def test_missing_substitution_run_fails_clearly(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "broken.md",
        r"""
        # Broken Workflow

        ```bash run id=detail
        printf 'Detail {{missing.id}}\n'
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="bash", quiet=True)

    assert summary.failed == 1
    assert "unknown run id 'missing'" in summary.failures[0]


def test_contexts_can_prepare_private_documentation_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    bin_dir = project / "bin"
    bin_dir.mkdir(parents=True)
    helper = bin_dir / "helper-tool"
    helper.write_text("#!/usr/bin/env bash\nprintf 'helper:%s\\n' \"$DOC_VALUE\"\n")
    helper.chmod(0o755)
    write(
        project / "pyproject.toml",
        r"""
        [tool.mustmatch.contexts.demo]
        cwd = "{tmp}"
        path = ["{root}/bin"]
        required_env = ["DOC_VALUE"]
        setup = ["printf 'ready' > {tmp}/state.txt"]

        [tool.mustmatch.contexts.demo.env]
        DOC_VALUE = "example"
        """,
    )
    doc = write(
        project / "docs" / "context.md",
        r"""
        # Context

        ```bash run id=context-demo context=demo
        printf 'state=%s\n' "$(cat state.txt)"
        helper-tool
        ```

        ```text expect=context-demo contains
        state=ready
        helper:example
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="bash", quiet=True)

    assert summary.failed == 0
    assert summary.passed == 2


def test_context_required_env_reports_missing_values(tmp_path: Path) -> None:
    project = tmp_path / "project"
    write(
        project / "pyproject.toml",
        r"""
        [tool.mustmatch.contexts.needs-secret]
        required_env = ["MISSING_DOC_SECRET"]
        """,
    )
    doc = write(
        project / "docs" / "context.md",
        r"""
        # Context

        ```bash run id=needs-secret context=needs-secret
        printf 'never runs\n'
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="bash", quiet=True)

    assert summary.failed == 1
    assert "requires environment values: MISSING_DOC_SECRET" in summary.failures[0]


def test_console_block_accepts_expected_stderr_exit(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "console-error.md",
        r"""
        # Console Error

        ```console mustmatch exit=2 stream=stderr
        $ mustmatch --bad-option
        Error: unknown option: --bad-option
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed == 0
    assert summary.passed >= 1


def test_console_block_rejects_unknown_stream_directive(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "console-error.md",
        r"""
        # Console Error

        ```console mustmatch stream=stdrr
        $ printf 'visible on stdout\n'
        visible on stdout
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed >= 1
    failure = summary.failures[0].lower()
    assert "stream" in failure
    assert "stdrr" in failure


def test_console_block_rejects_non_integer_exit_directive(tmp_path: Path) -> None:
    doc = write(
        tmp_path / "docs" / "console-error.md",
        r"""
        # Console Error

        ```console mustmatch exit=two
        $ printf 'still exits zero\n'
        still exits zero
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed >= 1
    failure = summary.failures[0].lower()
    assert "exit" in failure
    assert "two" in failure


def test_console_block_exit_mismatch_names_expected_actual_and_stream(
    tmp_path: Path,
) -> None:
    doc = write(
        tmp_path / "docs" / "console-error.md",
        r"""
        # Console Error

        ```console mustmatch exit=0 stream=stderr
        $ mustmatch --bad-option
        Error: unknown option: --bad-option
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="all", quiet=True)

    assert summary.failed >= 1
    failure = summary.failures[0].lower()
    assert "expected exit" in failure
    assert "actual exit" in failure or "exited 2" in failure
    assert "stderr" in failure


def test_named_run_accepts_expected_nonzero_and_uses_run_stream(
    tmp_path: Path,
) -> None:
    doc = write(
        tmp_path / "docs" / "run-error.md",
        r"""
        # Run Error

        ```bash run id=bad-command exit=2 stream=stderr
        mustmatch --bad-option
        ```

        ```text expect=bad-command contains
        Error: unknown option: --bad-option
        ```
        """,
    )

    summary = run_markdown_tests([doc], lang="bash", quiet=True)

    assert summary.failed == 0
    assert summary.passed >= 2


def test_standalone_doc_runner_doc_examples_execute_console_errors() -> None:
    summary = run_markdown_tests(
        [Path("docs/13-standalone-doc-runner.md")],
        lang="all",
        quiet=True,
    )

    assert summary.failed == 0, "\n".join(summary.failures)
    assert summary.passed >= 1


def run_pytest_doc(doc: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(doc), "-q"],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )


def test_pytest_plugin_collects_console_expected_stderr_exit(tmp_path: Path) -> None:
    marker = tmp_path / "console-ran.txt"
    doc = write(
        tmp_path / "docs" / "console-error.md",
        f"""
        # Console Error

        ```console mustmatch exit=2 stream=stderr
        $ touch {shlex.quote(str(marker))} && mustmatch --bad-option
        Error: unknown option: --bad-option
        ```
        """,
    )

    result = run_pytest_doc(doc)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()


def test_pytest_plugin_named_run_expected_nonzero_uses_run_stream(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "run-ran.txt"
    doc = write(
        tmp_path / "docs" / "run-error.md",
        f"""
        # Run Error

        ```bash run id=bad-command exit=2 stream=stderr
        touch {shlex.quote(str(marker))}
        mustmatch --bad-option
        ```

        ```text expect=bad-command contains
        Error: unknown option: --bad-option
        ```
        """,
    )

    result = run_pytest_doc(doc)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
