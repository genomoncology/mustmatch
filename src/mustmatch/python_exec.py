"""Python code execution for markdown testing.

Execute Python code blocks from markdown documentation with optional
state sharing (memory mode) between blocks.
"""

from __future__ import annotations

import io
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any


def create_namespace() -> dict[str, Any]:
    """Create a fresh Python namespace for code execution.

    Returns:
        A dict with __name__ and __builtins__ set for exec().
    """
    return {"__name__": "__main__", "__builtins__": __builtins__}


@dataclass
class PythonResult:
    """Result of Python execution."""

    success: bool
    output: str = ""  # Captured stdout
    error: str | None = None
    exception: BaseException | None = None


def execute_python(
    code: str,
    namespace: dict[str, Any] | None = None,
    filename: str = "<markdown>",
) -> tuple[PythonResult, dict[str, Any]]:
    """Execute Python code in a namespace.

    Args:
        code: Python source code to execute.
        namespace: Optional namespace dict. If None, creates fresh namespace.
        filename: Filename for error reporting.

    Returns:
        Tuple of (PythonResult, namespace) where namespace may be modified.
    """
    if namespace is None:
        namespace = create_namespace()

    # Capture stdout
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        compiled = compile(code, filename, "exec")
        exec(compiled, namespace)
        output = captured_output.getvalue()
        return PythonResult(success=True, output=output), namespace
    except SyntaxError as e:
        # Format syntax error nicely
        output = captured_output.getvalue()
        error_msg = f"SyntaxError: {e.msg}"
        if e.lineno:
            error_msg += f" (line {e.lineno})"
        return PythonResult(
            success=False,
            output=output,
            error=error_msg,
            exception=e,
        ), namespace
    except Exception as e:
        # Format other exceptions with traceback
        output = captured_output.getvalue()
        # Get the traceback, skip internal frames
        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        # Filter out internal frames (from exec/compile)
        filtered_tb = []
        skip_next = False
        for line in tb_lines:
            if 'File "<markdown>"' in line or 'File "<string>"' in line:
                skip_next = False
                filtered_tb.append(line)
            elif skip_next:
                continue
            elif "exec(compiled, namespace)" in line:
                skip_next = True
                continue
            else:
                filtered_tb.append(line)

        error_msg = "".join(filtered_tb).strip()
        return PythonResult(
            success=False,
            output=output,
            error=error_msg,
            exception=e,
        ), namespace
    finally:
        sys.stdout = old_stdout


@dataclass
class PythonBlockResult:
    """Result of executing a single Python block."""

    block_index: int
    line_start: int
    success: bool
    output: str = ""
    error: str | None = None


@dataclass
class PythonFileResult:
    """Result of executing Python blocks in a file."""

    blocks: list[PythonBlockResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for b in self.blocks if b.success)

    @property
    def failed(self) -> int:
        return sum(1 for b in self.blocks if not b.success)

    @property
    def success(self) -> bool:
        return all(b.success for b in self.blocks)


def execute_python_blocks(
    blocks: list[tuple[str, int]],  # List of (code, line_number) tuples
    memory: bool = False,
    filename: str = "<markdown>",
) -> PythonFileResult:
    """Execute multiple Python blocks.

    Args:
        blocks: List of (code, line_number) tuples.
        memory: If True, blocks share namespace (state persists).
                If False, each block gets fresh namespace.
        filename: Filename for error reporting.

    Returns:
        PythonFileResult with results for each block.
    """
    result = PythonFileResult()

    if not blocks:
        return result

    # In memory mode, share namespace; otherwise use None (fresh each time)
    namespace: dict[str, Any] | None = create_namespace() if memory else None

    for i, (code, line_num) in enumerate(blocks):
        block_filename = f"{filename}:{line_num}"
        exec_result, updated_namespace = execute_python(code, namespace, block_filename)

        result.blocks.append(PythonBlockResult(
            block_index=i,
            line_start=line_num,
            success=exec_result.success,
            output=exec_result.output,
            error=exec_result.error,
        ))

        # In memory mode, preserve namespace and stop on failure
        if memory:
            namespace = updated_namespace
            if not exec_result.success:
                break

    return result
