# doctest-expect

CLI output assertion tool for documentation testing. Pipe command output to `expect` to verify it matches expected values.

## Installation

```bash
uv add --group dev doctest-expect
```

Or install from path:
```bash
uv pip install -e /path/to/doctest-expect
```

## Usage in Documentation

### Exact match

```bash
findterms --version | expect "findterms 0.1.0"
```

### Contains substring

```bash
findterms --help | expect --contains "Usage:"
```

### JSONL semantic comparison

Field order doesn't matter:

```bash
echo '{"text": "hello"}' | findterms extract --format jsonl \
  | expect --jsonl '{"term": "hello", "start": 0, "end": 5}'
```

### JSONL subset check

Verify output contains expected records:

```bash
findterms scan doc.txt --format jsonl \
  | expect --jsonl-contains '{"entity_id": "D001234"}'
```

### Multi-line expected output

```bash
findterms scan doc.txt --format jsonl | expect <<'EOF'
{"entity_id": "D001234", "term": "diabetes"}
{"entity_id": "D005678", "term": "insulin"}
EOF
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
- `1` - Mismatch
- `2` - Invalid arguments

## Why?

When testing CLI documentation with mktestdocs, bash blocks only verify exit code 0 (command didn't crash). They don't verify output.

This tool lets you show AND verify expected output in documentation:

```bash
# This just verifies the command runs
findterms --version

# This verifies the command runs AND produces correct output
findterms --version | expect "findterms 0.1.0"
```

Both forms are valid documentation. Use `expect` when the output is important to show readers.
