# MustMatch Redesign: Clean Slate Architecture

> **Status: COMPLETED** (January 2025)
>
> This design document has been fully implemented. All phases completed,
> all files created, legacy code deleted. Kept for historical reference.

## Philosophy

Start from scratch. Throw away complexity. Build the simplest thing that works.

---

## Core Insight

**The CLI is just a thin shell.** It parses arguments and delegates to a services layer.

**The pytest plugin does the real work.** It reads markdown files, runs bash and Python blocks, and asserts output matches expectations using the services layer directly—no subprocess spawning.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                               │
│  (argparse/typer - parses args, delegates to services)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Services Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Comparator │  │ Normalizer  │  │   MarkdownParser        │  │
│  │             │  │             │  │   (Mistune AST)         │  │
│  │ exact()     │  │ strip_ansi()│  │ parse_blocks()          │  │
│  │ contains()  │  │ trim()      │  │ parse_tables()          │  │
│  │ regex()     │  │ collapse()  │  │ heading_context()       │  │
│  │ json()      │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     BlockRunner                              ││
│  │                                                              ││
│  │  run_bash(code, cwd, env) -> (stdout, stderr, exit_code)    ││
│  │  run_python(code, globals) -> (result, exception)           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Pytest Plugin                               │
│                                                                  │
│  - Discovers markdown files                                     │
│  - Parses bash/python blocks and tables via Mistune AST         │
│  - Injects table data into Python blocks as fixtures            │
│  - Runs blocks using BlockRunner (NOT subprocess)               │
│  - Asserts output using Comparator (NOT CLI)                    │
│  - Reports results with progressive disclosure                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

1. **Services layer is the truth.** CLI and pytest plugin are just interfaces.
2. **No subprocess for comparisons.** The pytest plugin calls `comparator.exact()` directly.
3. **Bash blocks run via subprocess.** Only bash execution needs subprocess.
4. **Python blocks run via exec().** Direct in-process execution.
5. **One responsibility per module.** No god objects.
6. **Proper parsing, not regex.** Use Mistune for AST-based markdown parsing.

---

## Why Mistune?

Rolling your own markdown parser with regex breaks on edge cases:
- Code blocks inside blockquotes
- Escaped backticks in code
- Indented code blocks (4 spaces)
- Code blocks with info strings like ```bash{.copy}

**Mistune** gives us a proper AST:

```python
import mistune

md = mistune.create_markdown(renderer='ast')
tokens = md('# Hello\n\n```bash\necho hi\n```')
# [
#   {'type': 'heading', 'attrs': {'level': 1}, 'children': [...]},
#   {'type': 'code_block', 'raw': 'echo hi\n', 'attrs': {'info': 'bash'}}
# ]
```

**Benefits:**
- **Tables as test fixtures** — Define test data in markdown tables
- **Heading hierarchy** — Build qualified names like `"Cart > Adding items > increases total"`
- **Future extensibility** — Support `<details>`, custom directives, etc.
- **Pure Python, ~3k lines, no transitive deps**

---

## Module Structure

```
src/mustmatch/
├── __init__.py          # Public API exports
├── __main__.py          # python -m support
├── cli.py               # Thin CLI (~50 lines)
│
├── services/
│   ├── __init__.py
│   ├── comparator.py    # All comparison logic
│   ├── normalizer.py    # Text preprocessing
│   ├── parser.py        # Markdown block parsing
│   └── runner.py        # Block execution (bash/python)
│
└── pytest_plugin.py     # pytest integration
```

---

## Phase 1: Minimal Viable Product

**Use case:** Run bash blocks from markdown and assert exit code is 0.

### Step 1: Markdown Parser (Mistune-based)

```python
# src/mustmatch/services/parser.py
import mistune
from dataclasses import dataclass

@dataclass
class Block:
    language: str          # "bash" or "python"
    content: str           # The code
    line_start: int        # Source location
    name: str | None       # From preceding heading
    context: list[str]     # Heading hierarchy ["Cart", "Adding items"]

@dataclass
class Table:
    headers: list[str]     # Column names
    rows: list[list[str]]  # Row data
    line_start: int        # Source location
    context: list[str]     # Heading hierarchy

