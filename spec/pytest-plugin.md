# Spec: outmatch pytest Plugin

**Phase 3: Native PyTest Integration**

---

## Overview

The `outmatch` pytest plugin enables native pytest integration for testing markdown documentation. It provides better integration than mktestdocs with fixtures, markers, coverage, and parallel execution.

**Design goals:**
1. **Native pytest**: Full pytest ecosystem integration
2. **Coverage**: Track code covered by documentation examples
3. **Fixtures**: Use pytest fixtures in bash blocks
4. **DX**: Better error messages, IDE integration, debugging

---

## Installation

```bash
# Plugin is included with outmatch
pip install outmatch

# Or with all dev dependencies
pip install "outmatch[dev]"
```

**Auto-discovery:** Plugin registers automatically via entry point.

---

## Basic Usage

### Minimal Configuration

```python
# tests/test_docs.py
from pathlib import Path
import pytest
from outmatch.pytest import MarkdownTest

# Collect all markdown files
DOCS_DIR = Path(__file__).parent.parent / "docs"
tests = list(MarkdownTest.discover(DOCS_DIR))

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_markdown(test):
    """Run bash blocks from markdown documentation."""
    test.run()
```

**That's it.** Now:
```bash
pytest tests/test_docs.py        # Run doc tests
pytest --cov=mypackage tests/    # With coverage
pytest tests/test_docs.py::test_markdown[docs/cli.md:23]  # Single block
```

---

## API Reference

### `MarkdownTest` Class

```python
class MarkdownTest:
    """Represents a single bash block from markdown."""

    # Attributes
    file: Path              # Markdown file path
    line: int               # Starting line number
    content: str            # Bash block content
    name: str               # Block name (from heading or comment)
    id: str                 # Unique test ID (file:line)

    # Methods
    @classmethod
    def discover(
        cls,
        path: Path,
        *,
        pattern: str = "**/*.md",
        exclude: list[str] | None = None,
    ) -> Iterator[MarkdownTest]:
        """Discover all bash blocks in markdown files."""

    def run(
        self,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Execute the bash block.

        Raises:
            AssertionError: If block fails
            TimeoutError: If execution exceeds timeout
        """

    def run_with_fixture(self, fixture_value: Any) -> None:
        """Execute block with access to pytest fixture."""
```

---

## Pytest Integration

### Test Discovery

**Automatic via parametrize:**

```python
import pytest
from outmatch.pytest import MarkdownTest

# Discover all docs
tests = list(MarkdownTest.discover("docs/"))

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_docs(test):
    test.run()
```

**Pytest sees:**
```
tests/test_docs.py::test_docs[docs/cli.md:23]
tests/test_docs.py::test_docs[docs/cli.md:45]
tests/test_docs.py::test_docs[docs/api.md:67]
...
```

### Test Selection

```bash
# Run all doc tests
pytest tests/test_docs.py

# Run specific file's tests
pytest tests/test_docs.py -k "cli.md"

# Run specific block
pytest tests/test_docs.py::test_docs[docs/cli.md:45]

# Run tests matching pattern
pytest tests/test_docs.py -k "quickstart"
```

---

## Fixtures Integration

### Passing Fixtures to Bash Blocks

**Via environment variables:**

```python
import pytest
from outmatch.pytest import MarkdownTest

@pytest.fixture
def test_db(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    # Setup database
    create_test_db(db_path)
    yield db_path
    # Cleanup happens automatically

tests = list(MarkdownTest.discover("docs/"))

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_docs(test, test_db):
    """Run docs with test database available."""
    test.run(env={"TEST_DB": str(test_db)})
```

**In markdown:**
````markdown
```bash
# Use the test database
mycli query --db "$TEST_DB" "SELECT * FROM users" \
  | outmatch --jsonl-contains '{"name": "alice"}'
```
````

### Fixture-Based Setup/Teardown

```python
import pytest
from outmatch.pytest import MarkdownTest

@pytest.fixture(scope="module")
def test_server():
    """Start test server for all doc tests."""
    server = start_test_server(port=8080)
    yield "http://localhost:8080"
    server.stop()

tests = list(MarkdownTest.discover("docs/api/"))

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_api_docs(test, test_server):
    test.run(env={"API_URL": test_server})
```

### Complex Fixtures

