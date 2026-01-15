# MustMatch: CLI Assertions & Documentation Testing

**Objective:** Rename outmatch to mustmatch and merge mktestdocs Python execution capabilities to create a unified assertion tool for both DevOps scripts and documentation testing.

---

## Rationale

### Naming
`mustmatch` reads naturally as English in pipes:

```bash
findterms --version | mustmatch "0.1.0"
mytool export | mustmatch --json '{"status": "ok"}'
```

Compare to `outmatch` which reads awkwardly.

### Unified Tooling
Currently testing documentation requires two dependencies:
- **outmatch** - CLI output assertions, bash block testing
- **mktestdocs** - Python code block testing with memory/state

Merging eliminates the mktestdocs dependency and provides a single, memorable tool:
- One package to install
- One API to learn
- Full control over implementation

---

## Use Cases

### 1. DevOps & Script Assertions

`mustmatch` is `assert` for shell scripts. Use it anywhere you need to fail fast if output doesn't match expectations:

```bash
#!/bin/bash
set -e

# Deployment script - bail if service isn't healthy
curl -s localhost:8080/health | mustmatch --json '{"status": "healthy"}'

# CI pipeline - verify build output
./build.sh | mustmatch --contains "BUILD SUCCESSFUL"

# Infrastructure check - verify config
kubectl get configmap myapp -o json | mustmatch --json-contains '{"replicas": 3}'

# Version gate - ensure minimum version
python --version 2>&1 | mustmatch --regex "Python 3\.(1[0-9]|[2-9][0-9])"
```

**Key properties for DevOps:**
- Exit 0 on match, exit 1 on mismatch (standard Unix convention)
- No output on success (quiet by default in pipes)
- Clear diff output on failure for debugging
- Works with any command that produces stdout

```bash
# Use in conditionals
if echo "$response" | mustmatch --contains "error" -q; then
    echo "Error detected, rolling back..."
    rollback
fi

# Use with set -e (fail the script)
set -e
deploy_service
curl -s localhost/health | mustmatch '{"status":"ok"}'
echo "Deployment verified"
```

### 2. Documentation Testing

Test that code examples in your docs actually work:

```bash
# Run all bash blocks in docs/
mustmatch test docs/

# Run Python examples with state sharing
mustmatch test --lang python --memory docs/

# Integrate with pytest
pytest docs/  # Auto-discovers markdown files
```

### 3. Inline Test Assertions

Use in bash blocks within documentation to make examples self-verifying:

````markdown
## API Response Format

The `/users` endpoint returns JSON:

```bash
curl -s localhost:8080/users/1 | mustmatch --json '{
  "id": 1,
  "name": "alice",
  "email": "alice@example.com"
}'
```
````

When you run `mustmatch test docs/`, this block executes and verifies the API actually returns that structure.

---

## Current State Analysis

### outmatch Has (Keep)

| Feature | Implementation |
|---------|----------------|
| CLI pipe mode | `echo "x" \| outmatch "x"` |
| Comparison modes | exact, contains, regex, json, jsonl, jsonl-set, jsonl-key |
| Normalization | strip-ansi, trim, collapse-whitespace, ignore-case |
| Pattern transforms | --replace, --redact, --json-ignore |
| Bash markdown testing | `outmatch test docs/` via `mdtest.py` |
| Pytest plugin | Auto-discovers .md files, runs bash blocks |
| Block metadata | `<!-- outmatch: skip -->`, timeout, env |
| Output formats | JUnit XML, JSON, TAP |
| Exec mode | `outmatch exec --exit-code 0 -- cmd` |

### mktestdocs Has (Merge In)

| Feature | Implementation |
|---------|----------------|
| Python code execution | `exec(code, namespace)` |
| Memory mode | Concatenate blocks, run together (state sharing) |
| Docstring testing | `check_docstring(obj)` |
| Custom executors | `register_executor(lang, func)` |
| Language filtering | `check_md_file(path, lang="python")` |

---

## Implementation Plan

### Phase 1: Rename (Low Risk)

1. **Package rename**: `outmatch` → `mustmatch`
   - Update `pyproject.toml`: name, entry points
   - Rename `src/outmatch/` → `src/mustmatch/`
   - Update all internal imports
   - Update CLI help text and version output
   - Update README and docs

2. **Backward compatibility** (optional):
   - Keep `outmatch` as deprecated alias for one version
   - Or clean break (recommended for new project)

### Phase 2: Add Python Execution

#### 2.1 Extend Parsing (`parsing.py`)

Add Python fence detection alongside bash:

```python
# Current
BASH_FENCES = frozenset({"```bash", "```sh", "```shell"})