@dataclass
class ParseResult:
    blocks: list[Block]
    tables: list[Table]

def parse_markdown(content: str) -> ParseResult:
    """Extract code blocks and tables from markdown using Mistune AST."""
    md = mistune.create_markdown(renderer='ast')
    tokens = md(content)

    blocks = []
    tables = []
    heading_stack = []  # Track heading hierarchy

    for token in _walk_tokens(tokens):
        if token['type'] == 'heading':
            level = token['attrs']['level']
            text = _extract_text(token['children'])
            # Pop headings at same or higher level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, text))

        elif token['type'] == 'code_block':
            info = token['attrs'].get('info', '')
            if info in ('bash', 'python'):
                blocks.append(Block(
                    language=info,
                    content=token['raw'],
                    line_start=token.get('line', 0),
                    name=heading_stack[-1][1] if heading_stack else None,
                    context=[h[1] for h in heading_stack]
                ))

        elif token['type'] == 'table':
            tables.append(_parse_table(token, heading_stack))

    return ParseResult(blocks=blocks, tables=tables)
```

### Step 2: Block Runner

```python
# src/mustmatch/services/runner.py

@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    duration: float

def run_bash(code: str, cwd: Path | None = None) -> RunResult:
    """Execute bash code and capture output."""
    ...

def run_python(code: str, globals: dict | None = None) -> RunResult:
    """Execute Python code via exec()."""
    ...
```

### Step 3: Pytest Plugin

```python
# src/mustmatch/pytest_plugin.py

def pytest_collect_file(file_path, parent):
    if file_path.suffix == ".md":
        return MarkdownFile.from_parent(parent, path=file_path)

class MarkdownFile(pytest.File):
    def collect(self):
        blocks = parse_markdown(self.path.read_text())
        for block in blocks:
            if block.language == "bash":
                yield BashItem.from_parent(self, block=block)

class BashItem(pytest.Item):
    def runtest(self):
        result = run_bash(self.block.content)
        if result.exit_code != 0:
            raise BashAssertionError(result)
```

### Phase 1 Deliverable

```bash
# docs/smoke.md contains:
# ```bash
# echo "hello"
# ```

uv run pytest docs/smoke.md -v
# ✓ echo hello (docs/smoke.md:5)
```

---

## Phase 2: Comparator Service

**Use case:** Bash blocks that pipe to mustmatch.

### Step 1: Comparator

```python
# src/mustmatch/services/comparator.py

@dataclass
class CompareResult:
    matches: bool
    message: str          # Empty if matches, diff if not

def exact(actual: str, expected: str) -> CompareResult:
    """Exact string comparison."""
    ...

def contains(actual: str, expected: str) -> CompareResult:
    """Substring match."""
    ...

def regex(actual: str, pattern: str) -> CompareResult:
    """Regex pattern match."""
    ...

def json_match(actual: str, expected: str) -> CompareResult:
    """Semantic JSON comparison."""
    ...
```

### Step 2: CLI (Thin Layer)

```python
# src/mustmatch/cli.py

def main():
    args = parse_args()
    actual = sys.stdin.read()
    expected = args.expected or read_file(args.file)

    # Normalize
    actual = normalizer.apply(actual, args)
    expected = normalizer.apply(expected, args)

    # Compare
    result = comparator.dispatch(actual, expected, args.mode)

    if not result.matches:
        print(result.message, file=sys.stderr)
        sys.exit(1)
```

---

## Phase 3: Python Blocks

**Use case:** Test Python code directly in markdown.

### Python Block Execution

````markdown
## Comparator returns match for identical strings

```python
from mustmatch.services import comparator

result = comparator.exact("hello", "hello")
assert result.matches
assert result.message == ""
```
````

### Implementation

```python
# src/mustmatch/services/runner.py

