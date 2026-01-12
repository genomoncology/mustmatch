# outmatch

**Assert CLI output. Test your documentation.**

Your CLI tool works perfectly—until someone copies an example from your
docs and it fails. outmatch catches broken examples before users do.

```bash
# Does your help text still say what your docs claim?
mytool --help | outmatch --contains "Usage:"

# Does your JSON output match the documented schema?
mytool export | outmatch --json '{"status": "ok"}'

# Run every bash block in your docs as a test
outmatch test docs/
```

## Why outmatch?

| Problem                        | Solution                       |
|--------------------------------|--------------------------------|
| Docs show outdated CLI output  | Test docs with `outmatch test` |
| JSON field order breaks tests  | `--json` compares semantically |
| Timestamps cause flaky tests   | `--replace` normalizes them    |
| ANSI colors break CI           | `--strip-ansi` removes them    |
| No good CLI assertion library  | Pipe to outmatch, check exit   |

## Install

```bash
pip install outmatch
```

## Quick Start

Pipe any command's output to outmatch with the expected value:

```bash
echo "hello" | outmatch "hello"
```

Exit 0 on match. Exit 1 with diff on mismatch. That's it.

[**Full tutorial → docs/getting-started.md**](docs/getting-started.md)

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
echo "hello world" | outmatch "hello world"

# Contains
python --version 2>&1 | outmatch --contains "Python"

# Regex
date +%Y-%m-%d | outmatch --regex '^\d{4}-\d{2}-\d{2}$'

# JSON - field order independent
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'

# JSONL - one object per line
printf '{"id":1}\n{"id":2}' | outmatch --jsonl '{"id":1}
{"id":2}'
```

[**All modes → docs/matching.md**](docs/matching.md) ·
[**JSON details → docs/json.md**](docs/json.md)

---

## Handling Dynamic Output

Replace timestamps, IDs, and paths before comparison:

```bash
# Replace pattern with placeholder
echo "took 1.5s" | outmatch --replace '\d+\.\d+s=>TIME' \
    "took TIME"

# Multiple replacements
echo "user alice, id 42" | outmatch \
    --replace 'alice=>USER' \
    --replace '\d+=>ID' \
    "user USER, id ID"

# Redact sensitive values
echo "token: abc123" | outmatch --redact 'abc\w+' \
    "token: <redacted>"

# Ignore JSON fields
echo '{"data":"x","ts":123}' | outmatch --json \
    --json-ignore '$.ts' '{"data":"x"}'
```

[**Preprocessing → docs/preprocessing.md**](docs/preprocessing.md)

---

## Normalization

Handle environment differences that cause flaky tests:

| Flag                    | Effect                        |
|-------------------------|-------------------------------|
| `--strip-ansi`          | Remove color codes            |
| `--normalize-newlines`  | CRLF → LF                     |
| `--trim`                | Strip leading/trailing space  |
| `--collapse-whitespace` | Collapse runs to single space |
| `-i`, `--ignore-case`   | Case-insensitive comparison   |

```bash
# Colored output in CI
NO_COLOR=1 mytool status | outmatch "OK"
# Or strip ANSI codes
mytool status | outmatch --strip-ansi "OK"

# Flexible whitespace matching
echo "  hello   world  " | outmatch --trim \
    --collapse-whitespace "hello world"
```

---

## Testing Documentation

Every ` ```bash ` block in your markdown becomes a test:

````markdown
# My CLI Tool

Install it:

```bash
pip install mytool
```

Check it works:

```bash
mytool --version | outmatch --contains "1.0"
```
````

Run with the built-in test runner:

```bash
outmatch test docs/           # Test a directory
outmatch test README.md       # Test a file
outmatch test -v docs/        # Verbose output
outmatch test --fail-fast     # Stop on first failure
```

Or integrate with pytest—the plugin auto-discovers markdown:

```bash
pytest docs/                  # Run markdown as tests
pytest docs/ --collect-only   # See discovered tests
```

[**Test runner → docs/mdtest.md**](docs/mdtest.md) ·
[**pytest plugin → docs/pytest-plugin.md**](docs/pytest-plugin.md)

---

## Block Directives

Control test execution with HTML comments:

````markdown
<!-- outmatch: skip -->
```bash
echo "this block won't run"
```

<!-- outmatch: timeout=60 -->
```bash
slow-command
```

<!-- outmatch: skip-if=CI -->
```bash
interactive-command
```
````

---

## File-Based Expectations

Store expected output in files for large outputs or snapshots:

```bash
# Compare against file
mytool export | outmatch -f expected/output.json

# Update snapshot when output intentionally changes
mytool export | outmatch -f expected/output.json --update
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
outmatch [OPTIONS] [EXPECTED]

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
  --normalize-newlines   CRLF → LF
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

[**Full CLI docs → docs/cli.md**](docs/cli.md)

---

## Development

```bash
git clone https://github.com/anthropics/outmatch
cd outmatch
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

## License

MIT
