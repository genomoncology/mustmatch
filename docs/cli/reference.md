# CLI Reference

## Usage

```
command | expect [OPTIONS] EXPECTED
```

Reads stdin, compares to EXPECTED, exits 0 on match or 1 on mismatch.

## Comparison Modes

### Exact Match (Default)

Compares output exactly (trailing newlines are normalized):

```bash
echo "hello world" | expect "hello world"
```

### Contains (`--contains`)

Checks if output contains a substring:

```bash
python --version | expect --contains "Python"
```

### JSONL Semantic (`--jsonl`)

Compares JSON Lines output semantically. Field order within objects doesn't matter:

```bash
echo '{"b": 2, "a": 1}' | expect --jsonl '{"a": 1, "b": 2}'
```

Record order **does** matter:

```bash
# This will FAIL - wrong order
echo '{"id": 1}
{"id": 2}' | expect --jsonl '{"id": 2}
{"id": 1}'
```

### JSONL Contains (`--jsonl-contains`)

Checks if output contains expected records:

```bash
echo '{"id": 1, "name": "alice"}
{"id": 2, "name": "bob"}' | expect --jsonl-contains '{"id": 2}'
```

## Options

| Flag | Description |
|------|-------------|
| `--contains` | Substring match instead of exact |
| `--jsonl` | JSONL semantic comparison |
| `--jsonl-contains` | JSONL subset matching |
| `-q`, `--quiet` | Suppress diff output on failure |
| `--version` | Show version |
| `--help` | Show help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Match - assertion passed |
| 1 | Mismatch - assertion failed |
| 2 | Error - invalid arguments |

## Multi-line Expectations

Use heredoc syntax for multi-line expected output:

```bash
echo "line 1
line 2
line 3" | expect "$(cat <<'EOF'
line 1
line 2
line 3
EOF
)"
```

Or use JSONL mode for structured data:

```bash
echo '{"id": 1}
{"id": 2}' | expect --jsonl '{"id": 1}
{"id": 2}'
```

## Tips

1. **Use `--contains` for volatile output** - Match only stable parts when output includes timestamps or versions.

2. **Use `--jsonl` for structured data** - Don't rely on field ordering in JSON output.

3. **Use `-q` in CI** - The quiet flag reduces noise in test output.
