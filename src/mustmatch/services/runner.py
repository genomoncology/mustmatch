"""
Block runner for executing bash and Python code.

Bash blocks run via subprocess, Python blocks run via exec().
"""

from __future__ import annotations

import io
import subprocess
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunResult:
    """Result of executing a code block."""

    stdout: str
    stderr: str
    exit_code: int
    duration: float
    exception: Exception | None = None


def run_bash(
    code: str,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> RunResult:
    """Execute bash code and capture output.

    Args:
        code: Bash code to execute.
        cwd: Working directory (defaults to current directory).
        env: Environment variables (defaults to current environment).
        timeout: Timeout in seconds (defaults to no timeout).

    Returns:
        RunResult with stdout, stderr, exit_code, and duration.
    """
    start = time.perf_counter()
    bash_code = f"set -e\n{code}"

    try:
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
        duration = time.perf_counter() - start

        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            duration=duration,
        )
    except subprocess.TimeoutExpired as e:
        duration = time.perf_counter() - start
        return RunResult(
            stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
            stderr=e.stderr or "" if isinstance(e.stderr, str) else "",
            exit_code=-1,
            duration=duration,
            exception=e,
        )
    except Exception as e:
        duration = time.perf_counter() - start
        return RunResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            duration=duration,
            exception=e,
        )


def run_python(
    code: str,
    *,
    globals_dict: dict[str, Any] | None = None,
    locals_dict: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> RunResult:
    """Execute Python code via exec().

    Args:
        code: Python code to execute.
        globals_dict: Global namespace (will be modified in place).
        locals_dict: Local namespace (optional, defaults to globals_dict).

    Returns:
        RunResult with stdout, stderr (from exception), exit_code, and duration.
    """
    if globals_dict is None:
        globals_dict = {"__builtins__": __builtins__}
    if locals_dict is None:
        locals_dict = globals_dict

    class _RunPythonTimeout(Exception):
        pass

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    start = time.perf_counter()

    timer_enabled = False
    old_handler: Any | None = None
    if timeout is not None:
        try:
            import signal

            def _handle_timeout(signum: int, frame: Any) -> None:  # noqa: ARG001
                raise _RunPythonTimeout

            old_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            timer_enabled = True
        except Exception:
            timer_enabled = False
            old_handler = None

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, globals_dict, locals_dict)
        duration = time.perf_counter() - start

        return RunResult(
            stdout=stdout_capture.getvalue(),
            stderr=stderr_capture.getvalue(),
            exit_code=0,
            duration=duration,
        )
    except _RunPythonTimeout as e:
        duration = time.perf_counter() - start
        return RunResult(
            stdout=stdout_capture.getvalue(),
            stderr=f"Timed out after {timeout}s",
            exit_code=-1,
            duration=duration,
            exception=e,
        )
    except AssertionError as e:
        duration = time.perf_counter() - start
        # Format assertion error with traceback
        tb = traceback.format_exc()
        return RunResult(
            stdout=stdout_capture.getvalue(),
            stderr=tb,
            exit_code=1,
            duration=duration,
            exception=e,
        )
    except Exception as e:
        duration = time.perf_counter() - start
        tb = traceback.format_exc()
        return RunResult(
            stdout=stdout_capture.getvalue(),
            stderr=tb,
            exit_code=1,
            duration=duration,
            exception=e,
        )
    finally:
        if timer_enabled:
            import signal

            signal.setitimer(signal.ITIMER_REAL, 0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)


def create_python_namespace(
    *,
    table: list[dict[str, str]] | None = None,
    parse_result: Any | None = None,
    current_block: Any | None = None,
) -> dict[str, Any]:
    """Create a namespace for Python code execution.

    Args:
        table: Optional table data to inject as 'table' variable.
        parse_result: Optional ParseResult to create 'md' fixture.
        current_block: Optional current Block for context.

    Returns:
        A namespace dictionary ready for exec().
    """
    namespace: dict[str, Any] = {"__builtins__": __builtins__}

    if table is not None:
        namespace["table"] = table

    if parse_result is not None:
        from .fixture import create_md_fixture
        namespace["md"] = create_md_fixture(parse_result, current_block)

    return namespace
