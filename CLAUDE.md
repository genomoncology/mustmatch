# mustmatch

CLI assertion utility and pytest plugin for executable Markdown.

## Build And Test

```bash
uv sync --extra dev --reinstall-package mustmatch
uv run python -m pytest docs/ README.md -q
uv run python -m coverage run -m pytest docs/ README.md -q
uv run ruff check src
```

## Project Structure

```text
mustmatch/
├── crates/
│   ├── mustmatch-core/     # Rust core: parser, comparator, normalizer, coercion, fixture
│   ├── mustmatch-python/   # PyO3 bindings exposing mustmatch._core
│   └── mustmatch-cli/      # Standalone Rust CLI binary
├── src/mustmatch/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # Python CLI (match + test subcommands)
│   ├── runtime.py          # Bash/Python block execution
│   ├── pytest_plugin.py    # pytest collector for .md files
│   └── version.py
├── docs/                   # Executable documentation (pytest tests)
│   ├── index.md
│   ├── 01-overview.md
│   ├── 02-cli-assertions.md
│   ├── 03-executable-documents.md
│   ├── 04-fixtures-and-tables.md
│   ├── 05-directives.md
│   ├── 06-comparison-modes.md
│   ├── 07-normalization.md
│   ├── 08-configuration.md
│   └── 09-examples.md
├── bench/                  # CLI benchmark commands
└── pyproject.toml          # Package config (maturin build)
```

## Plugin Features

- Collects `.md` files as pytest tests
- Executes `bash`, `sh`, and `python` code blocks
- Supports directives: `skip`, `timeout`, `each_row`, `setup`, `expect_error`, `perf`
- Provides `md` fixture for section/table access
- Supports optional namespace injection via `pytest_mustmatch_namespace`

## Version

Current: **0.0.4**
