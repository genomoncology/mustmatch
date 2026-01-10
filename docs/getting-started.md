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

Most output falls into one of four patterns. Pick the right mode for your situation.

### When output is predictable: Exact match

Use the default mode when you control the exact output:

```bash
echo "hello world" | outmatch "hello world"
```

### When you need flexibility: Contains

Use `--contains` when you only care about part of the output:

```bash
echo "version 1.2.3" | outmatch --contains "1.2"
```

Ideal for help text, log messages, or any output with boilerplate you want to ignore.

### When output varies: Regex

Use `--regex` when values change between runs:

```bash
echo "completed in 42ms" | outmatch --regex 'completed in \d+ms'
```

Perfect for timestamps, durations, generated IDs, or any dynamic content.

### When comparing data: JSON

Use `--json` when field order shouldn't matter:

```bash
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'
```

Compares structure semantically. Different formatting, same data? It passes.

## Handling Volatile Values

Real-world output often contains timestamps, UUIDs, or paths that change. The `--replace` flag normalizes these before comparison:

```bash
echo "time: 1.5s" | outmatch --replace '\d+\.\d+s=>TIME' "time: TIME"
```

The pattern `REGEX=>REPLACEMENT` transforms matching text. Chain multiple replacements:

```bash
echo "user: alice, id: 12345" | outmatch \
  --replace '\d+=><id>' \
  --replace 'alice=><user>' \
  "user: <user>, id: <id>"
```

## Testing Your Documentation

This is where outmatch shines. Run all bash code blocks in your docs as tests:

```bash
outmatch test docs/
```

Every fenced `bash` block becomes a test case. Failed commands fail the test. Add outmatch assertions for output verification:

````markdown
```console
mycli --version | outmatch "mycli 1.0.0"
```
````

Control test execution with HTML comments:

````markdown
<!-- outmatch: skip -->
```console
# This block won't run
dangerous-command
```
````

## Next Steps

- [Matching Modes](tests/matching.md) - Exact, contains, regex
- [JSON Modes](tests/json.md) - Deep comparison, field ignoring
- [Preprocessing](tests/preprocessing.md) - Normalization, replace, redact
- [CLI Options](tests/cli.md) - Files, output, errors
- [Test Runner](tests/mdtest.md) - `outmatch test` documentation
