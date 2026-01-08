# doctest-expect

CLI output assertion tool for documentation testing.

## Overview

When testing CLI examples in documentation with mktestdocs, bash code blocks only verify that commands exit with code 0 (success). They don't verify the actual output.

doctest-expect solves this by letting you pipe output to `expect` to verify it matches:

```bash
# Without expect: only checks exit code
echo "hello"

# With expect: checks exit code AND output
echo "hello" | expect "hello"
```

## Documentation

- [Getting Started](getting-started.md) - Installation and first example
- [CLI Reference](cli/reference.md) - All commands and options

## Quick Example

```bash
# Exact match
echo "hello world" | expect "hello world"

# Contains substring
python --version | expect --contains "Python"

# JSONL semantic comparison (field order independent)
echo '{"b": 2, "a": 1}' | expect --jsonl '{"a": 1, "b": 2}'
```
