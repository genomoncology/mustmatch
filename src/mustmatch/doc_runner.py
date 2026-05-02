"""Documentation-first Markdown runner for mustmatch.

This module powers ``mustmatch test`` without requiring pytest. It understands the
same named run/output block style used by the pytest plugin, plus lightweight
context configuration from ``pyproject.toml``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib

from ._core import Block, get_table_for_block, parse_markdown
from .runtime import create_python_namespace, run_bash, run_python


class DocRunError(AssertionError):
    """A documentation block failed."""

    def __init__(
        self,
        message: str,
        *,
        stdout: str = "",
        stderr: str = "",
        exit_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


@dataclass
class DocTestCase:
    path: Path
    block: Block
    label: str
    kind: str


@dataclass
class DocTestSummary:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0


@dataclass
class ContextSettings:
    cwd: Path
    env: dict[str, str]


_RUN_DIRECTIVES = {"run", "mustmatch-run"}
_OUTPUT_DIRECTIVES = {"expect", "for", "mustmatch-output", "output"}
_TEMPLATE_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_MUSTMATCH_PIPE_RE = re.compile(r"\|\s*mustmatch\b")


def is_run_block(block: Block) -> bool:
    return block.language == "bash" and any(
        key in block.directives for key in _RUN_DIRECTIVES
    )


def is_output_block(block: Block) -> bool:
    return any(key in block.directives for key in _OUTPUT_DIRECTIVES)


def block_id(block: Block) -> str | None:
    value = block.directives.get("id")
    if value:
        return value
    if block.name:
        return normalize_lookup(block.name)
    return None


def expect_target(block: Block) -> str | None:
    return block.directives.get("expect") or block.directives.get("for")


def expect_mode(block: Block) -> str:
    if "not-contains" in block.directives or "not_contains" in block.directives:
        return "not-contains"
    if "equals" in block.directives:
        return "equals"
    return "contains"


def clean_expected(content: str) -> str:
    return content.strip("\n")


def normalize_lookup(value: str) -> str:
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


def bash_block_has_mustmatch_pipe(script: str) -> bool:
    for line in script.splitlines():
        code = line.split("#", 1)[0]
        if _MUSTMATCH_PIPE_RE.search(code):
            return True
    return False


def json_contains(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(
            key in actual and json_contains(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return all(
            any(json_contains(item, expected_item) for item in actual)
            for expected_item in expected
        )
    return actual == expected


def assert_output_matches(
    actual: str, expected: str, *, language: str, mode: str
) -> None:
    if mode == "not-contains":
        needles = [line for line in expected.splitlines() if line.strip()] or [expected]
        for needle in needles:
            if needle in actual:
                raise DocRunError(f"Output unexpectedly contained:\n{needle}")
        return

    if mode == "equals":
        if actual.strip() != expected.strip():
            raise DocRunError(
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
            if not json_contains(actual_json, expected_json):
                raise DocRunError(
                    "JSON output did not contain expected structure.\n"
                    f"expected:\n{expected}\nactual:\n{actual}"
                )
            return

    # Documentation-oriented multiline contains: every nonblank expected line
    # must occur somewhere in the actual output. This lets examples show context
    # without demanding exact adjacency when tables contain extra source rows.
    if "\n" in expected:
        missing = [
            line
            for line in expected.splitlines()
            if line.strip() and line not in actual
        ]
        if missing:
            joined = "\n".join(f"  - {line!r}" for line in missing)
            raise DocRunError(
                f"Output missed expected lines:\n{joined}\nactual:\n{actual}"
            )
        return

    if expected not in actual:
        raise DocRunError(
            "Output did not contain expected text.\n"
            f"expected:\n{expected}\nactual:\n{actual}"
        )


def find_pyproject(start: Path) -> Path | None:
    current = start.resolve() if start.is_dir() else start.resolve().parent
    for candidate in [current, *current.parents]:
        pyproject = candidate / "pyproject.toml"
        if pyproject.exists():
            return pyproject
    return None


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def substitute_env(value: str, env: dict[str, str], tokens: dict[str, str]) -> str:
    out = value
    for key, replacement in tokens.items():
        out = out.replace("{" + key + "}", replacement)
    return _ENV_RE.sub(lambda match: env.get(match.group(1), ""), out)


class ContextRegistry:
    """Resolve named run contexts from ``pyproject.toml``."""

    def __init__(self, root: Path, pyproject: Path | None) -> None:
        self.root = root
        self.pyproject = pyproject
        self.config = self._load_config(pyproject)
        self.cache: dict[str, ContextSettings] = {}
        self.tempdirs: list[tempfile.TemporaryDirectory[str]] = []

    def _load_config(self, pyproject: Path | None) -> dict[str, Any]:
        if pyproject is None or not pyproject.exists():
            return {}
        data = tomllib.loads(pyproject.read_text())
        tool = data.get("tool", {})
        if not isinstance(tool, dict):
            return {}
        mustmatch = tool.get("mustmatch", {})
        return mustmatch if isinstance(mustmatch, dict) else {}

    def resolve(self, name: str | None, default_cwd: Path) -> ContextSettings:
        if not name:
            return self._base_settings(default_cwd)
        if name in self.cache:
            return self.cache[name]

        contexts = self.config.get("contexts", {})
        config = contexts.get(name) if isinstance(contexts, dict) else None
        if not isinstance(config, dict):
            raise DocRunError(f"No mustmatch context named {name!r} in pyproject.toml")

        tmp = tempfile.TemporaryDirectory(prefix=f"mustmatch-{name}-")
        self.tempdirs.append(tmp)
        tmp_path = Path(tmp.name)
        tokens = {
            "root": str(self.root),
            "cwd": str(default_cwd),
            "tmp": str(tmp_path),
        }

        cwd_value = str(config.get("cwd", "."))
        cwd = Path(substitute_env(cwd_value, os.environ.copy(), tokens))
        if not cwd.is_absolute():
            cwd = self.root / cwd

        env = os.environ.copy()
        env_files = config.get("env_files", config.get("env_file", []))
        if isinstance(env_files, str):
            env_files = [env_files]
        if isinstance(env_files, list):
            for item in env_files:
                if not isinstance(item, str):
                    continue
                env_value = substitute_env(item, env, tokens).strip()
                if not env_value:
                    continue
                env_path = Path(env_value).expanduser()
                if not env_path.is_absolute():
                    env_path = self.root / env_path
                env.update(read_env_file(env_path))

        context_env = config.get("env", {})
        if isinstance(context_env, dict):
            for key, value in context_env.items():
                env[str(key)] = substitute_env(str(value), env, tokens)

        path_entries = config.get("path", [])
        if isinstance(path_entries, str):
            path_entries = [path_entries]
        if isinstance(path_entries, list) and path_entries:
            resolved_entries = []
            for item in path_entries:
                if not isinstance(item, str):
                    continue
                path = Path(substitute_env(item, env, tokens))
                if not path.is_absolute():
                    path = self.root / path
                resolved_entries.append(str(path))
            if resolved_entries:
                env["PATH"] = os.pathsep.join([*resolved_entries, env.get("PATH", "")])

        required_env = config.get("required_env", [])
        if isinstance(required_env, str):
            required_env = [required_env]
        missing = [
            key for key in required_env if isinstance(key, str) and not env.get(key)
        ]
        if missing:
            raise DocRunError(
                f"context {name!r} requires environment values: {', '.join(missing)}"
            )

        setup = config.get("setup", [])
        if isinstance(setup, str):
            setup = [setup]
        if isinstance(setup, list):
            for command in setup:
                if not isinstance(command, str) or not command.strip():
                    continue
                command = substitute_env(command, env, tokens)
                result = run_bash(
                    command,
                    cwd=cwd,
                    env=env,
                    timeout=float(config.get("setup_timeout", 120)),
                )
                if result.exit_code != 0:
                    raise DocRunError(
                        f"context {name!r} setup command failed: {command}",
                        stdout=result.stdout,
                        stderr=result.stderr,
                        exit_code=result.exit_code,
                    )

        settings = ContextSettings(cwd=cwd, env=env)
        self.cache[name] = settings
        return settings

    def _base_settings(self, default_cwd: Path) -> ContextSettings:
        env = os.environ.copy()
        path_entries = self.config.get("path", [])
        if isinstance(path_entries, str):
            path_entries = [path_entries]
        if isinstance(path_entries, list) and path_entries:
            resolved_entries = []
            for item in path_entries:
                if not isinstance(item, str):
                    continue
                path = Path(item).expanduser()
                if not path.is_absolute():
                    path = self.root / path
                resolved_entries.append(str(path))
            if resolved_entries:
                env["PATH"] = os.pathsep.join([*resolved_entries, env.get("PATH", "")])
        return ContextSettings(cwd=default_cwd, env=env)


class MarkdownRunner:
    def __init__(self, path: Path, *, lang: str = "all", timeout: int = 30) -> None:
        self.path = path
        self.lang = lang
        self.timeout = timeout
        self.content = path.read_text()
        self.parse_result = parse_markdown(self.content)
        pyproject = find_pyproject(path)
        root = pyproject.parent if pyproject else path.parent
        self.contexts = ContextRegistry(root, pyproject)
        self.run_blocks: dict[str, Block] = {}
        self.results: dict[str, Any] = {}
        for block in self.parse_result.blocks:
            if is_run_block(block):
                ident = block_id(block)
                if ident:
                    self.run_blocks[ident] = block

    def _timeout_for(self, block: Block) -> float:
        value = block.directives.get("timeout")
        if value:
            try:
                return float(value)
            except ValueError:
                pass
        return float(self.timeout)

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

    def _result_json(self, ident: str) -> Any:
        result = self.run_named(ident)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise DocRunError(f"run {ident!r} did not produce JSON stdout") from exc

    def substitute_runs(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            expr = match.group(1)
            parts = expr.split(".")
            if len(parts) < 2:
                raise DocRunError(f"template {match.group(0)} must reference run.field")
            ident, path = parts[0], parts[1:]
            value = self._json_path(self._result_json(ident), path)
            return str(value)

        return _TEMPLATE_RE.sub(replace, text)

    def run_named(self, ident: str) -> Any:
        if ident in self.results:
            return self.results[ident]
        block = self.run_blocks.get(ident)
        if block is None:
            raise DocRunError(f"unknown run id {ident!r}")
        context_name = block.directives.get("context", "").strip() or None
        settings = self.contexts.resolve(context_name, self.path.parent)
        content = self.substitute_runs(block.content)
        result = run_bash(
            content,
            cwd=settings.cwd,
            env=settings.env,
            timeout=self._timeout_for(block),
        )
        if result.exit_code != 0:
            raise DocRunError(
                f"run {ident!r} exited {result.exit_code}",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        self.results[ident] = result
        return result

    def run_block(self, block: Block) -> None:
        if "skip" in block.directives:
            raise SkipBlock
        if is_run_block(block):
            ident = block_id(block)
            if not ident:
                raise DocRunError("run blocks require id=<name>")
            self.run_named(ident)
            return
        if is_output_block(block):
            target = expect_target(block)
            if not target:
                raise DocRunError("output blocks require expect=<run-id>")
            result = self.run_named(target)
            stream = block.directives.get("stream", "stdout")
            actual = result.stderr if stream == "stderr" else result.stdout
            assert_output_matches(
                actual,
                clean_expected(block.content),
                language=block.language,
                mode=expect_mode(block),
            )
            return
        if block.language == "bash":
            if not bash_block_has_mustmatch_pipe(block.content):
                raise SkipBlock
            settings = self.contexts.resolve(
                block.directives.get("context"), self.path.parent
            )
            content = self.substitute_runs(block.content)
            result = run_bash(
                content,
                cwd=settings.cwd,
                env=settings.env,
                timeout=self._timeout_for(block),
            )
            if result.exit_code != 0:
                raise DocRunError(
                    f"bash block exited {result.exit_code}",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                )
            return
        if block.language == "python":
            table = get_table_for_block(self.parse_result, block)
            table_data = None
            if table is not None:
                table_data = [dict(zip(table.headers, row)) for row in table.rows]
            result = run_python(
                block.content,
                globals_dict=create_python_namespace(
                    table=table_data,
                    parse_result=self.parse_result,
                    current_block=block,
                ),
                timeout=self._timeout_for(block),
            )
            if result.exit_code != 0:
                raise DocRunError(
                    f"python block exited {result.exit_code}",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                )
            return
        raise SkipBlock

    def iter_cases(self) -> list[DocTestCase]:
        cases: list[DocTestCase] = []
        for block in self.parse_result.blocks:
            if self.lang != "all" and block.language != self.lang:
                if not (self.lang == "bash" and is_output_block(block)):
                    continue
            if block.language not in {"bash", "python", "json", "markdown", "text"}:
                continue
            if not (
                is_run_block(block)
                or is_output_block(block)
                or block.language in {"bash", "python"}
            ):
                continue
            heading = block.name or "unnamed"
            label = f"{heading} (line {block.line_start}) [{block.language}]"
            cases.append(DocTestCase(self.path, block, label, "block"))
        return cases


class SkipBlock(Exception):
    pass


def collect_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.md"))
    return sorted(set(files))


def run_markdown_tests(
    paths: list[Path],
    *,
    lang: str = "all",
    timeout: int = 30,
    verbose: bool = False,
    quiet: bool = False,
    fail_fast: bool = False,
) -> DocTestSummary:
    summary = DocTestSummary()
    files = collect_markdown_files(paths)
    if not files:
        if not quiet:
            print("No markdown files found", file=sys.stderr)
        return summary

    for file in files:
        runner = MarkdownRunner(file, lang=lang, timeout=timeout)
        for case in runner.iter_cases():
            try:
                runner.run_block(case.block)
            except SkipBlock:
                summary.skipped += 1
                if verbose:
                    print(f"SKIP {case.label}")
                continue
            except DocRunError as exc:
                summary.failed += 1
                message = f"FAIL {case.label}: {exc}"
                summary.failures.append(message)
                if not quiet:
                    print(message, file=sys.stderr)
                    if verbose and exc.stdout:
                        print(f"stdout:\n{exc.stdout}", file=sys.stderr)
                    if verbose and exc.stderr:
                        print(f"stderr:\n{exc.stderr}", file=sys.stderr)
                if fail_fast:
                    return summary
            else:
                summary.passed += 1
                if verbose:
                    print(f"PASS {case.label}")

    return summary
