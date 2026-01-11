# outmatch

CLI output assertion tool for documentation testing. Verify command output matches expectations.

## Overview

| Usage | Description |
|-------|-------------|
| `cmd \| outmatch "expected"` | Pipe output to verify it matches |
| `pytest docs/` | Auto-run bash blocks in markdown via pytest plugin |
| `outmatch test docs/` | Standalone markdown test runner |

## Capabilities

| Feature | Flags |
|---------|-------|
| **Comparison modes** | `--contains`, `--regex`, `--json`, `--jsonl`, `--jsonl-set`, `--jsonl-key`, `--jsonl-contains` |
| **Normalization** | `--strip-ansi`, `--trim`, `--collapse-whitespace`, `--normalize-newlines`, `-i` |
| **Transformation** | `--replace 'REGEX=>REPL'`, `--redact 'REGEX'` |
| **JSON options** | `--json-ignore '$.path'` |
| **File options** | `-f FILE`, `--update` |
| **Output** | `-q`, `--color`, `--diff-context` |

## Installation

```bash
uv add outmatch              # Add to project
uv tool install outmatch     # Install globally
pip install outmatch         # Or with pip
```

## Quick Examples

```bash
# Exact match
echo "hello" | outmatch "hello"

# Contains substring
python --version 2>&1 | outmatch --contains "Python"

# Regex pattern
date | outmatch --regex '\d{4}'

# JSON (field order independent)
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'

# Replace volatile content
echo "took 1.5s" | outmatch --replace '\d+\.\d+s=>TIME' "took TIME"
```

---

## Pytest Plugin

The pytest plugin automatically discovers and runs bash blocks in markdown files.

### Setup

Install outmatch in your project - the plugin registers automatically:

```bash
uv add --dev outmatch
```

Configure pytest to find your docs:

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests", "docs"]
```

### Usage

```bash
# Run all tests including markdown
pytest

# Run only markdown tests
pytest docs/

# Run specific markdown file
pytest docs/usage.md

# See what tests are collected
pytest docs/ --collect-only
```

### How It Works

Every ` ```bash ` block becomes a test:

```markdown
# My Documentation

## Installation

` ```bash
pip install mypackage
` ```

## Usage

` ```bash
mypackage --version | outmatch --contains "1.0"
` ```
```

Running `pytest docs/` executes each bash block. Test names come from the preceding heading.

---

## Comparison Modes

| Mode | Flag | Behavior |
|------|------|----------|
| Exact | (default) | Exact string match (trailing newlines normalized) |
| Contains | `--contains` | Substring match |
| Regex | `--regex` | Regex pattern match |
| JSON | `--json` | Semantic JSON comparison |
| JSONL | `--jsonl` | JSON Lines (order matters) |
| JSONL Set | `--jsonl-set` | JSON Lines (order independent) |
| JSONL Key | `--jsonl-key F` | Match by field F, then compare |
| JSONL Contains | `--jsonl-contains` | Subset match with partial fields |

### Examples

```bash
# Exact (default)
echo "hello world" | outmatch "hello world"

# Contains
python --help | outmatch --contains "usage:"

# Regex
mycli build | outmatch --regex 'built in \d+ms'

# JSON - field order doesn't matter
echo '{"name":"alice","age":30}' | outmatch --json '{"age":30,"name":"alice"}'

# JSONL - record order matters
printf '{"id":1}\n{"id":2}' | outmatch --jsonl '{"id":1}
{"id":2}'

# JSONL Set - record order doesn't matter
mycli list | outmatch --jsonl-set '{"id":2}
{"id":1}'

# JSONL Key - match by id field
mycli users | outmatch --jsonl-key id '{"id":2,"name":"bob"}
{"id":1,"name":"alice"}'

# JSONL Contains - partial matching
mycli users | outmatch --jsonl-contains '{"name":"alice"}'
```

---

## Normalization

Handle trivial differences that cause flaky tests.

| Flag | Effect |
|------|--------|
| `--strip-ansi` | Remove ANSI color codes |
| `--normalize-newlines` | Convert CRLF to LF |
| `--trim` | Strip leading/trailing whitespace |
| `--collapse-whitespace` | Collapse whitespace runs |
| `-i`, `--ignore-case` | Case-insensitive comparison |

