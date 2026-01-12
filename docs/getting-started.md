# Getting Started

Get outmatch running in under a minute, then learn the patterns you'll use daily.

## Installation

<!-- outmatch: skip -->
```bash
pip install outmatch
```

Or with uv:
```
uv add outmatch
```

## Your First Assertion

Pipe command output to outmatch with the expected value:

```bash
echo "hello world" | outmatch "hello world"
```

No output means success (exit code 0). On mismatch, you get a diff and exit code 1.

## Choosing a Match Mode

### Exact match (default)

```bash
echo "hello world" | outmatch "hello world"
```

### Contains (`--contains`)

```bash
outmatch --help | outmatch --contains "Usage:"
```

### Regex (`--regex`)

```bash
echo "completed in 42ms" | outmatch --regex 'completed in \d+ms'
```

### JSON (`--json`)

```bash
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'
```

## Multi-line Output

Use literal newlines in your expected value:

```bash
printf "line 1\nline 2\nline 3" | outmatch "line 1
line 2
line 3"
```

Or test against real CLI output:

```bash
ls --help | outmatch --contains "list"
```

## Handling Volatile Values

Use `--replace` for timestamps, IDs, or paths that change:

```bash
echo "time: 1.5s" | outmatch --replace '\d+\.\d+s=>TIME' "time: TIME"
echo "user: alice, id: 12345" | outmatch \
  --replace '\d+=><id>' \
  --replace 'alice=><user>' \
  "user: <user>, id: <id>"
```

## Testing Your Documentation

Run all bash code blocks in your docs as tests:

```console
$ outmatch test docs/
✓ 42 passed, 42 total
```

Skip blocks with HTML comments:

````markdown
<!-- outmatch: skip -->
```bash
# This block won't run
```
````

## Next Steps

- [Text Matching](matching.md) - Exact, contains, regex
- [JSON Comparison](json.md) - Semantic comparison, field ignoring
- [JSONL Comparison](jsonl.md) - JSON Lines modes
- [Preprocessing](preprocessing.md) - Normalization, replace, redact
- [CLI Reference](cli.md) - All options, exit codes, errors
- [Test Runner](mdtest.md) - `outmatch test` documentation
- [Pytest Plugin](pytest-plugin.md) - pytest integration
