# Refactoring Plan: doctest-expect

## Goals

1. Decompose the monolithic `__init__.py` (800+ lines) into focused modules
2. Decompose the large `main()` function into smaller, testable pieces
3. Use Typer for CLI (modern, type-hint based, better than argparse)
4. Use dataclasses for configuration and results
5. Replace unit tests with self-hosted doctests (eat our own dogfood)
6. Achieve 100% coverage using doctest-expect itself
7. Follow Python best practices (max 88 char lines, focused modules)

## New Package Structure

```
src/doctest_expect/
├── __init__.py          # Public API exports only
├── __main__.py          # Entry point: from .cli import app; app()
├── cli.py               # Typer CLI definition (~100 lines)
├── config.py            # Dataclasses for options (~50 lines)
├── compare.py           # All comparison functions (~200 lines)
├── normalize.py         # Preprocessing/normalization (~80 lines)
├── json_utils.py        # JSON/JSONL helpers (~80 lines)
├── output.py            # Diff formatting and colors (~60 lines)
└── version.py           # Version constant
```

## Module Responsibilities

### version.py
- Single `__version__` constant
- No dependencies

### config.py
- `NormalizeOptions` dataclass: strip_ansi, normalize_newlines, trim, etc.
- `CompareMode` enum: EXACT, CONTAINS, REGEX, JSON, JSONL, etc.
- `ExpectConfig` dataclass: mode, normalize_opts, json_ignore, quiet, color, etc.
- `CompareResult` dataclass: success, message

### normalize.py
- `strip_ansi(text) -> str`
- `normalize_newlines(text) -> str`
- `collapse_whitespace(text) -> str`
- `apply_replacements(text, replacements) -> str`
- `apply_redactions(text, patterns) -> str`
- `preprocess(text, options: NormalizeOptions) -> str`

### json_utils.py
- `normalize_json(obj) -> Any`
- `parse_jsonl(text) -> list[Any]`
- `remove_json_paths(obj, paths) -> Any`

### compare.py
- `compare_exact(actual, expected) -> CompareResult`
- `compare_contains(actual, expected) -> CompareResult`
- `compare_regex(actual, expected) -> CompareResult`
- `compare_json(actual, expected, ignore_paths) -> CompareResult`
- `compare_jsonl(actual, expected, ignore_paths) -> CompareResult`
- `compare_jsonl_set(actual, expected, ignore_paths) -> CompareResult`
- `compare_jsonl_key(actual, expected, key_field, ignore_paths) -> CompareResult`
- `compare_jsonl_contains(actual, expected, ignore_paths) -> CompareResult`
- `compare(actual, expected, config: ExpectConfig) -> CompareResult` (dispatcher)

### output.py
- `unified_diff(actual, expected, context) -> str`
- `colorize_diff(diff, use_color) -> str`
- `format_error(result: CompareResult, config: ExpectConfig) -> str`

### cli.py
- Typer app with all options organized into option groups
- `expect()` command function that:
  1. Reads stdin
  2. Gets expected from arg or file
  3. Builds config from options
  4. Calls preprocess on both
  5. Calls compare dispatcher
  6. Handles output/update mode
  7. Returns exit code

### __init__.py
- Export public API only:
  - `__version__`
  - `main(args)` - for backwards compatibility
  - `compare`, `preprocess` - for library use

## Typer CLI Design

```python
import typer
from typing import Annotated, Optional
from enum import Enum

app = typer.Typer(help="Assert CLI output matches expected value")

class ColorChoice(str, Enum):
    auto = "auto"
    always = "always"
    never = "never"

@app.command()
def expect(
    expected: Annotated[Optional[str], typer.Argument()] = None,
    expected_file: Annotated[Optional[Path], typer.Option("-f")] = None,
    # Comparison modes
    contains: Annotated[bool, typer.Option()] = False,
    regex: Annotated[bool, typer.Option()] = False,
    json_mode: Annotated[bool, typer.Option("--json")] = False,
    jsonl: Annotated[bool, typer.Option()] = False,
    jsonl_set: Annotated[bool, typer.Option()] = False,
    jsonl_key: Annotated[Optional[str], typer.Option()] = None,
    jsonl_contains: Annotated[bool, typer.Option()] = False,
    # Normalization
    strip_ansi: Annotated[bool, typer.Option()] = False,
    # ... etc
):
    ...
```

## Testing Strategy: Self-Hosted Doctests

Replace all unit tests with documentation that uses doctest-expect itself.

### Test Structure

```
docs/
├── index.md
├── getting-started.md
├── cli/
│   └── reference.md
└── tests/           # New: executable test documentation
    ├── exact.md
    ├── contains.md
    ├── regex.md
    ├── json.md
    ├── jsonl.md
    ├── normalize.md
    ├── transform.md
    ├── files.md
    └── errors.md
```

### Example Test Document (docs/tests/exact.md)

```markdown
# Exact Match Tests

## Basic exact match

```bash
echo "hello world" | expect "hello world"
```

## Trailing newline normalization

```bash
printf "hello world\n" | expect "hello world"
```

## Multi-line exact match

```bash
printf "line one\nline two" | expect "line one
line two"
```

## Mismatch returns exit code 1

```bash
echo "hello" | expect "world" || echo "failed as expected"
```
```

### Test Runner

Use pytest + mktestdocs to execute all markdown files:

```python
# tests/test_docs.py
import pytest
from mktestdocs import check_md_file
from pathlib import Path

DOCS = Path(__file__).parent.parent / "docs"

@pytest.mark.parametrize("md_file", DOCS.rglob("*.md"))
def test_docs(md_file):
    check_md_file(md_file)
```

### Coverage Strategy

To achieve 100% coverage:

1. Each comparison mode gets its own test document with:
   - Happy path tests
   - Edge cases
   - Error cases (using `|| true` or checking exit codes)

2. Each normalization option tested in combination

3. File operations tested with temp files

4. Error paths tested by intentionally triggering them

5. Use `coverage run` with the test documents

## Implementation Order

1. Create `version.py` with version constant
2. Create `config.py` with dataclasses
3. Create `normalize.py` with preprocessing functions
4. Create `json_utils.py` with JSON helpers
5. Create `compare.py` with comparison functions
6. Create `output.py` with formatting functions
7. Create `cli.py` with Typer app
8. Update `__init__.py` to export public API
9. Update `__main__.py` to use new CLI
10. Create test documents under `docs/tests/`
11. Update `tests/test_docs.py` to run doc tests
12. Delete old `tests/test_expect.py`
13. Run coverage and fill gaps
14. Update README and other docs

## Dependencies to Add

```toml
[project]
dependencies = [
    "typer>=0.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
    "mktestdocs>=0.2.0",
]
```

## Line Length and Style

- Max line length: 88 (black default)
- Use ruff for formatting and linting
- Type hints on all public functions
- Docstrings on all public functions
- No function over 30 lines
- No module over 200 lines
