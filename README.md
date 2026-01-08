# outmatch

CLI output assertion tool for documentation testing. Pipe command output to `outmatch` to verify it matches expected values.

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
uv add --group dev outmatch
```

Or install globally:
```bash
uv tool install outmatch
pipx install outmatch
```

## Quickstart

```bash
# Exact match
echo "hello world" | outmatch "hello world"

# Contains substring
python --version 2>&1 | outmatch --contains "Python"

# Regex for volatile output
mycli run | outmatch --regex 'completed in \d+\.\d+s'

# JSON semantic comparison (field order independent)
echo '{"b": 2, "a": 1}' | outmatch --json '{"a": 1, "b": 2}'
```

**Important**: Many commands write to stderr (e.g., `python --version` on some systems). Use `2>&1` to capture both streams:
```bash
python --version 2>&1 | outmatch --contains "Python"
```

**Pipeline exit codes**: In bash, `cmd | outmatch` returns `outmatch`'s exit code, not `cmd`'s. To fail when `cmd` fails:
```bash
set -o pipefail
mycli run | outmatch "success"
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
echo "hello world" | outmatch "hello world"
```

### Contains

Checks if output contains the expected substring.

```bash
python --help | outmatch --contains "usage:"
```

### Regex

Matches output against a regex pattern. Uses Python's `re` with `MULTILINE` and `DOTALL` flags.

```bash
mycli build | outmatch --regex 'built in \d+ms'
mycli logs | outmatch --regex 'ERROR:.*connection refused'
```

### JSON

Compares single JSON values semantically. Field order doesn't matter.

```bash
echo '{"name": "alice", "age": 30}' | outmatch --json '{"age": 30, "name": "alice"}'
```

### JSONL

Compares JSON Lines output. Field order within records doesn't matter, but record order does.

```bash
echo '{"id": 1}
{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
```

### JSONL Set

Order-independent JSONL comparison (multiset semantics).

```bash
mycli list | outmatch --jsonl-set '{"id": 2}
{"id": 1}'
```

### JSONL Key

Match records by a key field, then compare. Useful for stable docs when record order varies.

```bash
mycli users | outmatch --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

### JSONL Contains

Check that output contains expected records. Partial field matching supported.

```bash
mycli users | outmatch --jsonl-contains '{"name": "alice"}'
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
mycli status | outmatch --contains "OK" --strip-ansi

# Handle Windows line endings
mycli export | outmatch --normalize-newlines -f expected.txt

# Flexible whitespace matching
mycli format | outmatch --trim --collapse-whitespace "hello world"
```

## Pattern Transformation

For nondeterministic output (timestamps, durations, IDs, temp paths), use pattern replacement.

### Replace

Replace regex patterns before comparison. Repeatable.

```bash
mycli run | outmatch --replace '\d+\.\d+s' '<time>' "completed in <time>"
mycli build | outmatch --replace '/tmp/[a-z0-9]+' '<tmpdir>' "output: <tmpdir>/result.txt"
```

### Redact

Replace patterns with `<redacted>`. Repeatable.

```bash
mycli token | outmatch --redact '[a-f0-9]{32}' "token: <redacted>"
```

## JSON Options

### Ignore Paths

Ignore volatile JSON fields during comparison. Uses JSONPath-like syntax.

```bash
# Ignore timestamp field
mycli audit | outmatch --json --json-ignore '$.timestamp' '{"status": "ok"}'

# Ignore nested field
mycli user | outmatch --json --json-ignore '$.metadata.updated_at' '{"name": "alice"}'

# Multiple ignores
mycli export | outmatch --jsonl --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'
```

## Expected from File

For multi-line expectations, use `-f`/`--expected-file` instead of command substitution.

```bash
# Much cleaner than heredocs
mycli help | outmatch -f docs/expected/help.txt

# Works with all modes
mycli export | outmatch --jsonl -f expected/records.jsonl
```

## Snapshot Updates

Automatically update expected files when output changes. Useful for maintaining documentation.

```bash
# Update expected file if mismatch
mycli help | outmatch -f docs/expected/help.txt --update
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
mycli run | outmatch -q "success"

# Force colors in CI
mycli run | outmatch --color always "success"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Match |
| `1` | Mismatch (prints diff to stderr) |
| `2` | Invalid arguments or file error |

## Using with Documentation Tools

### mktestdocs

With mktestdocs, bash blocks only verify exit code 0. Use `outmatch` to verify output content:

```markdown
# Example: Check Python version

```bash
python --version 2>&1 | outmatch --contains "Python 3"
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
python --version 2>&1 | outmatch --contains "Python"
```

### "Why did my pipeline pass when the command failed?"

Use `pipefail`:
```bash
set -o pipefail
failing_cmd | outmatch "never reached"  # Now fails correctly
```

### "Why does it fail on CI but not locally?"

Common causes:
- **Colors**: CI might enable/disable colors differently. Use `--strip-ansi`.
- **Locale**: Different systems might have different sorting. Be specific in expectations.
- **Newlines**: Windows vs Unix. Use `--normalize-newlines`.
- **Timestamps**: Use `--replace` or `--json-ignore`.

### "My output has ANSI colors"

```bash
mycli status | outmatch --strip-ansi --contains "OK"
# Or disable colors at source:
NO_COLOR=1 mycli status | outmatch --contains "OK"
```

## Example: Testing a CLI Tool

```bash
#!/bin/bash
set -euo pipefail

# Test help output
mycli --help | outmatch --contains "Usage: mycli"

# Test version (with stderr redirect)
mycli --version 2>&1 | outmatch --regex 'mycli v\d+\.\d+\.\d+'

# Test JSON output (ignoring timestamps)
mycli status --json | outmatch --json --json-ignore '$.timestamp' '{"healthy": true}'

# Test list output (order may vary)
mycli list --jsonl | outmatch --jsonl-set '{"name": "bob"}
{"name": "alice"}'

# Test volatile output with replacement
mycli build | outmatch --replace '\d+ms' '<time>' "Built in <time>"
```

## Standalone Markdown Testing

The `outmatch test` command runs bash code blocks in markdown files directly, without requiring pytest or mktestdocs.

```bash
# Test all markdown files in current directory
outmatch test

# Test specific file or directory
outmatch test docs/cli.md
outmatch test docs/

# Verbose output
outmatch test -v docs/

# Generate JUnit XML report
outmatch test --junit-xml results.xml docs/
```

### Options

| Flag | Effect |
|------|--------|
| `-q`, `--quiet` | Only show pass/fail counts |
| `-v`, `--verbose` | Show full output for failures |
| `--fail-fast` | Stop on first failure |
| `--parallel N` | Max concurrent files (default: 4) |
| `--timeout N` | Per-block timeout in seconds (default: 30) |
| `--include PATTERN` | Only run blocks matching pattern |
| `--exclude PATTERN` | Skip blocks matching pattern |
| `--line N` | Only run block at line N |
| `--junit-xml PATH` | Write JUnit XML report |
| `--json PATH` | Write JSON report |
| `--tap` | Output in TAP format |
| `--env KEY=VALUE` | Set environment variable |
| `--cwd PATH` | Working directory for blocks |

### Metadata Directives

Control block behavior with HTML comments:

```markdown
<!-- outmatch: skip -->
```bash
# This block will be skipped
echo "skipped"
```

<!-- outmatch: skip-if=CI -->
```bash
# This block is skipped when CI environment variable is set
interactive_command
```

<!-- outmatch: timeout=60 -->
```bash
# This block has a 60 second timeout
long_running_command
```

<!-- outmatch: env=DEBUG=1,VERBOSE=true -->
```bash
# This block runs with custom environment variables
echo $DEBUG $VERBOSE
```
```

| Directive | Effect |
|-----------|--------|
| `skip` | Always skip this block |
| `skip-if=VAR` | Skip if environment variable VAR is set |
| `timeout=N` | Override timeout to N seconds |
| `env=K=V,...` | Set environment variables for block |

### Example Output

```
Running tests in docs/cli.md...

  ✓ Block (line 10): Installation
  ✓ Block (line 25): Basic Usage
  ✗ Block (line 40): JSON Example

Results: 2 passed, 1 failed, 3 total
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