```python
@pytest.fixture
def api_client(test_server):
    """Authenticated API client."""
    token = login(test_server, "testuser", "password")
    return {"url": test_server, "token": token}

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_api_docs(test, api_client):
    test.run(env={
        "API_URL": api_client["url"],
        "API_TOKEN": api_client["token"],
    })
```

---

## Markers Integration

### Standard Markers

```python
import pytest
from outmatch.pytest import MarkdownTest

# Collect tests
cli_tests = list(MarkdownTest.discover("docs/cli/"))
api_tests = list(MarkdownTest.discover("docs/api/"))

@pytest.mark.slow
@pytest.mark.parametrize("test", cli_tests, ids=lambda t: t.id)
def test_cli_docs(test):
    """CLI docs are slow (build required)."""
    test.run()

@pytest.mark.integration
@pytest.mark.parametrize("test", api_tests, ids=lambda t: t.id)
def test_api_docs(test, test_server):
    """API docs need test server."""
    test.run(env={"API_URL": test_server})
```

**Run marked tests:**
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m integration          # Only integration tests
pytest -m "not (slow or integration)"  # Skip both
```

### Custom Markers

```python
import pytest

@pytest.mark.requires_docker
@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_docs(test):
    test.run()
```

**Register in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
markers = [
    "requires_docker: Tests that need Docker",
    "slow: Slow-running tests",
]
```

### Conditional Skip

```python
import pytest
import shutil

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_cli_docs(test):
    # Skip if CLI not installed
    if not shutil.which("mycli"):
        pytest.skip("mycli not installed")

    test.run()
```

---

## Coverage Integration

### Basic Coverage

```bash
# Run tests with coverage
pytest --cov=mypackage tests/

# Coverage includes both unit tests AND doc tests
```

**Coverage report shows:**
```
Name                    Stmts   Miss  Cover
-------------------------------------------
mypackage/cli.py           50      2    96%
mypackage/core.py         120      8    93%
-------------------------------------------
TOTAL                     170     10    94%
```

### Coverage Analysis

```bash
# HTML report
pytest --cov=mypackage --cov-report=html tests/

# See which lines are hit by docs vs unit tests
open htmlcov/index.html
```

**Coverage context tracking:**

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
coverage_context = "test"
```

Shows which tests hit which lines.

### Doc-Only Coverage

```bash
# Only run doc tests to see "real usage" coverage
pytest --cov=mypackage tests/test_docs.py

# Compare to unit test coverage
pytest --cov=mypackage tests/test_unit.py
```

**Use case:** Find functions with unit tests but no documentation examples.

---

## Parallel Execution

### pytest-xdist Integration

```bash
# Install
pip install pytest-xdist

# Run in parallel
pytest -n 4 tests/test_docs.py

# Auto-detect CPU count
pytest -n auto tests/
```

**Performance:**
- 100 doc tests in ~5 seconds (4 workers)
- Each worker gets isolated environment
- No shared state between workers

### Controlling Parallelism

```python
# Mark tests that must run sequentially
import pytest

@pytest.mark.xdist_group("database")
@pytest.mark.parametrize("test", db_tests, ids=lambda t: t.id)
def test_db_docs(test, test_db):
    """These tests share a database, run sequentially."""
    test.run(env={"DB": str(test_db)})
```

---

## Configuration

### via `pyproject.toml`

```toml
[tool.pytest.ini_options]
# Test discovery
testpaths = ["tests", "docs"]
python_files = ["test_*.py", "*_test.py"]

# Markers
markers = [
    "docs: Documentation tests",
    "slow: Slow-running tests",
]

# Coverage
[tool.coverage.run]
source = ["mypackage"]
parallel = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]

# Outmatch-specific
[tool.outmatch.pytest]
timeout = 30
parallel = 4
env = { NO_COLOR = "1", CI = "1" }
```

### via `pytest.ini`

```ini
[pytest]
testpaths = tests docs
markers =
    docs: Documentation tests
    slow: Slow-running tests

[outmatch]
timeout = 30
parallel = 4
```

---

## Advanced Patterns

### Conditional Fixtures

```python
import pytest

@pytest.fixture
def api_client(request):
    """Only start API client if test needs it."""
    if "api" not in request.node.name:
        pytest.skip("Not an API test")

    client = APIClient()
    yield client
    client.close()

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_docs(test, api_client):
    test.run(env={"API_URL": api_client.url})
```

### Test Categorization

```python
import pytest
from pathlib import Path
from outmatch.pytest import MarkdownTest