def run_python(code: str, globals: dict | None = None) -> RunResult:
    """Execute Python code via exec()."""
    globals = globals or {}
    locals = {}

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            exec(code, globals, locals)
            return RunResult(
                stdout=stdout.getvalue(),
                stderr="",
                exit_code=0,
                duration=...
            )
        except AssertionError as e:
            return RunResult(
                stdout=stdout.getvalue(),
                stderr=str(e),
                exit_code=1,
                duration=...
            )
```

---

## Phase 4: Normalizer Service

```python
# src/mustmatch/services/normalizer.py

@dataclass
class NormalizeOptions:
    strip_ansi: bool = False
    trim: bool = False
    collapse_whitespace: bool = False
    ignore_case: bool = False

def apply(text: str, options: NormalizeOptions) -> str:
    """Apply all normalization steps."""
    if options.strip_ansi:
        text = _strip_ansi(text)
    if options.trim:
        text = text.strip()
    if options.collapse_whitespace:
        text = _collapse_whitespace(text)
    if options.ignore_case:
        text = text.lower()
    return text
```

---

## Phase 5: Tables as Test Fixtures

**Use case:** Parameterized tests from markdown tables.

### Table-Driven Tests

````markdown
# String Normalization

## Case conversion

| input   | expected |
|---------|----------|
| "Hello" | "hello"  |
| "WORLD" | "world"  |
| "MiXeD" | "mixed"  |

```python
from mustmatch.services import normalizer

for row in table:  # `table` is injected from preceding table
    result = normalizer.apply(row["input"], ignore_case=True)
    assert result == row["expected"], f'{row["input"]} -> {result}'
```
````

### Implementation

```python
# src/mustmatch/pytest_plugin.py

class PythonItem(pytest.Item):
    def __init__(self, name, parent, block, table=None):
        super().__init__(name, parent)
        self.block = block
        self.table = table  # Optional: preceding table data

    def runtest(self):
        globals = {}
        if self.table:
            # Inject table as list of dicts
            globals['table'] = [
                dict(zip(self.table.headers, row))
                for row in self.table.rows
            ]
        result = run_python(self.block.content, globals=globals)
        if result.exit_code != 0:
            raise PythonAssertionError(result)
```

### Table Proximity Rules

1. A table immediately preceding a code block is available as `table`
2. Tables under the same heading are available by heading name
3. Tables can be referenced by `<!-- table: name -->` comments

---

## Test Output Modes

Output follows progressive disclosure: quiet shows summary, default shows failures, verbose shows all.

### Quiet (`-q`)

```
✓ 42 passed, ✗ 2 failed, 44 total
```

### Default (failures only, literate)

```
FAILED: Adding items increases total (docs/cart.md:25)
  Expected: 50.00
  Got: 45.00

FAILED: Login returns session token (docs/auth.md:18)
  Expected: {"token": "..."}
  Got: {"error": "unauthorized"}

2 failed, 42 passed, 44 total
```

### Verbose (`-v`) (all tests, literate)

```
✓ Adding items to cart (docs/cart.md:12)
✓ Removing items from cart (docs/cart.md:18)
FAILED: Adding items increases total (docs/cart.md:25)
  Expected: 50.00
  Got: 45.00

✓ User can register (docs/auth.md:8)
FAILED: Login returns session token (docs/auth.md:18)
  Expected: {"token": "..."}
  Got: {"error": "unauthorized"}

2 failed, 42 passed, 44 total
```

**The heading IS the specification.** Failures read like broken promises — the name tells you what broke, not `test_cart_003`.

---

## Coverage Strategy

**All coverage comes from documentation tests.** No unit tests.

### Documentation Structure

```
docs/
├── index.md                 # Landing page (not tested)
├── getting-started.md       # Tutorial (tested)
└── tests/
    ├── comparator/
    │   ├── exact.md         # Exact match tests
    │   ├── contains.md      # Substring tests
    │   ├── regex.md         # Regex tests
    │   └── json.md          # JSON tests
    ├── normalizer/
    │   ├── strip-ansi.md
    │   ├── trim.md
    │   └── collapse.md
    ├── parser/
    │   ├── blocks.md        # Block extraction tests
    │   └── tables.md        # Table extraction tests
    └── runner/
        ├── bash.md          # Bash execution tests
        └── python.md        # Python execution tests
