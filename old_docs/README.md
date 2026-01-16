# mustmatch

**Assert CLI output. Test your documentation.**

```bash
# Exact match
echo "hello" | mustmatch "hello"

# Contains substring
mytool --help | mustmatch like "Usage:"

# JSON (auto-detected, field order independent)
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Regex (auto-detected by /pattern/ syntax)
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Negation
echo "success" | mustmatch not like "error"

# Test all code blocks in your docs
mustmatch test docs/
```

## Install

```bash
pip install mustmatch
```

## Quick Start

Pipe any command output to mustmatch with the expected value:

```bash
echo "hello" | mustmatch "hello"    # Exit 0 on match
echo "hello" | mustmatch "world"    # Exit 1 on mismatch
```

## Matching Modes

mustmatch auto-detects the comparison mode from syntax:

| Syntax | Mode | Example |
|--------|------|---------|
| `"text"` | Exact string | `mustmatch "hello"` |
| `like "text"` | Contains | `mustmatch like "hello"` |
| `'/pattern/'` | Regex | `mustmatch '/v\d+/'` |
| `'{...}'` | JSON | `mustmatch '{"a":1}'` |
| `'[...]'` | JSON array | `mustmatch '[1,2,3]'` |

### Negation

Add `not` to invert any match:

```bash
echo "ok" | mustmatch not like "error"     # Pass: doesn't contain "error"
echo "ok" | mustmatch not "fail"           # Pass: not exactly "fail"
```

### JSON Comparison

JSON is compared semantically—field order doesn't matter:

```bash
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'           # Match
echo '{"a":1,"b":2,"c":3}' | mustmatch like '{"a":1}'      # Subset match
```

## Testing Documentation

Every bash and python code block in your markdown becomes a test:

````markdown
# My CLI Tool

Check it works:

```bash
mytool --version | mustmatch like "1.0"
```

Python example:

```python
import mytool
assert mytool.process("data")["status"] == "ok"
```
````

Run tests:

```bash
mustmatch test docs/              # Test all markdown files
mustmatch test README.md          # Test single file
mustmatch test -v docs/           # Verbose output
mustmatch test -x docs/           # Stop on first failure
mustmatch test --lang python .    # Only Python blocks
mustmatch test --memory .         # Share Python state between blocks
```

Or use pytest—the plugin auto-discovers markdown:

```bash
pytest docs/
pytest docs/ --mustmatch-lang python
pytest docs/ --mustmatch-memory
```

### Block Directives

Control test behavior with directives in the code fence:

````markdown
```bash skip
echo "this block is skipped"
```

```bash timeout=60
slow-command
```
````

## CLI Reference

```
mustmatch [OPTIONS] [not] [like] EXPECTED
mustmatch test [OPTIONS] PATHS

Options:
    -i, --ignore-case    Case-insensitive comparison
    -q, --quiet          Suppress output
    --version            Show version

Test options:
    -v, --verbose        Show each test result
    -q, --quiet          Minimal output
    -x, --fail-fast      Stop on first failure
    --timeout N          Timeout per block (default: 30)
    --lang LANG          Language: bash, python, all
    --memory             Share Python state between blocks
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Match |
| 1 | Mismatch |
| 2 | Invalid argument |

## Development

```bash
git clone https://github.com/botassembly/mustmatch
cd mustmatch
uv sync --extra dev
uv run pytest docs/
uv run ruff check src
```

## License

MIT
