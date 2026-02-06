# mustmatch

CLI assertion utility and pytest plugin for executable Markdown.

## Build And Test

```bash
uv sync --extra dev
uv run pytest
uv run pytest --cov
uv run ruff check src
```

## Project Structure

```text
mustmatch/
├── src/mustmatch/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── pytest_plugin.py
│   ├── version.py
│   └── services/
│       ├── comparator.py
│       ├── fixture.py
│       ├── normalizer.py
│       ├── parser.py
│       └── runner.py
├── docs/
│   ├── index.md
│   ├── quick-start.md
│   ├── comparison-modes.md
│   ├── normalization.md
│   ├── examples.md
│   ├── writing-test-documents.md
│   ├── fixture.md
│   ├── each-row.md
│   ├── conventions.md
│   ├── error-handling.md
│   ├── json-subset.md
│   └── jsonl.md
└── pyproject.toml
```

## Plugin Features

- Collects `.md` files as pytest tests
- Executes `bash`, `sh`, and `python` code blocks
- Supports directives: `skip`, `timeout`, `each_row`, `setup`, `expect_error`, `perf`
- Provides `md` fixture for section/table access
- Supports optional namespace injection via `pytest_mustmatch_namespace`

## Version

Current: **0.0.2**
