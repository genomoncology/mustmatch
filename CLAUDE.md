# mustmatch

**CLI output assertion tool for documentation testing**

---

## Build & Test

```bash
uv sync --extra dev    # Install dependencies
uv run pytest          # Run tests
uv run pytest --cov    # With coverage
uv run ruff check src tests  # Lint
```

---

## Project Structure

```
mustmatch/
├── src/mustmatch/      # Package source
│   ├── __init__.py        # Main module exports
│   ├── __main__.py        # python -m support
│   ├── cli.py             # CLI interface
│   ├── mdtest.py          # Markdown test runner
│   ├── python_exec.py     # Python execution
│   └── pytest_plugin.py   # pytest integration
├── tests/                 # Test suite
│   └── test_uncoverables.py   # Unit tests
├── docs/                  # Documentation
│   └── *.md               # Usage guides
└── pyproject.toml         # Package config
```

---

## API

### CLI Usage

```bash
# Exact match
echo "hello" | mustmatch "hello"

# Contains substring
cmd --help | mustmatch --contains "Usage:"

# JSON semantic (field order independent)
echo '{"b": 2, "a": 1}' | mustmatch --json '{"a": 1, "b": 2}'

# Test markdown docs (bash blocks)
mustmatch test docs/

# Test Python blocks with memory
mustmatch test --lang python --memory docs/
```

### Exit Codes

- `0` - Match
- `1` - Mismatch
- `2` - Invalid arguments

---

## Documentation Testing

Uses pytest to test itself. Tests are in `tests/test_uncoverables.py`.

To run: `uv run pytest -v`

---

## Code Quality

- **Linting**: ruff
- **Testing**: pytest with coverage
- **CI**: GitHub Actions (test on Python 3.10-3.13)

---

## Version

Current: **0.0.0.dev0**
