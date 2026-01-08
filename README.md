# doctest-expect

CLI output assertion tool for documentation testing. Pipe command output to `expect` to verify it matches expected values.

Designed for use with [mktestdocs](https://github.com/koaning/mktestdocs) to test CLI examples in documentation.

## Key Features

- **Multiple comparison modes**: exact, contains, regex, JSON, JSONL
- **Normalization options**: handle ANSI colors, whitespace, case sensitivity
- **Pattern transformation**: replace/redact volatile content (timestamps, IDs)
- **JSON path ignore**: skip volatile fields in JSON comparisons
- **Expected from file**: cleaner multi-line expectations
- **Snapshot updates**: auto-update expected files on mismatch
- **Colored diff output**: actionable failure messages

## Installation

```bash
uv add --group dev doctest-expect
```

Or install globally:
```bash
uv tool install doctest-expect
pipx install doctest-expect
```

**Note**: The CLI installs as `expect`. On systems with Tcl's `expect`, use the unambiguous invocation:
```bash
python -m doctest_expect --help
```

## Quickstart

```bash
# Exact match
echo "hello world" | expect "hello world"

# Contains substring
python --version 2>&1 | expect --contains "Python"

# Regex for volatile output
mycli run | expect --regex 'completed in \d+\.\d+s'

# JSON semantic comparison (field order independent)
echo '{"b": 2, "a": 1}' | expect --json '{"a": 1, "b": 2}'
```

**Important**: Many commands write to stderr (e.g., `python --version` on some systems). Use `2>&1` to capture both streams:
```bash
python --version 2>&1 | expect --contains "Python"
```

**Pipeline exit codes**: In bash, `cmd | expect` returns `expect`'s exit code, not `cmd`'s. To fail when `cmd` fails:
```bash
set -o pipefail
mycli run | expect "success"
```

## Comparison Modes

| Flag | Behavior |
|------|----------|
| (default) | Exact string match (trailing newlines normalized) |
| `--contains` | Substring match |
| `--regex` | Regex pattern match (multiline, dotall) |
| `--json` | Single JSON value semantic comparison |
| `--jsonl` | JSONL semantic comparison (record order matters) |
| `--jsonl-set` | JSONL as unordered multiset |
| `--jsonl-key FIELD` | JSONL matched by key field |
| `--jsonl-contains` | JSONL subset match (partial fields OK) |

### Exact Match (default)

Compares output exactly, normalizing trailing newlines on both sides.

```bash
echo "hello world" | expect "hello world"
```

### Contains

Checks if output contains the expected substring.

```bash
python --help | expect --contains "usage:"
```

### Regex

Matches output against a regex pattern. Uses Python's `re` with `MULTILINE` and `DOTALL` flags.

```bash
mycli build | expect --regex 'built in \d+ms'
mycli logs | expect --regex 'ERROR:.*connection refused'
```

### JSON

Compares single JSON values semantically. Field order doesn't matter.

```bash
echo '{"name": "alice", "age": 30}' | expect --json '{"age": 30, "name": "alice"}'
```

### JSONL

Compares JSON Lines output. Field order within records doesn't matter, but record order does.

```bash
echo '{"id": 1}
{"id": 2}' | expect --jsonl '{"id": 1}
{"id": 2}'
```

### JSONL Set

Order-independent JSONL comparison (multiset semantics).

```bash
mycli list | expect --jsonl-set '{"id": 2}
{"id": 1}'
```

### JSONL Key

Match records by a key field, then compare. Useful for stable docs when record order varies.

```bash
mycli users | expect --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

### JSONL Contains

Check that output contains expected records. Partial field matching supported.

```bash
mycli users | expect --jsonl-contains '{"name": "alice"}'
```

## Normalization Options

Use these flags to reduce flaky tests caused by trivial differences.

| Flag | Effect |
|------|--------|
| `--strip-ansi` | Remove ANSI escape sequences (colors) |
| `--normalize-newlines` | Convert CRLF to LF |
| `--trim` | Strip leading/trailing whitespace |
| `--collapse-whitespace` | Collapse whitespace runs to single spaces |
| `--ignore-case`, `-i` | Case-insensitive comparison |

```bash
# Handle colored output
mycli status | expect --contains "OK" --strip-ansi

# Handle Windows line endings
mycli export | expect --normalize-newlines -f expected.txt

# Flexible whitespace matching
mycli format | expect --trim --collapse-whitespace "hello world"
```

## Pattern Transformation

For nondeterministic output (timestamps, durations, IDs, temp paths), use pattern replacement.

### Replace

Replace regex patterns before comparison. Repeatable.

```bash
mycli run | expect --replace '\d+\.\d+s' '<time>' "completed in <time>"
mycli build | expect --replace '/tmp/[a-z0-9]+' '<tmpdir>' "output: <tmpdir>/result.txt"
```

### Redact

Replace patterns with `<redacted>`. Repeatable.

```bash
mycli token | expect --redact '[a-f0-9]{32}' "token: <redacted>"
```

## JSON Options

### Ignore Paths

Ignore volatile JSON fields during comparison. Uses JSONPath-like syntax.

```bash
# Ignore timestamp field
mycli audit | expect --json --json-ignore '$.timestamp' '{"status": "ok"}'

# Ignore nested field
mycli user | expect --json --json-ignore '$.metadata.updated_at' '{"name": "alice"}'

# Multiple ignores
mycli export | expect --jsonl --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'
```

## Expected from File

For multi-line expectations, use `-f`/`--expected-file` instead of command substitution.

```bash
# Much cleaner than heredocs
mycli help | expect -f docs/expected/help.txt

# Works with all modes
mycli export | expect --jsonl -f expected/records.jsonl
```

## Snapshot Updates

Automatically update expected files when output changes. Useful for maintaining documentation.

```bash
# Update expected file if mismatch
mycli help | expect -f docs/expected/help.txt --update
```

**Safety**: Only works with `-f`. Requires explicit flag to prevent accidental overwrites.

## Output Options

| Flag | Effect |
|------|--------|
| `-q`, `--quiet` | Suppress diff output on failure |
| `--color auto\|always\|never` | Colorize output (default: auto) |
| `--diff-context N` | Lines of context in diff (default: 3) |

```bash
# Quiet mode for CI
mycli run | expect -q "success"

# Force colors in CI
mycli run | expect --color always "success"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Match |
| `1` | Mismatch (prints diff to stderr) |
| `2` | Invalid arguments or file error |

## Using with Documentation Tools

### mktestdocs

With mktestdocs, bash blocks only verify exit code 0. Use `expect` to verify output content:

```markdown
# Example: Check Python version

```bash
python --version 2>&1 | expect --contains "Python 3"
```
```

### Recommended Shell Settings

For reliable documentation tests:

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures
```

## Troubleshooting

### "Why is output empty?"

The command might write to stderr. Redirect both streams:
```bash
python --version 2>&1 | expect --contains "Python"
```

### "Why did my pipeline pass when the command failed?"

Use `pipefail`:
```bash
set -o pipefail
failing_cmd | expect "never reached"  # Now fails correctly
```

### "Why does it fail on CI but not locally?"

Common causes:
- **Colors**: CI might enable/disable colors differently. Use `--strip-ansi`.
- **Locale**: Different systems might have different sorting. Be specific in expectations.
- **Newlines**: Windows vs Unix. Use `--normalize-newlines`.
- **Timestamps**: Use `--replace` or `--json-ignore`.

### "My output has ANSI colors"

```bash
mycli status | expect --strip-ansi --contains "OK"
# Or disable colors at source:
NO_COLOR=1 mycli status | expect --contains "OK"
```

### "Conflict with Tcl expect"

Use the unambiguous module invocation:
```bash
python -m doctest_expect --contains "test"
```

## Example: Testing a CLI Tool

```bash
#!/bin/bash
set -euo pipefail

# Test help output
mycli --help | expect --contains "Usage: mycli"

# Test version (with stderr redirect)
mycli --version 2>&1 | expect --regex 'mycli v\d+\.\d+\.\d+'

# Test JSON output (ignoring timestamps)
mycli status --json | expect --json --json-ignore '$.timestamp' '{"healthy": true}'

# Test list output (order may vary)
mycli list --jsonl | expect --jsonl-set '{"name": "bob"}
{"name": "alice"}'

# Test volatile output with replacement
mycli build | expect --replace '\d+ms' '<time>' "Built in <time>"
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check src tests
```

## License

MIT
