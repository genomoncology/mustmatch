from __future__ import annotations

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