```bash
# Handle colored output
mycli status | outmatch --strip-ansi --contains "OK"

# Flexible whitespace
mycli format | outmatch --trim --collapse-whitespace "hello world"
```

---

## Pattern Transformation

Replace volatile content (timestamps, IDs, paths) before comparison.

### Replace

Syntax: `--replace 'REGEX=>REPLACEMENT'`

```bash
# Replace duration
echo "took 1.5s" | outmatch --replace '\d+\.\d+s=><time>' "took <time>"

# Replace UUID
echo "id: 550e8400-e29b-41d4-a716-446655440000" | \
    outmatch --replace '[0-9a-f-]{36}=><uuid>' "id: <uuid>"

# Multiple replacements
echo "user alice, id 123" | \
    outmatch --replace '\d+=><id>' --replace 'alice=><user>' "user <user>, id <id>"

# Replace with empty string
echo "hello123world" | outmatch --replace '\d+=>' "helloworld"
```

### Redact

Replace patterns with `<redacted>`:

```bash
echo "token: abc123xyz" | outmatch --redact 'abc\w+xyz' "token: <redacted>"
```

---

## JSON Options

### Ignore Paths

Skip volatile JSON fields during comparison:

```bash
# Ignore timestamp
mycli status | outmatch --json --json-ignore '$.timestamp' '{"status":"ok"}'

# Ignore nested field
mycli user | outmatch --json --json-ignore '$.meta.updated_at' '{"name":"alice"}'

# Multiple ignores
mycli export | outmatch --jsonl --json-ignore '$.ts' --json-ignore '$.hash' '{"id":1}'
```

### Writing Multiline JSON

Bash preserves literal newlines inside single quotes, making multiline JSON easy to write:

```bash
# Multiline JSONL - newlines inside quotes are literal
printf '{"id":1}\n{"id":2}' | outmatch --jsonl '{"id":1}
{"id":2}'

# Multiline JSON object
echo '{"name":"alice","age":30}' | outmatch --json '{
  "name": "alice",
  "age": 30
}'

# Command continuation with backslash (outside quotes)
printf '{"id":1}\n{"id":2}' \
  | outmatch --jsonl '{"id":1}
{"id":2}'
```

For complex JSON, use a file instead:

<!-- outmatch: skip -->
```bash
mycli export | outmatch --jsonl -f expected/records.jsonl
```

---

## File Options

### Expected from File

```bash
mycli help | outmatch -f expected/help.txt
mycli export | outmatch --jsonl -f expected/records.jsonl
```

### Snapshot Updates

Update expected file when output changes:

```bash
mycli help | outmatch -f expected/help.txt --update
```

---

## Standalone Test Runner

Run markdown tests without pytest:

```bash
outmatch test docs/           # Test directory
outmatch test docs/usage.md   # Test file
outmatch test -v docs/        # Verbose
outmatch test --fail-fast     # Stop on first failure
```

### Options

| Flag | Effect |
|------|--------|
| `-q` | Quiet - only counts |
| `-v` | Verbose - full output |
| `--fail-fast` | Stop on first failure |
| `--parallel N` | Concurrent files (default: 4) |
| `--timeout N` | Per-block timeout (default: 30s) |
| `--junit-xml PATH` | JUnit XML report |
| `--json PATH` | JSON report |
| `--tap` | TAP format output |

### Block Directives

Control blocks with HTML comments:

```markdown
<!-- outmatch: skip -->
` ```bash
echo "this block is skipped"
` ```

<!-- outmatch: timeout=60 -->
` ```bash
long_running_command
` ```
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Match |
| `1` | Mismatch |
| `2` | Invalid arguments |

---

## Tips

### Capture stderr

Many commands write to stderr:

```bash
python --version 2>&1 | outmatch --contains "Python"
```

### Handle pipe failures

```bash
set -o pipefail
failing_cmd | outmatch "never reached"  # Now fails correctly
```

### CI considerations

- **Colors**: Use `--strip-ansi` or `NO_COLOR=1`
- **Newlines**: Use `--normalize-newlines` for cross-platform
- **Timestamps**: Use `--replace` or `--json-ignore`

---

## Development

```bash
uv sync --extra dev       # Install dependencies
uv run pytest             # Run tests (includes markdown docs)
uv run pytest --cov       # With coverage
uv run ruff check src     # Lint
```

## License

MIT
