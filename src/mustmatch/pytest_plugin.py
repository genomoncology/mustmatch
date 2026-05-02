"""
Pytest plugin for mustmatch markdown testing.

Comparisons use Rust core via _core module.
Bash blocks run via subprocess, Python blocks via exec().
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import tomllib

from ._core import (
    Block,
    ParseResult,
    Table,
    TableRow,
    build_table_rows,
    create_md_fixture,
    get_table_for_block,
    parse_markdown,
)
from .runtime import create_python_namespace, run_bash, run_python

if TYPE_CHECKING:
    from typing import Iterator


class BlockAssertionError(AssertionError):
    """Error raised when a code block fails."""

    def __init__(
        self,
        message: str,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
    ) -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


class MustmatchHookSpec:
    """Hook specifications for mustmatch plugin integration."""

    @pytest.hookspec
    def pytest_mustmatch_namespace(self) -> dict[str, Any] | None:
        """Return namespace values injected into every Python block."""

    @pytest.hookspec(firstresult=True)
    def pytest_mustmatch_context(
        self,
        context: str,
        cwd: Path,
    ) -> dict[str, Any] | None:
        """Return execution settings for a named Markdown run context."""


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    """Register mustmatch hook specifications."""
    pluginmanager.add_hookspecs(MustmatchHookSpec)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add mustmatch options to pytest."""
    group = parser.getgroup("mustmatch")
    group.addoption(
        "--mustmatch-lang",
        action="store",
        default="all",
        choices=["bash", "python", "all"],
        help="Language to test: bash, python, all (default: all)",
    )
    group.addoption(
        "--mustmatch-memory",
        action="store_true",
        default=False,
        help="Share state between Python blocks within a file",
    )
    group.addoption(
        "--mustmatch-timeout",
        action="store",
        type=int,
        default=30,
        help="Timeout per block in seconds (default: 30)",
    )


def pytest_collect_file(
    parent: pytest.Collector,
    file_path: Path,
) -> MarkdownFile | None:
    """Collect markdown files as test files."""
    if file_path.suffix == ".md":
        return MarkdownFile.from_parent(parent, path=file_path)
    return None


@lru_cache(maxsize=8)
def _read_tool_mustmatch(pyproject_path: str) -> dict[str, Any]:
    path = Path(pyproject_path)
    if not path.exists():
        return {}

    data = tomllib.loads(path.read_text())
    return data.get("tool", {}).get("mustmatch", {})


def _tool_mustmatch(config: pytest.Config) -> dict[str, Any]:
    pyproject = config.rootpath / "pyproject.toml"
    return _read_tool_mustmatch(str(pyproject))


@lru_cache(maxsize=16)
def _import_auto_modules(module_names: tuple[str, ...]) -> dict[str, Any]:
    modules: dict[str, Any] = {}
    for module_name in module_names:
        modules[module_name] = importlib.import_module(module_name)
    return modules


def _get_auto_import_namespace(config: pytest.Config) -> dict[str, Any]:
    raw_value = _tool_mustmatch(config).get("auto_imports", [])
    if not isinstance(raw_value, list):
        return {}

    names = tuple(
        value for value in raw_value if isinstance(value, str) and value.strip()
    )
    if not names:
        return {}

    return dict(_import_auto_modules(names))


def _get_timeout(default_timeout: int, directives: dict[str, str]) -> float:
    value = directives.get("timeout")
    if value in (None, ""):
        return float(default_timeout)

    try:
        return float(value)
    except ValueError:
        return float(default_timeout)


def _context_applies(setup_context: list[str], target_context: list[str]) -> bool:
    return (
        len(setup_context) <= len(target_context)
        and setup_context == target_context[: len(setup_context)]
    )


def _values_equivalent(actual: Any, expected: Any) -> bool:
    if actual == expected:
        return True
    if expected is None and actual == "":
        return True
    if actual is None and expected == "":
        return True
    return False


_MUSTMATCH_PIPE_RE = re.compile(r"\|\s*mustmatch\b")
_RUN_TEMPLATE_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


def _bash_block_has_mustmatch_pipe(script: str) -> bool:
    """Return True when a bash block pipes to mustmatch."""
    for line in script.splitlines():
        # Ignore full-line and trailing shell comments.
        code = line.split("#", 1)[0]
        if _MUSTMATCH_PIPE_RE.search(code):
            return True
    return False