# Separate test functions for different categories
cli_tests = list(MarkdownTest.discover("docs/cli/"))
api_tests = list(MarkdownTest.discover("docs/api/"))
guides = list(MarkdownTest.discover("docs/guides/"))

@pytest.mark.cli
@pytest.mark.parametrize("test", cli_tests, ids=lambda t: t.id)
def test_cli(test):
    test.run()

@pytest.mark.api
@pytest.mark.parametrize("test", api_tests, ids=lambda t: t.id)
def test_api(test, api_server):
    test.run(env={"API_URL": api_server})

@pytest.mark.guides
@pytest.mark.parametrize("test", guides, ids=lambda t: t.id)
def test_guides(test):
    test.run()
```

**Usage:**
```bash
pytest -m cli              # Only CLI tests
pytest -m api              # Only API tests
pytest -m "not guides"     # Skip guides
```

### Shared State Across Blocks

```python
import pytest

@pytest.fixture(scope="module")
def shared_state():
    """State shared across all doc tests in a module."""
    return {"counter": 0}

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_docs(test, shared_state):
    # Pass state via environment
    test.run(env={"COUNTER": str(shared_state["counter"])})
    shared_state["counter"] += 1
```

---

## Error Reporting

### Pytest Native Output

```
FAILED tests/test_docs.py::test_docs[docs/cli.md:45] - AssertionError: Command failed

docs/cli.md:45-52 (Help text)

Command:
  findterms --help | outmatch --contains "Usage:"

Expected (contains):
  Usage:

Actual:
  findterms - Fast term extraction

  USAGE:
    findterms [OPTIONS] <COMMAND>

Error: Substring not found
```

**Benefits:**
- Familiar pytest format
- Shows file and line number
- Includes test name
- Shows full diff

### IDE Integration

**Works in VS Code, PyCharm, etc:**
- Click on failure → jumps to markdown file and line
- Run individual test from IDE
- Debug with breakpoints
- Rerun failed tests

---

## Migration from mktestdocs

### Before (mktestdocs)

```python
# tests/test_docs.py
import pytest
from pathlib import Path
from mktestdocs import check_md_file

DOCS = Path(__file__).parent.parent / "docs"

@pytest.mark.parametrize("md_file", DOCS.rglob("*.md"), ids=str)
def test_python_docs(md_file):
    """Test Python blocks."""
    check_md_file(md_file, lang="python")

@pytest.mark.parametrize("md_file", DOCS.rglob("*.md"), ids=str)
def test_bash_docs(md_file):
    """Test bash blocks."""
    check_md_file(md_file, lang="bash")
```

**Issues:**
- Two test functions for two languages
- No fixture support
- No per-block reporting
- Poor error messages

### After (outmatch plugin)

```python
# tests/test_docs.py
import pytest
from pathlib import Path
from outmatch.pytest import MarkdownTest

DOCS = Path(__file__).parent.parent / "docs"

# Python blocks (unchanged, use mktestdocs)
@pytest.mark.parametrize("md_file", DOCS.rglob("*.md"), ids=str)
def test_python_docs(md_file):
    check_md_file(md_file, lang="python")

# Bash blocks (use outmatch)
bash_tests = list(MarkdownTest.discover(DOCS))

@pytest.mark.parametrize("test", bash_tests, ids=lambda t: t.id)
def test_bash_docs(test):
    test.run()
```

**Benefits:**
- Per-block test reporting
- Better error messages
- Fixture support
- Coverage integration

---

## Implementation Details

### Plugin Architecture

```python
# outmatch/pytest.py

from pathlib import Path
from typing import Iterator, Any
import subprocess