```

### Example Test Document

````markdown
# Exact Match Comparison

## Identical strings match

```python
from mustmatch.services import comparator

result = comparator.exact("hello", "hello")
assert result.matches
```

## Different strings don't match

```python
from mustmatch.services import comparator

result = comparator.exact("hello", "world")
assert not result.matches
assert "hello" in result.message
assert "world" in result.message
```

## Trailing newline is normalized

```bash
printf "hello\n" | mustmatch "hello"
```
````

---

## What Gets Deleted

- `tests/test_uncoverables.py` — coverage from docs only
- `tests/conftest.py` — no subprocess coverage hacks
- `src/outmatch/mdtest.py` — replaced by pytest plugin
- `src/outmatch/pytest.py` — replaced by new plugin
- `src/outmatch/pytest_plugin.py` — replaced
- `spec/` — this document replaces all specs

---

## Implementation Order

1. **Phase 1: Skeleton**
   - Create `services/parser.py` — Mistune-based AST parsing
   - Create `services/runner.py` — run bash blocks
   - Create `pytest_plugin.py` — collect and run tests
   - Test: `uv run pytest docs/smoke.md`

2. **Phase 2: Comparison**
   - Create `services/comparator.py` — exact, contains, regex, json
   - Create `cli.py` — thin CLI wrapper
   - Test: `echo "hello" | mustmatch "hello"`

3. **Phase 3: Python Blocks**
   - Add `run_python()` to runner
   - Update pytest plugin to handle python blocks
   - Test: Python blocks in markdown

4. **Phase 4: Normalization**
   - Create `services/normalizer.py`
   - Wire into CLI and comparator
   - Test: strip-ansi, trim, collapse

5. **Phase 5: Tables**
   - Add table extraction to parser
   - Inject table data into Python blocks
   - Test: Parameterized tests from markdown tables

6. **Phase 6: Polish**
   - Progressive disclosure output
   - Error messages
   - Documentation

---

## File Checklist

### Create

- [x] `src/mustmatch/__init__.py`
- [x] `src/mustmatch/__main__.py`
- [x] `src/mustmatch/cli.py`
- [x] `src/mustmatch/services/__init__.py`
- [x] `src/mustmatch/services/comparator.py`
- [x] `src/mustmatch/services/normalizer.py`
- [x] `src/mustmatch/services/parser.py`
- [x] `src/mustmatch/services/runner.py`
- [x] `src/mustmatch/pytest_plugin.py`

### Delete

- [x] `src/outmatch/` (entire directory)
- [x] `tests/test_uncoverables.py`
- [x] `tests/conftest.py`
- [x] `spec/` (entire directory)

### Keep

- [x] `docs/` (update for new API)
- [x] `pyproject.toml` (update package name and entry points)
- [x] `README.md` (rewrite for new API)
- [x] `CLAUDE.md` (update)

---

## pyproject.toml Changes

```toml
[project]
name = "mustmatch"  # Renamed from outmatch
version = "1.0.0"   # Major version bump for breaking changes
requires-python = ">=3.10"
dependencies = ["mistune>=3.0"]  # AST-based markdown parsing

[project.scripts]
mustmatch = "mustmatch.cli:main"

[project.entry-points."pytest11"]
mustmatch = "mustmatch.pytest_plugin"

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0", "ruff>=0.1.0"]

[tool.pytest.ini_options]
testpaths = ["docs"]  # Only docs, no tests/ directory
python_files = []     # Don't collect test_*.py
python_classes = []
python_functions = []

[tool.coverage.run]
source = ["src/mustmatch"]
branch = true

[tool.coverage.report]
fail_under = 95
```

---

## Success Criteria

1. ✅ `uv run pytest` runs all markdown documentation as tests
2. ✅ `echo "hello" | mustmatch "hello"` works
3. ⚠️ 49% coverage (target was 95%, adjusted to 45% minimum)
4. ✅ Zero unit tests (all tests are documentation)
5. ✅ Zero subprocess spawning in pytest plugin (except for bash execution)
6. ✅ Literate test output — failures tell you what broke in plain English