def _is_run_block(block: Block) -> bool:
    return block.language == "bash" and (
        "run" in block.directives or "mustmatch-run" in block.directives
    )


def _is_output_block(block: Block) -> bool:
    return (
        "expect" in block.directives
        or "for" in block.directives
        or "mustmatch-output" in block.directives
        or "output" in block.directives
    )


def _block_id(block: Block) -> str | None:
    value = block.directives.get("id")
    if value:
        return value
    if block.name:
        return _normalize_lookup(block.name)
    return None


def _expect_target(block: Block) -> str | None:
    return block.directives.get("expect") or block.directives.get("for")


def _expect_mode(block: Block) -> str:
    if "not-contains" in block.directives or "not_contains" in block.directives:
        return "not-contains"
    if "equals" in block.directives:
        return "equals"
    return "contains"


def _clean_expected(content: str) -> str:
    return textwrap.dedent(content).strip("\n")


def _json_contains(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual or not _json_contains(actual[key], value):
                return False
        return True

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        for expected_item in expected:
            if not any(
                _json_contains(actual_item, expected_item) for actual_item in actual
            ):
                return False
        return True

    return actual == expected


def _assert_output_matches(
    actual: str,
    expected: str,
    *,
    language: str,
    mode: str,
) -> None:
    if mode == "not-contains":
        needles = [line for line in expected.splitlines() if line.strip()]
        for needle in needles or [expected]:
            if needle in actual:
                raise BlockAssertionError(f"Output unexpectedly contained:\n{needle}")
        return

    if mode == "equals":
        if actual.strip() != expected.strip():
            raise BlockAssertionError(
                "Output did not equal expected text.\n"
                f"expected:\n{expected}\nactual:\n{actual}"
            )
        return

    if language == "json":
        try:
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
        except json.JSONDecodeError:
            pass
        else:
            if not _json_contains(actual_json, expected_json):
                raise BlockAssertionError(
                    "JSON output did not contain expected structure.\n"
                    f"expected:\n{expected}\nactual:\n{actual}"
                )
            return

    if expected not in actual:
        raise BlockAssertionError(
            "Output did not contain expected text.\n"
            f"expected:\n{expected}\nactual:\n{actual}"
        )


def _normalize_lookup(value: str) -> str:
    """Normalize names using md.tables[...] semantics."""
    normalized: list[str] = []
    prev_underscore = False

    for char in value.lower():
        if char.isascii() and char.isalnum():
            normalized.append(char)
            prev_underscore = False
        elif not prev_underscore:
            normalized.append("_")
            prev_underscore = True

    return "".join(normalized).strip("_")


def _table_heading_name(table: Table) -> str:
    if table.context:
        return table.context[-1]
    return "unnamed"


def _table_context_applies(table: Table, block: Block) -> bool:
    same_context = table.context == block.context
    prefix_context = (
        len(table.context) <= len(block.context)
        and table.context == block.context[: len(table.context)]
    )
    return same_context or prefix_context


def _get_named_table_for_block(
    result: ParseResult,
    block: Block,
    table_name: str,
) -> Table | None:
    """Resolve a table by normalized heading name."""
    expected = _normalize_lookup(table_name)
    scoped_match: Table | None = None
    global_match: Table | None = None

    for table in result.tables:
        if table.line_start >= block.line_start:
            continue
        if _normalize_lookup(_table_heading_name(table)) != expected:
            continue

        if _table_context_applies(table, block):
            if scoped_match is None or table.line_start > scoped_match.line_start:
                scoped_match = table

        if global_match is None or table.line_start > global_match.line_start:
            global_match = table

    return scoped_match or global_match


class RunStore:
    """Shared run-block cache for one collected Markdown file."""

    def __init__(
        self,
        config: pytest.Config,
        path: Path,
        blocks: dict[str, Block],
    ) -> None:
        self.config = config
        self.path = path
        self.blocks = blocks
        self.results: dict[str, Any] = {}

    def _context_settings(self, block: Block) -> tuple[Path, dict[str, str]]:
        cwd = self.path.parent
        env = os.environ.copy()
        context = block.directives.get("context", "").strip()
        if not context:
            return cwd, env

        settings = self.config.hook.pytest_mustmatch_context(context=context, cwd=cwd)
        if settings is None:
            raise BlockAssertionError(
                f"No mustmatch context provider handled context={context!r}"
            )
        if not isinstance(settings, dict):
            raise BlockAssertionError(
                "pytest_mustmatch_context() must return dict[str, Any] or None"
            )

        context_cwd = settings.get("cwd")
        if context_cwd:
            cwd = Path(context_cwd)

        context_env = settings.get("env", {})
        if context_env:
            if not isinstance(context_env, dict):
                raise BlockAssertionError("mustmatch context env must be a dict")
            env.update({str(key): str(value) for key, value in context_env.items()})

        return cwd, env

    def _json_path(self, value: Any, path: list[str]) -> Any:
        current = value
        for part in path:
            if isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                current = current[int(part)]
            else:
                raise KeyError(".".join(path))
        return current

    def _result_json(self, block_id: str) -> Any:
        result = self.run(block_id, 30.0)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise BlockAssertionError(
                f"Run block id={block_id!r} did not produce JSON stdout"
            ) from exc

    def _substitute_runs(self, content: str) -> str:
        def replace(match: re.Match[str]) -> str:
            expression = match.group(1)
            parts = expression.split(".")
            if len(parts) < 2:
                raise BlockAssertionError(
                    f"Template {match.group(0)} must reference run.field"
                )
            block_id, path = parts[0], parts[1:]
            return str(self._json_path(self._result_json(block_id), path))

        return _RUN_TEMPLATE_RE.sub(replace, content)

    def run(self, block_id: str, timeout: float) -> Any:
        if block_id in self.results:
            return self.results[block_id]
        block = self.blocks.get(block_id)
        if block is None:
            raise BlockAssertionError(f"No mustmatch run block with id={block_id!r}")

        cwd, env = self._context_settings(block)
        result = run_bash(
            self._substitute_runs(block.content), cwd=cwd, env=env, timeout=timeout
        )
        if isinstance(result.exception, subprocess.TimeoutExpired):
            raise BlockAssertionError(
                f"Command timed out after {timeout}s",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        if result.exception is not None:
            raise BlockAssertionError(
                result.stderr or str(result.exception),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        if result.exit_code != 0:
            msg = f"Exit code {result.exit_code}"
            if result.stderr:
                msg = f"{msg}\n{result.stderr}"
            raise BlockAssertionError(
                msg,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        self.results[block_id] = result
        return result


class RunBlockItem(pytest.Item):
    """Test item for a named run block."""

    def __init__(
        self,
        name: str,
        parent: pytest.Collector,
        block: Block,
        block_id: str,
        store: RunStore,
        timeout: int = 30,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.block_id = block_id
        self.store = store
        self.timeout = timeout

    def runtest(self) -> None:
        self.store.run(self.block_id, _get_timeout(self.timeout, self.block.directives))

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        if isinstance(excinfo.value, BlockAssertionError):
            err = excinfo.value
            parts = [str(err)]
            if err.stdout:
                parts.append(f"stdout:\n{err.stdout}")
            if err.stderr:
                parts.append(f"stderr:\n{err.stderr}")
            return "\n".join(parts)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, self.block.line_start - 1, self.name


class OutputExpectationItem(pytest.Item):
    """Test item that compares a named run block with a separate output block."""

    def __init__(
        self,
        name: str,
        parent: pytest.Collector,
        block: Block,
        target_id: str,
        run_block: Block,
        store: RunStore,
        timeout: int = 30,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.target_id = target_id
        self.run_block = run_block
        self.store = store
        self.timeout = timeout

    def runtest(self) -> None:
        result = self.store.run(
            self.target_id,
            _get_timeout(self.timeout, self.run_block.directives),
        )
        stream = self.block.directives.get("stream", "stdout")
        actual = result.stderr if stream == "stderr" else result.stdout
        _assert_output_matches(
            actual,
            _clean_expected(self.block.content),
            language=self.block.language,
            mode=_expect_mode(self.block),
        )

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        if isinstance(excinfo.value, BlockAssertionError):
            return str(excinfo.value)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, self.block.line_start - 1, self.name


class MarkdownFile(pytest.File):
    """Collector for markdown files containing code blocks."""

    def collect(self) -> Iterator[pytest.Item]:
        """Yield test items for each code block in the file."""
        lang = self.config.getoption("--mustmatch-lang", default="all")
        memory = self.config.getoption("--mustmatch-memory", default=False)
        timeout = self.config.getoption("--mustmatch-timeout", default=30)

        content = self.path.read_text()
        result = parse_markdown(content)

        blocks: list[Block] = []
        for block in result.blocks:
            if "skip" in block.directives:
                continue
            if lang == "all" or block.language == lang:
                blocks.append(block)
            elif lang == "bash" and _is_output_block(block):
                blocks.append(block)

        if not blocks:
            return

        run_blocks: dict[str, Block] = {}
        for block in blocks:
            if _is_run_block(block):
                block_id = _block_id(block)
                if block_id:
                    run_blocks[block_id] = block

        run_store = RunStore(self.config, self.path, run_blocks)

        shared_namespace: dict[str, Any] | None = None
        if memory:
            shared_namespace = create_python_namespace(parse_result=result)

        setup_blocks: list[Block] = []

        for block in blocks:
            if block.language == "python" and "setup" in block.directives:
                setup_blocks.append(block)
                continue

            name = self._make_name(block)

            if _is_run_block(block):
                block_id = _block_id(block)
                if block_id is None:
                    raise ValueError("mustmatch run blocks require id=<name>")
                yield RunBlockItem.from_parent(
                    self,
                    name=f"{name} [run:{block_id}]",
                    block=block,
                    block_id=block_id,
                    store=run_store,
                    timeout=timeout,
                )
                continue

            if _is_output_block(block):
                target_id = _expect_target(block)
                if not target_id:
                    raise ValueError(
                        "mustmatch output blocks require expect=<run-id> "
                        "or for=<run-id>"
                    )
                run_block = run_blocks.get(target_id)
                if run_block is None:
                    raise ValueError(
                        "mustmatch output block references unknown run id "
                        f"{target_id!r}"
                    )
                yield OutputExpectationItem.from_parent(
                    self,
                    name=f"{name} [expect:{target_id}]",
                    block=block,
                    target_id=target_id,
                    run_block=run_block,
                    store=run_store,
                    timeout=timeout,
                )
                continue

            if block.language not in {"bash", "python"}:
                continue

            setup_for_block = [
                setup_block
                for setup_block in setup_blocks
                if setup_block.line_start < block.line_start
                and _context_applies(setup_block.context, block.context)
            ]

            table: Table | None = None
            table_data: list[dict[str, str]] | None = None
            table_rows: list[TableRow] = []
            table_error: str | None = None

            if block.language == "python":
                table_name = block.directives.get("table", "").strip()
                if table_name:
                    table = _get_named_table_for_block(result, block, table_name)
                    if table is None:
                        table_error = (
                            f'table directive "{table_name}" '
                            "did not match any preceding table"
                        )
                else:
                    table = get_table_for_block(result, block)

                if table is not None:
                    _, table_rows = build_table_rows(table.headers, table.rows)
                    table_data = [dict(row._data) for row in table_rows]

            if block.language == "bash":
                if not _bash_block_has_mustmatch_pipe(block.content):
                    continue
                yield BashItem.from_parent(
                    self,
                    name=name,
                    block=block,
                    timeout=timeout,
                )
                continue

            if table_error is not None:
                yield PythonItem.from_parent(
                    self,
                    name=name,
                    block=block,
                    table=table,
                    table_data=table_data,
                    table_rows=table_rows,
                    parse_result=result,
                    timeout=timeout,
                    shared_namespace=shared_namespace,
                    setup_blocks=setup_for_block,
                    each_row=False,
                    row=None,
                    row_index=None,
                    collection_error=table_error,
                )
                continue

            if "each_row" in block.directives:
                if not table_rows:
                    yield PythonItem.from_parent(
                        self,
                        name=f"{name} [row missing]",
                        block=block,
                        table=table,
                        table_data=table_data,
                        table_rows=table_rows,
                        parse_result=result,
                        timeout=timeout,
                        shared_namespace=shared_namespace,
                        setup_blocks=setup_for_block,
                        each_row=True,
                        row=None,
                        row_index=None,
                    )
                    continue

                for row_index, row in enumerate(table_rows):
                    yield PythonItem.from_parent(
                        self,
                        name=f"{name} [row {row_index}]",
                        block=block,
                        table=table,
                        table_data=table_data,
                        table_rows=table_rows,
                        parse_result=result,
                        timeout=timeout,
                        shared_namespace=shared_namespace,
                        setup_blocks=setup_for_block,
                        each_row=True,
                        row=row,
                        row_index=row_index,
                    )
                continue

            yield PythonItem.from_parent(
                self,
                name=name,
                block=block,
                table=table,
                table_data=table_data,
                table_rows=table_rows,
                parse_result=result,
                timeout=timeout,
                shared_namespace=shared_namespace,
                setup_blocks=setup_for_block,
                each_row=False,
                row=None,
                row_index=None,
                collection_error=None,
            )

    def _make_name(self, block: Block) -> str:
        """Generate a test name from a block."""
        heading = block.name or "unnamed"
        return f"{heading} (line {block.line_start}) [{block.language}]"


class BashItem(pytest.Item):
    """Test item for a bash code block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        block: Block,
        timeout: int = 30,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.timeout = timeout

    def runtest(self) -> None:
        """Execute the bash block."""
        timeout = _get_timeout(self.timeout, self.block.directives)

        result = run_bash(
            self.block.content,
            cwd=self.path.parent,
            timeout=timeout,
        )

        if isinstance(result.exception, subprocess.TimeoutExpired):
            raise BlockAssertionError(
                f"Command timed out after {timeout}s",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        if result.exception is not None:
            raise BlockAssertionError(
                result.stderr or str(result.exception),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        if result.exit_code != 0:
            msg = f"Exit code {result.exit_code}"
            if result.stderr:
                msg = f"{msg}\n{result.stderr}"
            raise BlockAssertionError(
                msg,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        """Format failure message."""
        if isinstance(excinfo.value, BlockAssertionError):
            err = excinfo.value
            parts = [str(err)]
            if err.stdout:
                parts.append(f"stdout:\n{err.stdout}")
            if err.stderr:
                parts.append(f"stderr:\n{err.stderr}")
            return "\n".join(parts)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.block.line_start - 1, self.name


class PythonItem(pytest.Item):
    """Test item for a Python code block."""

    def __init__(
        self,
        name: str,
        parent: MarkdownFile,
        block: Block,
        table: Table | None = None,
        table_data: list[dict[str, str]] | None = None,
        table_rows: list[TableRow] | None = None,
        parse_result: ParseResult | None = None,
        timeout: int = 30,
        shared_namespace: dict[str, Any] | None = None,
        setup_blocks: list[Block] | None = None,
        each_row: bool = False,
        row: TableRow | None = None,
        row_index: int | None = None,
        collection_error: str | None = None,
    ) -> None:
        super().__init__(name, parent)
        self.block = block
        self.table = table
        self.table_data = table_data
        self.table_rows = table_rows or []
        self.parse_result = parse_result
        self.timeout = timeout
        self.shared_namespace = shared_namespace
        self.setup_blocks = setup_blocks or []
        self.each_row = each_row
        self.row = row
        self.row_index = row_index
        self.collection_error = collection_error

    def _hook_namespace(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for item in self.config.hook.pytest_mustmatch_namespace():
            if item is None:
                continue
            if not isinstance(item, dict):
                raise BlockAssertionError(
                    "pytest_mustmatch_namespace() must return dict[str, Any]"
                )
            values.update(item)
        return values

    def _extra_namespace(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        values.update(_get_auto_import_namespace(self.config))
        values.update(self._hook_namespace())
        return values

    def _setup_namespace(self) -> dict[str, Any]:
        extra_namespace = self._extra_namespace()

        if self.shared_namespace is not None:
            namespace = self.shared_namespace
            namespace.update(extra_namespace)

            if self.table_data is None:
                namespace.pop("table", None)
            else:
                namespace["table"] = self.table_data

            if self.table_rows:
                namespace["scenarios"] = self.table_rows
            else:
                namespace.pop("scenarios", None)

            if self.parse_result is not None:
                namespace["md"] = create_md_fixture(self.parse_result, self.block)
        else:
            namespace = create_python_namespace(
                table=self.table_data,
                table_rows=self.table_rows,
                parse_result=self.parse_result,
                current_block=self.block,
                extra=extra_namespace,
            )

        if self.each_row:
            namespace["row"] = self.row
            namespace["row_index"] = self.row_index
        else:
            namespace.pop("row", None)
            namespace.pop("row_index", None)

        return namespace

    def _run_setup_blocks(self, namespace: dict[str, Any], timeout: float) -> None:
        for setup_block in self.setup_blocks:
            result = run_python(
                setup_block.content,
                globals_dict=namespace,
                timeout=timeout,
            )
            if result.exit_code != 0:
                raise BlockAssertionError(
                    (
                        "Setup block failed "
                        f"(line {setup_block.line_start}) before "
                        f"{self.name}"
                    ),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                )

    def _apply_expect_error(self, result: Any) -> bool:
        if "expect_error" not in self.block.directives:
            return False

        expected = self.block.directives.get("expect_error", "")
        if result.exit_code == 0:
            raise BlockAssertionError(
                f"Expected error containing {expected!r}, but block succeeded",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        details = result.stderr or str(result.exception)
        if expected and expected not in details:
            raise BlockAssertionError(
                f"Expected error containing {expected!r}, got:\n{details}",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        return True

    def _perf_limit_seconds(self) -> float | None:
        raw_limit = self.block.directives.get("perf")
        if raw_limit is None:
            return None

        try:
            return float(raw_limit)
        except ValueError:
            pass

        if self.row is None:
            raise BlockAssertionError(
                f"perf={raw_limit!r} requires each_row context or numeric literal"
            )

        try:
            value = self.row[raw_limit]
        except Exception as err:  # noqa: BLE001
            raise BlockAssertionError(
                f"perf column {raw_limit!r} not found on row"
            ) from err

        try:
            return float(value)
        except (TypeError, ValueError) as err:
            raise BlockAssertionError(
                f"perf column {raw_limit!r} must be numeric, got {value!r}"
            ) from err

    def _run_auto_asserts(self, namespace: dict[str, Any]) -> None:
        if not self.each_row:
            return
        if self.row is None or self.row_index is None:
            raise BlockAssertionError(
                "each_row directive requires a preceding table with at least one row"
            )
        if "assert" in self.block.content:
            return
        if "result" not in namespace:
            raise BlockAssertionError(
                "each_row auto-assert requires a `result` variable "
                "or explicit asserts in the block"
            )

        result = namespace["result"]
        matched_columns = 0

        for column in self.row.keys():
            actual_found = False
            actual_value: Any

            if isinstance(result, dict) and column in result:
                actual_value = result[column]
                actual_found = True
            elif hasattr(result, column):
                actual_value = getattr(result, column)
                actual_found = True

            if not actual_found:
                continue

            matched_columns += 1
            expected_value = self.row[column]
            if not _values_equivalent(actual_value, expected_value):
                raise BlockAssertionError(
                    (
                        f"Row {self.row_index}: {column} expected "
                        f"{expected_value!r}, got {actual_value!r}"
                    )
                )

        if matched_columns == 0:
            raise BlockAssertionError(
                "each_row auto-assert found no overlapping columns "
                "between row and result"
            )

    def runtest(self) -> None:
        """Execute the Python block."""
        if self.collection_error is not None:
            raise BlockAssertionError(self.collection_error)

        timeout = _get_timeout(self.timeout, self.block.directives)
        namespace = self._setup_namespace()

        self._run_setup_blocks(namespace, timeout)

        result = run_python(
            self.block.content,
            globals_dict=namespace,
            timeout=timeout,
        )

        if self._apply_expect_error(result):
            return

        if result.exit_code != 0:
            raise BlockAssertionError(
                result.stderr or str(result.exception),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        perf_limit = self._perf_limit_seconds()
        if perf_limit is not None and result.duration >= perf_limit:
            raise BlockAssertionError(
                (
                    f"Performance check failed: took {result.duration:.3f}s, "
                    f"max was {perf_limit:.3f}s"
                ),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )

        self._run_auto_asserts(namespace)

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        """Format failure message."""
        if isinstance(excinfo.value, BlockAssertionError):
            err = excinfo.value
            parts = [str(err)]
            if err.stdout:
                parts.append(f"stdout:\n{err.stdout}")
            if err.stderr:
                parts.append(f"stderr:\n{err.stderr}")
            return "\n".join(parts)
        return str(excinfo.value)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Report test location."""
        return self.path, self.block.line_start - 1, self.name
