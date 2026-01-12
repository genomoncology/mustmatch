# outmatch

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
outmatch/
├── src/outmatch/       # Package source
│   ├── __init__.py        # Main module (all logic here)
│   └── __main__.py        # python -m support
├── tests/                 # Test suite
│   └── test_coverage.py   # Unit tests
├── docs/                  # Documentation
│   └── usage.md           # Usage guide
└── pyproject.toml         # Package config
```

---

## API

### CLI Usage

```bash
# Exact match
echo "hello" | outmatch "hello"

# Contains substring
cmd --help | outmatch --contains "Usage:"

# JSONL semantic (field order independent)
echo '{"b": 2, "a": 1}' | outmatch --jsonl '{"a": 1, "b": 2}'

# JSONL contains (subset match)
cat data.jsonl | outmatch --jsonl-contains '{"id": 1}'
```

### Exit Codes

- `0` - Match
- `1` - Mismatch
- `2` - Invalid arguments

---

## Documentation Testing

Uses pytest to test itself. Tests are in `tests/test_coverage.py`.

To run: `uv run pytest -v`

---

## Code Quality

- **Linting**: ruff
- **Testing**: pytest with coverage
- **CI**: GitHub Actions (test on Python 3.10-3.13)

---

## Version

Current: **0.0.0.dev0**
