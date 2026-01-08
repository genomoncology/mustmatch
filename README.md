# doctest-expect

CLI output assertion tool for documentation testing. Pipe command output to `expect` to verify it matches expected values.

Designed for use with [mktestdocs](https://github.com/koaning/mktestdocs) to test CLI examples in documentation.

## Installation

```bash
uv add --group dev doctest-expect
```

Or install from source:
```bash
uv pip install -e path/to/doctest-expect
```

## Usage

### Exact match

```bash
echo "hello world" | expect "hello world"
```

### Contains substring

```bash
python --version | expect --contains "Python"
```

### JSONL semantic comparison

Field order doesn't matter - these are equivalent:

```bash
echo '{"name": "alice", "age": 30}' | expect --jsonl '{"age": 30, "name": "alice"}'
```

### JSONL subset check

Verify output contains expected records (useful for filtering):

```bash
echo '{"id": 1, "name": "alice"}
{"id": 2, "name": "bob"}' | expect --jsonl-contains '{"id": 1}'
```

### Multi-line expected output

Use heredoc for multi-line expectations:

```bash
echo "line one
line two" | expect "$(cat <<'EOF'
line one
line two
EOF
)"
```

## Modes

| Flag | Behavior |
|------|----------|
| (default) | Exact string match |
| `--contains` | Substring match |
| `--jsonl` | JSONL semantic comparison (field order independent) |
| `--jsonl-contains` | JSONL subset match |
| `-q` / `--quiet` | Suppress diff output on failure |

## Exit Codes

- `0` - Match
- `1` - Mismatch (prints diff to stderr)
- `2` - Invalid arguments

## Why?

When testing CLI documentation with mktestdocs, bash blocks only verify exit code 0 (command didn't crash). They don't verify output content.

This tool lets you **show AND verify** expected output in documentation:

```bash
# This just verifies the command runs without error
python --version

# This verifies the command runs AND produces expected output
python --version | expect --contains "Python 3"
```

Both forms are valid documentation. Use `expect` when the output content is important to demonstrate to readers.

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check src tests
```

## License

MIT
