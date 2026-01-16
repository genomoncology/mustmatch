# mustmatch

**CLI output assertion tool for documentation testing**

---

## Build & Test

```bash
uv sync --extra dev    # Install dependencies
uv run pytest          # Run tests
uv run pytest --cov    # With coverage
uv run ruff check src  # Lint
```

---

## Project Structure

```
mustmatch/
├── src/mustmatch/         # Package source
│   ├── __init__.py           # Public API exports
│   ├── __main__.py           # python -m support
│   ├── cli.py                # CLI interface (match, test, exec)
│   ├── pytest_plugin.py      # pytest integration
│   ├── version.py            # Version info
│   └── services/             # Core services layer
│       ├── __init__.py          # Service exports
│       ├── comparator.py        # Comparison logic (exact, contains, regex, json, jsonl)
│       ├── normalizer.py        # Text preprocessing (ANSI strip, whitespace)
│       ├── parser.py            # Markdown parsing (Mistune AST)
│       └── runner.py            # Code execution (bash, python)
├── docs/                  # Documentation
│   ├── *.md                  # User guides
│   └── tests/                # Test documentation (run via pytest)
│       ├── api.md
│       ├── cli/
│       ├── comparator/
│       ├── normalizer/
│       ├── parser/
│       └── runner/
└── pyproject.toml         # Package config
```

---

## API

### CLI Usage

```bash
# Exact match
echo "hello" | mustmatch "hello"

# Contains substring (like)
cmd --help | mustmatch like "Usage:"

# Negation
echo "ok" | mustmatch not like "error"

# JSON semantic (auto-detected, field order independent)
echo '{"b": 2, "a": 1}' | mustmatch '{"a": 1, "b": 2}'

# JSON subset match
echo '{"a":1,"b":2}' | mustmatch like '{"a":1}'

# Regex (auto-detected by /pattern/ syntax)
echo "v1.2.3" | mustmatch "/v\d+\.\d+/"

# Test markdown docs
mustmatch test docs/

# Test with verbose output
mustmatch test -v docs/

# Execute and assert
mustmatch exec --exit-code 0 --stdout "hello" -- echo hello
```

### Exit Codes

- `0` - Match
- `1` - Mismatch
- `2` - Invalid arguments

---

## Documentation Testing

Tests live in `docs/` as markdown files with code blocks. The pytest plugin collects and runs these blocks.

To run: `uv run pytest docs/ -v`

### Block Directives

Code blocks support directives in the info string:

```markdown
\`\`\`bash skip
# This block is skipped
\`\`\`

\`\`\`bash timeout=5
# This block has a 5-second timeout
\`\`\`

\`\`\`bash expect-exit=1
# This block is expected to fail with exit code 1
echo "hello" | mustmatch "world"
\`\`\`
```

---

## Code Quality

- **Linting**: ruff
- **Testing**: pytest with coverage (target: 45%+)
- **CI**: GitHub Actions (test on Python 3.10-3.13)

---

## Version

Current: **0.0.0.dev0**
