# Usage Guide

doctest-expect is a CLI tool for asserting command output in documentation tests.

## Basic Concept

When testing CLI examples in documentation with mktestdocs, bash code blocks only verify that commands exit with code 0 (success). They don't verify the actual output.

doctest-expect solves this by letting you pipe output to `expect` to verify it matches:

```bash
# Without expect: only checks exit code
echo "hello"

# With expect: checks exit code AND output
echo "hello" | expect "hello"
```

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

Useful when you only care about part of the output.

### JSONL Semantic (`--jsonl`)

Compares JSON Lines output semantically. Field order within objects doesn't matter:

```bash
# These are equivalent
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

Checks if output contains expected records. Each expected record must match at least one actual record:

```bash
echo '{"id": 1, "name": "alice"}
{"id": 2, "name": "bob"}
{"id": 3, "name": "charlie"}' | expect --jsonl-contains '{"id": 2}'
```

You can check for multiple records:

```bash
echo '{"id": 1}
{"id": 2}
{"id": 3}' | expect --jsonl-contains '{"id": 1}
{"id": 3}'
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

For multi-line expected output, use heredoc syntax:

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

## Integration with mktestdocs

Add doctest-expect as a dev dependency:

```bash
uv add --group dev doctest-expect
```

Then use it in your documentation examples:

````markdown
## Example Usage

Check the version:

```bash
mycommand --version | expect --contains "1.0"
```

Process some data:

```bash
echo '{"input": "data"}' | mycommand process | expect --jsonl '{"output": "result"}'
```
````

When mktestdocs runs these bash blocks, the `expect` assertions will verify the output.

## Tips

1. **Use `--contains` for volatile output** - If output includes timestamps, versions, or other changing data, match only the stable parts.

2. **Use `--jsonl` for structured data** - Don't rely on field ordering in JSON output.

3. **Use `-q` in CI** - The quiet flag reduces noise in test output.

4. **Keep examples realistic** - The documentation should show real, useful commands.
