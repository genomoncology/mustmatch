# mustmatch

**Keep your documentation honest.**

Every code example in your docs is a promise. When those examples stop working, your users discover it the hard way. mustmatch tests command-line output against expected values, catching broken examples before your users do.

## The Problem

Documentation rots. You refactor a CLI flag, update an output format, or fix a bug that changes behavior. Your docs still show the old output. Users copy-paste examples that don't work. Issues pile up. Trust erodes.

## The Solution

Pipe any command through mustmatch to verify its output:

```bash
echo "hello world" | mustmatch "hello world"
```

If it matches, exit 0. If it doesn't, exit 1 with a helpful diff. Simple enough to use anywhere: CI pipelines, pre-commit hooks, or embedded in your markdown documentation itself.

## Quick Tour

**Exact matching** - The default. Output must match exactly.
```bash
mustmatch --version | mustmatch --contains "0.0.0.dev0"
```

**Substring matching** - Check that output contains expected text.
```bash
mustmatch --help | mustmatch --contains "Usage:"
```

**Pattern matching** - Handle dynamic values like timestamps.
```bash
echo "Completed in 1.23s" | mustmatch --regex 'Completed in \d+\.\d+s'
```

**JSON comparison** - Compare structure, not formatting.
```bash
echo '{"b":2,"a":1}' | mustmatch --json '{"a":1,"b":2}'
```

## Documentation as Tests

The real power: test your markdown documentation directly.

```console
$ mustmatch test docs/
✓ 42 passed, 42 total
```

Every `bash` code block becomes a test. Your docs become executable specifications. See [Getting Started](getting-started.md) to begin.

## When to Use mustmatch

- **Documentation testing** - Verify code examples in README, tutorials, API docs
- **CLI testing** - Assertion library for command-line tool output
- **Snapshot testing** - Store expected output in files, update with `--update`
- **CI pipelines** - Fast, dependency-free output verification