class MarkdownTest:
    """A single bash block from markdown."""

    def __init__(
        self,
        file: Path,
        line: int,
        content: str,
        name: str,
    ):
        self.file = file
        self.line = line
        self.content = content
        self.name = name

    @property
    def id(self) -> str:
        """Unique test ID for pytest."""
        return f"{self.file}:{self.line}"

    @classmethod
    def discover(
        cls,
        path: Path,
        *,
        pattern: str = "**/*.md",
        exclude: list[str] | None = None,
    ) -> Iterator["MarkdownTest"]:
        """Discover bash blocks in markdown files."""
        # Find all markdown files
        files = sorted(path.glob(pattern))

        # Parse each file
        for file in files:
            if exclude and any(e in str(file) for e in exclude):
                continue

            yield from cls._parse_file(file)

    @classmethod
    def _parse_file(cls, file: Path) -> Iterator["MarkdownTest"]:
        """Parse markdown file and yield bash blocks."""
        content = file.read_text()
        lines = content.split("\n")

        in_bash_block = False
        block_start = 0
        block_content = []
        block_name = "Unnamed block"

        for i, line in enumerate(lines, 1):
            # Detect bash block start
            if line.strip() in ("```bash", "```sh", "```shell"):
                in_bash_block = True
                block_start = i + 1
                block_content = []
                # Look for preceding heading
                block_name = cls._find_block_name(lines, i)

            # Detect bash block end
            elif line.strip() == "```" and in_bash_block:
                in_bash_block = False
                yield cls(
                    file=file,
                    line=block_start,
                    content="\n".join(block_content),
                    name=block_name,
                )

            # Accumulate block content
            elif in_bash_block:
                block_content.append(line)

    def run(
        self,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Execute bash block."""
        import os

        # Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Execute
        proc = subprocess.run(
            ["bash", "-e", "-u", "-c", self.content],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=exec_env,
            cwd=cwd,
        )

        # Check result
        if proc.returncode != 0:
            error_msg = f"{self.file}:{self.line} ({self.name})\n\n"
            error_msg += f"Command:\n{self.content}\n\n"
            if proc.stdout:
                error_msg += f"Stdout:\n{proc.stdout}\n\n"
            if proc.stderr:
                error_msg += f"Stderr:\n{proc.stderr}\n"
            raise AssertionError(error_msg)
```

### Pytest Registration

```python
# setup.py or pyproject.toml
[project.entry-points."pytest11"]
outmatch = "outmatch.pytest_plugin"
```

**Auto-discovery:** Pytest automatically loads the plugin.

---

## Testing the Plugin

**Self-hosted:** Use the plugin to test itself.

```python
# tests/test_plugin.py
import pytest
from outmatch.pytest import MarkdownTest

tests = list(MarkdownTest.discover("docs/"))

@pytest.mark.parametrize("test", tests, ids=lambda t: t.id)
def test_plugin_docs(test):
    """Test the plugin using itself."""
    test.run()
```

**Coverage target:** 100% of plugin code covered by its own tests.

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Discovery | < 100ms for 1000 blocks |
| Per-block overhead | < 50ms |
| Parallel scaling | Linear up to 8 workers |
| Memory per block | < 5MB |

---

## Examples

### Full Integration Example

```python
# tests/test_docs.py
"""Test all documentation examples."""
import pytest
from pathlib import Path
from outmatch.pytest import MarkdownTest

# Find docs
DOCS_DIR = Path(__file__).parent.parent / "docs"

# Fixtures
@pytest.fixture(scope="session")
def test_db(tmp_path_factory):
    """Shared test database."""
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    create_test_db(db_path)
    return db_path

@pytest.fixture(scope="session")
def api_server():
    """Test API server."""
    server = start_server(port=8080)
    yield "http://localhost:8080"
    server.stop()

# Discover tests
cli_tests = list(MarkdownTest.discover(DOCS_DIR / "cli"))
api_tests = list(MarkdownTest.discover(DOCS_DIR / "api"))

# CLI tests
@pytest.mark.cli
@pytest.mark.parametrize("test", cli_tests, ids=lambda t: t.id)
def test_cli_docs(test, test_db):
    """Test CLI documentation."""
    test.run(env={"TEST_DB": str(test_db)})

# API tests
@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize("test", api_tests, ids=lambda t: t.id)
def test_api_docs(test, api_server):
    """Test API documentation."""
    test.run(env={"API_URL": api_server})
```

**Usage:**
```bash
# All tests
pytest tests/test_docs.py

# With coverage
pytest --cov=mypackage tests/

# Parallel
pytest -n 4 tests/test_docs.py

# Only CLI tests
pytest -m cli tests/test_docs.py

# Skip integration tests
pytest -m "not integration" tests/test_docs.py
```

---

## Success Metrics

After Phase 3 implementation:

1. **Adoption:** Used in FindTerms and BotAssembly
2. **Coverage:** Doc tests contribute to >80% code coverage
3. **DX:** Developers prefer plugin over mktestdocs
4. **Speed:** 100 doc tests run in < 5 seconds with `-n 4`
5. **Integration:** Works seamlessly with existing pytest suites
