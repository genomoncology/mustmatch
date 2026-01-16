# mustmatch

**Assert CLI output. Test your documentation.**

```bash
# Verify command output
echo "hello" | mustmatch "hello"

# Test for substrings
ls -la | mustmatch like "README"

# JSON comparison (field order doesn't matter)
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'

# Regex patterns
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Assert errors DON'T appear
echo "success" | mustmatch not like "error"
```

## Install

```
pip install mustmatch
```

## Why mustmatch?

Your documentation has examples. But do they work?

```bash
# This example in your README:
echo "hello" | mustmatch "hello"

# Will it work tomorrow? Next week? After refactoring?
# With mustmatch, your docs are tests. If docs pass, examples work.
```

## Quick Start

### 1. Pipe and Match

```bash
echo "hello" | mustmatch "hello"        # ✓ Exit 0
echo "hello world" | mustmatch like "world"   # ✓ Contains
echo "success" | mustmatch not like "error"   # ✓ Negation
```

### 2. Auto-Detection

mustmatch figures out what you want:

```bash
# String comparison
echo "hello" | mustmatch "hello"

# Regex (from /slashes/)
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# JSON (from {braces})
echo '{"a":1,"b":2}' | mustmatch '{"a":1,"b":2}'
```

### 3. JSON Intelligence

```bash
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Subset matching
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

## Comparison Modes

### Exact Match

```bash
echo "hello" | mustmatch "hello"
```

### Contains (`like`)

```bash
echo "hello world" | mustmatch like "world"
ls -la | mustmatch like "README"
```

### Negation (`not`)

```bash
echo "success" | mustmatch not "error"
echo "success" | mustmatch not like "error"
```

### Regex (`/pattern/`)

```bash
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
echo "v1.2.3" | mustmatch '/^v\d+\.\d+\.\d+$/'
```

### JSON (semantic)

```bash
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Subset matching
echo '{"status":"ok","count":42,"time":"2024-01-01"}' | \
    mustmatch like '{"status":"ok"}'
```

## Text Normalization

mustmatch automatically cleans output:

```bash
# ANSI codes stripped
printf "\033[31mREADME\033[0m\n" | mustmatch "README"

# Whitespace trimmed
echo "  hello  " | mustmatch "hello"

# Newlines normalized
printf "hello\r\n" | mustmatch "hello"
```

## Exit Codes

```bash
echo "ok" | mustmatch "ok"              # Exit 0 (match)
echo "ok" | mustmatch "fail" || echo "no match"   # Exit 1

# Use in scripts
if echo "ready" | mustmatch "ready"; then
    echo "Proceeding..."
fi
```

## Use Cases

### Keep Documentation Up-to-Date

Every example in your docs becomes a test. If the example breaks, CI fails.

### DevOps Scripts

Verify service health in deployment scripts.

### API Testing

Test JSON API responses with semantic comparison.

## CLI Reference

```
Usage:
    command | mustmatch [not] [like] EXPECTED

Options:
    -i, --ignore-case    Case-insensitive
    -q, --quiet          Suppress output
    --version            Show version
    -h, --help           Show help

Exit codes:
    0    Match succeeded
    1    Match failed
    2    Invalid arguments
```

## Examples

```bash
# Exact match
echo "hello" | mustmatch "hello"

# Case insensitive
echo "HELLO" | mustmatch -i "hello"

# Contains
echo "hello world" | mustmatch like "world"

# Negation
echo "success" | mustmatch not like "error"

# Regex
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# JSON
echo '{"a":1,"b":2}' | mustmatch '{"a":1,"b":2}'

# JSON subset
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'

# Check help output
mustmatch --help | mustmatch like "Usage:"

# Verify version
mustmatch --version | mustmatch like "mustmatch"
```

## License

MIT
