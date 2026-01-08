# outmatchall

CLI output assertion tool for documentation testing.

## Overview

When testing CLI examples in documentation with mktestdocs, bash code blocks only verify that commands exit with code 0 (success). They don't verify the actual output.

outmatchall solves this by letting you pipe output to `outmatchall` to verify it matches:

```bash
# Without outmatchall: only checks exit code
echo "hello"

# With outmatchall: checks exit code AND output
echo "hello" | outmatchall "hello"
```

## Documentation

- [Getting Started](getting-started.md) - Installation and first example
- [CLI Reference](cli/reference.md) - All commands and options

## Quick Example

```bash
# Exact match
echo "hello world" | outmatchall "hello world"

# Contains substring
python --version | outmatchall --contains "Python"

# JSONL semantic comparison (field order independent)
echo '{"b": 2, "a": 1}' | outmatchall --jsonl '{"a": 1, "b": 2}'
```
