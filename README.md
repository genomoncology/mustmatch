# mustmatch

**Assert CLI output. Test your documentation.**

Your CLI tool works perfectly—until someone copies an example from your
docs and it fails. mustmatch catches broken examples before users do.

```bash
# Does your help text still say what your docs claim?
mytool --help | mustmatch --contains "Usage:"

# Does your JSON output match the documented schema?
mytool export | mustmatch --json '{"status": "ok"}'

# Run every code block in your docs as a test
mustmatch test docs/

# Test Python code blocks with shared state
mustmatch test --lang python --memory docs/
```

## Why mustmatch?

| Problem                        | Solution                         |
|--------------------------------|----------------------------------|
| Docs show outdated CLI output  | Test docs with `mustmatch test`  |
| JSON field order breaks tests  | `--json` compares semantically   |
| Timestamps cause flaky tests   | `--replace` normalizes them      |
| ANSI colors break CI           | `--strip-ansi` removes them      |
| Python examples drift          | `--lang python` tests them       |
| No good CLI assertion library  | Pipe to mustmatch, check exit    |

## Install

```bash
pip install mustmatch
```

## Quick Start

Pipe any command's output to mustmatch with the expected value:

```bash
echo "hello" | mustmatch "hello"
```

Exit 0 on match. Exit 1 with diff on mismatch. That's it.

[**Full tutorial -> docs/getting-started.md**](docs/getting-started.md)

---

## Comparison Modes

| Mode       | Flag                | Use When                       |
|------------|---------------------|--------------------------------|
| Exact      | *(default)*         | Output must match exactly      |
| Contains   | `--contains`        | Output includes substring      |
| Regex      | `--regex`           | Pattern matching needed        |
| JSON       | `--json`            | Comparing JSON objects         |
| JSONL      | `--jsonl`           | JSON Lines, order matters      |
| JSONL Set  | `--jsonl-set`       | JSON Lines, any order          |
| JSONL Key  | `--jsonl-key FIELD` | Match records by key field     |

```bash
# Exact (default)
echo "hello world" | mustmatch "hello world"

# Contains
python --version 2>&1 | mustmatch --contains "Python"

# Regex
date +%Y-%m-%d | mustmatch --regex '^\d{4}-\d{2}-\d{2}$'

# JSON - field order independent
echo '{"b":2,"a":1}' | mustmatch --json '{"a":1,"b":2}'

# JSONL - one object per line
printf '{"id":1}\n{"id":2}' | mustmatch --jsonl '{"id":1}
{"id":2}'
```

[**All modes -> docs/matching.md**](docs/matching.md) |
[**JSON details -> docs/json.md**](docs/json.md)

---

## Handling Dynamic Output

Replace timestamps, IDs, and paths before comparison:

```bash
# Replace pattern with placeholder
echo "took 1.5s" | mustmatch --replace '\d+\.\d+s=>TIME' \
    "took TIME"

# Multiple replacements
echo "user alice, id 42" | mustmatch \
    --replace 'alice=>USER' \
    --replace '\d+=>ID' \
    "user USER, id ID"

# Redact sensitive values
echo "token: abc123" | mustmatch --redact 'abc\w+' \
    "token: <redacted>"

# Ignore JSON fields
echo '{"data":"x","ts":123}' | mustmatch --json \
    --json-ignore '$.ts' '{"data":"x"}'
```

[**Preprocessing -> docs/preprocessing.md**](docs/preprocessing.md)

---

## Normalization

Handle environment differences that cause flaky tests:

| Flag                    | Effect                        |
|-------------------------|-------------------------------|
| `--strip-ansi`          | Remove color codes            |
| `--normalize-newlines`  | CRLF -> LF                    |
| `--trim`                | Strip leading/trailing space  |
| `--collapse-whitespace` | Collapse runs to single space |
| `-i`, `--ignore-case`   | Case-insensitive comparison   |

```bash
# Colored output in CI
NO_COLOR=1 mytool status | mustmatch "OK"
# Or strip ANSI codes
mytool status | mustmatch --strip-ansi "OK"

# Flexible whitespace matching
echo "  hello   world  " | mustmatch --trim \
    --collapse-whitespace "hello world"
```

---

## Testing Documentation