# Extended
PYTHON_FENCES = frozenset({"```python", "```py"})
SUPPORTED_LANGS = {
    "bash": BASH_FENCES,
    "python": PYTHON_FENCES,
}
```

Modify `ParsedBlock` to include language:

```python
@dataclass
class ParsedBlock:
    content: str
    line_start: int
    line_end: int
    name: str | None = None
    lang: str = "bash"  # NEW: "bash" | "python"
```

#### 2.2 Add Python Executor (`python_exec.py`)

New module for Python execution:

```python
"""Python code execution for markdown testing."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class PythonResult:
    """Result of Python execution."""
    success: bool
    error: str | None = None
    exception: BaseException | None = None


def execute_python(
    code: str,
    namespace: dict[str, Any] | None = None,
    filename: str = "<markdown>",
) -> PythonResult:
    """Execute Python code in a namespace.

    Args:
        code: Python source code to execute.
        namespace: Optional namespace dict. If None, creates fresh namespace.
        filename: Filename for error reporting.

    Returns:
        PythonResult with success status and any error.
    """
    if namespace is None:
        namespace = {"__name__": "__main__"}

    try:
        exec(compile(code, filename, "exec"), namespace)
        return PythonResult(success=True)
    except Exception as e:
        return PythonResult(
            success=False,
            error=f"{type(e).__name__}: {e}",
            exception=e,
        )


def execute_python_blocks(
    blocks: list[str],
    memory: bool = False,
    filename: str = "<markdown>",
) -> list[PythonResult]:
    """Execute multiple Python blocks.

    Args:
        blocks: List of code block contents.
        memory: If True, blocks share namespace (state persists).
                If False, each block gets fresh namespace.
        filename: Filename for error reporting.

    Returns:
        List of results, one per block.
    """
    if memory:
        # Concatenate and run as one unit
        combined = "\n\n".join(blocks)
        result = execute_python(combined, filename=filename)
        # Return same result for each block position
        return [result] * len(blocks)
    else:
        # Run each independently
        return [
            execute_python(block, filename=filename)
            for block in blocks
        ]
```

#### 2.3 Extend mdtest.py

Add language parameter and Python support:

```python
@dataclass
class RunConfig:
    # ... existing fields ...
    lang: str = "bash"  # NEW: "bash" | "python" | "all"
    memory: bool = False  # NEW: for Python state sharing


def run_file(path: Path, config: RunConfig) -> FileResult:
    """Test all blocks in a markdown file."""
    content = path.read_text()

    if config.lang == "python":
        blocks = list(parse_python_blocks(content))
        return run_python_file(path, blocks, config)
    elif config.lang == "bash":
        blocks = parse_markdown(content)
        return run_bash_file(path, blocks, config)
    else:  # "all"
        # Run both, aggregate results
        ...
```

#### 2.4 CLI Updates (`cli.py`)

Add `--lang` and `--memory` flags to test command:

```python
@test_app.callback(invoke_without_command=True)
def _test_callback(
    # ... existing params ...
    lang: Annotated[
        str,
        typer.Option(help="Language to test: bash, python, all"),
    ] = "bash",
    memory: Annotated[
        bool,
        typer.Option(help="Share state between Python blocks"),
    ] = False,
) -> None:
    """Run code blocks in markdown files as tests."""
```

New commands:

```bash
# Test bash (default, backward compatible)
mustmatch test docs/

# Test Python blocks
mustmatch test --lang python docs/

# Test Python with memory (state sharing)
mustmatch test --lang python --memory docs/

# Test all languages
mustmatch test --lang all docs/
```

### Phase 3: Pytest Integration

#### 3.1 Update pytest_plugin.py

Support both languages in collection:

```python
class MarkdownFile(pytest.File):
    def collect(self) -> Iterator[MarkdownItem]:
        content = self.path.read_text()

        # Collect bash blocks
        for block in parse_bash_blocks(content):
            yield BashItem.from_parent(self, block=block)

        # Collect python blocks
        for block in parse_python_blocks(content):
            yield PythonItem.from_parent(self, block=block)


class PythonItem(pytest.Item):
    """Test item for a Python code block."""

    def runtest(self) -> None:
        result = execute_python(
            self.block.content,
            filename=f"{self.path}:{self.block.line_start}",
        )
        if not result.success:
            raise AssertionError(result.error)
```

#### 3.2 Memory Mode in Pytest

For `memory=True`, need special handling since pytest runs items independently.
Options:

**Option A: File-level test** (simpler)
```python
class MarkdownFileTest(pytest.Item):
    """Run all Python blocks in file with shared state."""

    def runtest(self) -> None:
        blocks = list(parse_python_blocks(self.path.read_text()))
        results = execute_python_blocks(
            [b.content for b in blocks],
            memory=True,
            filename=str(self.path),
        )
        # Report first failure
        for i, result in enumerate(results):
            if not result.success:
                raise AssertionError(
                    f"Block at line {blocks[i].line_start}: {result.error}"
                )
```

**Option B: pytest fixture** (more pytest-native)
```python
@pytest.fixture(scope="module")
def python_namespace():
    """Shared namespace for Python blocks in a file."""
    return {"__name__": "__main__"}
```

Recommend **Option A** for simplicity - matches mktestdocs behavior.

### Phase 4: API Surface

#### 4.1 Public API (`__init__.py`)

```python
from mustmatch.mdtest import run_tests, RunConfig
from mustmatch.python_exec import execute_python, execute_python_blocks
from mustmatch.compare import compare
from mustmatch.pytest import MarkdownTest

# Convenience function matching mktestdocs API
def check_md_file(
    fpath: Path,
    lang: str = "python",
    memory: bool = True,
) -> None:
    """Test code blocks in a markdown file.

    Raises AssertionError on failure. For pytest parametrization.

    Args:
        fpath: Path to markdown file.
        lang: Language to test ("python", "bash", "all").
        memory: If True, Python blocks share state.
    """
    ...

__all__ = [
    "check_md_file",
    "execute_python",
    "compare",
    "run_tests",
    "RunConfig",
    "MarkdownTest",
]
```

#### 4.2 Usage Pattern (mktestdocs compatible)

```python
# tests/test_docs.py
import pytest
from pathlib import Path
from mustmatch import check_md_file

DOCS = sorted(Path("docs").glob("**/*.md"))

@pytest.mark.parametrize("fpath", DOCS, ids=lambda p: p.name)
def test_python_examples(fpath):
    check_md_file(fpath, lang="python", memory=True)

@pytest.mark.parametrize("fpath", DOCS, ids=lambda p: p.name)
def test_bash_examples(fpath):
    check_md_file(fpath, lang="bash")
```

---

## Migration Guide

### For Users

**Before (two packages):**
```bash
pip install outmatch mktestdocs
```

```python
# tests/test_docs.py
from mktestdocs import check_md_file  # Python
from outmatch.pytest import MarkdownTest  # Bash
```

**After (one package):**
```bash
pip install mustmatch
```

```python
# tests/test_docs.py
from mustmatch import check_md_file  # Both languages
```

### For Existing outmatch Users

1. Replace `pip install outmatch` with `pip install mustmatch`
2. Replace `from outmatch` imports with `from mustmatch`
3. Replace CLI `outmatch` with `mustmatch`
4. No behavioral changes for bash testing

---

## Block Metadata Extension

Extend directive syntax for Python-specific options:

```markdown
<!-- mustmatch: lang=python memory -->
```python
x = 1
```

<!-- mustmatch: skip-if=CI -->
```python
# Interactive code
```
```

---

## Testing Strategy

### Unit Tests
- Python execution with/without memory
- Block parsing for both languages
- Error formatting and line number reporting

### Integration Tests
- Full markdown files with mixed bash/python
- Memory mode state persistence
- Pytest plugin collection and execution

### Dogfooding
- Test mustmatch's own docs with mustmatch
- Validate README examples work

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Python exec() security | Document that test code runs with full privileges (same as mktestdocs) |
| Memory mode complexity | Default to memory=False; opt-in for state sharing |
| Breaking changes | Semantic versioning; optional backward compat aliases |
| Scope creep | Focus on mktestdocs parity first; defer docstring testing |

---

## Out of Scope (Future)

1. **Docstring testing** (`check_docstring`) - Defer unless needed
2. **Custom executor registry** - Defer; only bash+python for now
3. **Language auto-detection** - Explicit `--lang` is clearer
4. **Jupyter notebook support** - Different beast entirely

---

## Implementation Order

1. **Rename to mustmatch** (1-2 hours)
   - Package rename, imports, CLI, docs

2. **Add Python parsing** (1 hour)
   - Extend parsing.py for Python fences
   - Add lang field to ParsedBlock

3. **Add Python executor** (2 hours)
   - New python_exec.py module
   - Unit tests for exec with/without memory

4. **Integrate into mdtest** (2 hours)
   - Add --lang and --memory to CLI
   - Wire up Python execution path

5. **Update pytest plugin** (2 hours)
   - Support Python blocks in collection
   - Handle memory mode

6. **Add check_md_file API** (1 hour)
   - mktestdocs-compatible convenience function

7. **Documentation** (2 hours)
   - Update README
   - Migration guide
   - Examples

**Total: ~12 hours**

---

## Success Criteria

- [ ] `mustmatch test --lang python docs/` runs Python blocks
- [ ] `mustmatch test --lang python --memory docs/` shares state
- [ ] Pytest auto-discovers and runs Python blocks
- [ ] `check_md_file(path, lang="python", memory=True)` works
- [ ] All existing bash tests continue to work unchanged
- [ ] README is self-documenting (tests itself)