Every ` ```bash ` and ` ```python ` block in your markdown becomes a test:

````markdown
# My CLI Tool

Install it:

```bash
pip install mytool
```

Check it works:

```bash
mytool --version | mustmatch --contains "1.0"
```

Python example:

```python
import mytool
result = mytool.process("data")
assert result["status"] == "ok"
```
````

Run with the built-in test runner:

```bash
mustmatch test docs/           # Test all code blocks
mustmatch test README.md       # Test a file
mustmatch test -v docs/        # Verbose output
mustmatch test --fail-fast     # Stop on first failure

# Language-specific testing
mustmatch test --lang bash docs/     # Only bash blocks
mustmatch test --lang python docs/   # Only Python blocks
mustmatch test --lang all docs/      # Both (default for pytest)

# Python with shared state (memory mode)
mustmatch test --lang python --memory docs/
```

Or integrate with pytest—the plugin auto-discovers markdown:

```bash
pytest docs/                            # Run markdown as tests
pytest docs/ --collect-only             # See discovered tests
pytest docs/ --mustmatch-lang python    # Only Python blocks
pytest docs/ --mustmatch-memory         # Share Python state
```

[**Test runner -> docs/mdtest.md**](docs/mdtest.md) |
[**Python testing -> docs/python.md**](docs/python.md) |
[**pytest plugin -> docs/pytest-plugin.md**](docs/pytest-plugin.md)

---

## Python Memory Mode

When testing Python documentation, blocks can share state:

````markdown
# Python Tutorial

Define a class:

```python
class Calculator:
    def add(self, a, b):
        return a + b

calc = Calculator()
```

Use it in subsequent blocks:

```python
result = calc.add(2, 3)
assert result == 5
```
````

Run with memory mode:

```bash
mustmatch test --lang python --memory docs/python-tutorial.md
```

Without `--memory`, each block runs independently and the second block would fail because `calc` is undefined.

[**Python testing guide -> docs/python.md**](docs/python.md)

---

## Block Directives

Control test execution with HTML comments:

````markdown
<!-- mustmatch: skip -->
```bash
echo "this block won't run"
```

<!-- mustmatch: timeout=60 -->
```bash
slow-command
```

<!-- mustmatch: skip-if=CI -->
```bash
interactive-command
```
````

---

## File-Based Expectations

Store expected output in files for large outputs or snapshots:

```bash
# Compare against file
mytool export | mustmatch -f expected/output.json

# Update snapshot when output intentionally changes
mytool export | mustmatch -f expected/output.json --update
```

---

## Programmatic API

Use mustmatch in your Python tests:

```python
from mustmatch import check_md_file

# Test all code blocks in a file
assert check_md_file("docs/getting-started.md")

# Test only Python blocks with memory mode
assert check_md_file(
    "docs/python-tutorial.md",
    lang="python",
    memory=True
)
```

---

## Exit Codes

| Code | Meaning          |
|------|------------------|
| 0    | Match            |
| 1    | Mismatch         |
| 2    | Invalid argument |

---

## CLI Reference

```
mustmatch [OPTIONS] [EXPECTED]

Comparison:
  --contains             Substring match
  --regex                Regex pattern match
  --json                 JSON semantic comparison
  --jsonl                JSON Lines (order matters)
  --jsonl-set            JSON Lines (unordered)
  --jsonl-key FIELD      Match by key field
  --jsonl-contains       Subset matching

Normalization:
  --strip-ansi           Remove ANSI codes
  --normalize-newlines   CRLF -> LF
  --trim                 Strip whitespace
  --collapse-whitespace  Collapse whitespace runs
  -i, --ignore-case      Case-insensitive

Transform:
  --replace REGEX=>REPL  Pattern replacement
  --redact REGEX         Replace with <redacted>
  --json-ignore PATH     Ignore JSON path

Files:
  -f, --expected-file    Read expected from file
  --update               Update file on mismatch

Output:
  -q, --quiet            Suppress output
  --color MODE           auto | always | never
  --diff-context N       Diff context lines
```

[**Full CLI docs -> docs/cli.md**](docs/cli.md)

---

## Development

```bash
git clone https://github.com/botassembly/mustmatch
cd mustmatch
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

## License

MIT
