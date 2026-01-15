# CLI Reference

Complete reference for mustmatch command-line options.

## Version

```bash
mustmatch --version | mustmatch --contains "0.0.0.dev0"
```

## Exit Codes

| Code | Meaning                                      |
|------|----------------------------------------------|
| 0    | Match - output matched expected value        |
| 1    | Mismatch - output differs from expected      |
| 2    | Error - invalid arguments, bad regex, etc.   |

```bash
# Exit 0 on match
echo "hello" | mustmatch "hello"

# Exit 1 on mismatch
echo "hello" | mustmatch "world" || test $? -eq 1

# Exit 2 on error (missing expected value)
echo "test" | mustmatch 2>&1 || test $? -eq 2
```

## Quiet Mode

Suppress all output, use exit code only. Useful in scripts:

```bash
# -q / --quiet suppresses output
if echo "hello" | mustmatch -q "hello"; then
    echo "matched"
fi
```

Verify no output is produced:

```bash
output=$(echo "hello" | mustmatch --quiet "world" 2>&1) || true
test -z "$output"
```

## Color Control

Control ANSI color output with `--color`:

| Value    | Behavior                        |
|----------|---------------------------------|
| `auto`   | Color if stderr is a TTY        |
| `always` | Always use color                |
| `never`  | Never use color                 |

```bash
# Force no color
echo "hello" | mustmatch --color never "world" 2>&1 | \
    mustmatch --contains "FAIL"

# Force color
echo "hello" | mustmatch --color always "world" 2>&1 | \
    mustmatch --contains "FAIL"
```

## Diff Context

Control how many context lines appear in diffs with `--diff-context`:

```bash
# Default is 3 lines of context
echo "actual" | mustmatch "expected" 2>&1 | \
    mustmatch --contains "actual"

# Show more context
echo "actual" | mustmatch --diff-context 5 "expected" 2>&1 | \
    mustmatch --contains "actual"
```

## Diff Format

Control the diff output format with `--diff-format`:

| Value         | Description                              |
|---------------|------------------------------------------|
| `unified`     | Standard unified diff (default)          |
| `side-by-side`| Side-by-side comparison                  |
| `inline`      | Word-level inline diff                   |
| `none`        | No diff output, just pass/fail message   |

```bash
# Side-by-side diff
echo "hello world" | mustmatch --diff-format side-by-side "hello there" 2>&1 | \
    mustmatch --contains "expected"

# Inline word-level diff
echo "hello world" | mustmatch --diff-format inline "hello there" 2>&1 | \
    mustmatch --contains "[-there-]"

# No diff output
echo "hello" | mustmatch --diff-format none "world" 2>&1 | \
    mustmatch "FAIL: Exact match failed."
```

## Negative Assertions

Assert that content is NOT present with `--not-contains` and `--not-regex`:

```bash
# Assert substring is absent
echo "hello world" | mustmatch --not-contains "error"

# Assert regex does not match
echo "success: ok" | mustmatch --not-regex "[Ee]rror|FAIL"

# Fails when pattern is found
echo "Error occurred" | mustmatch --not-contains "Error" 2>&1 | \
    mustmatch --contains "Expected NOT to contain"
```

## File-Based Expected Values

Read expected value from a file with `-f` / `--expected-file`:

```bash
# Create expected file
echo "test content" > /tmp/expected.txt
echo "test content" | mustmatch -f /tmp/expected.txt
rm /tmp/expected.txt

# Works with all comparison modes
echo '{"id": 1}' > /tmp/expected.json
echo '{"id": 1}' | mustmatch --json -f /tmp/expected.json
rm /tmp/expected.json
```

Missing files return exit code 2:

```bash
echo "test" | mustmatch -f /nonexistent.txt 2>&1 | \
    mustmatch --contains "not found"
```

## Snapshot Updates

Update expected files when output changes with `--update`:

```bash
# Create snapshot on first run
rm -f /tmp/snapshot.txt
echo "new content" | mustmatch -f /tmp/snapshot.txt --update
cat /tmp/snapshot.txt | mustmatch "new content"

# Update existing snapshot
echo "updated" | mustmatch -f /tmp/snapshot.txt --update
cat /tmp/snapshot.txt | mustmatch "updated"
rm /tmp/snapshot.txt
```

## Error Messages

Common error messages and their meanings:

**Missing expected value:**
```bash
echo "test" | mustmatch 2>&1 | mustmatch --contains "expected"
```

**Invalid --replace format** (must be `REGEX=>REPL`):
```bash
echo "test" | mustmatch --replace 'bad' "test" 2>&1 | \
    mustmatch --contains "REGEX=>REPL"
```

**Invalid regex pattern:**
```bash
echo "test" | mustmatch --regex '[invalid' 2>&1 | \
    mustmatch --contains "Invalid regex"
```

**Invalid JSON in actual output:**
```bash
echo "not json" | mustmatch --json '{}' 2>&1 | \
    mustmatch --contains "not valid JSON"
```

**Invalid JSON in expected value:**
```bash
echo '{}' | mustmatch --json 'not json' 2>&1 | \
    mustmatch --contains "not valid JSON"
```

**JSONL parse error:**
```bash
printf '{"a":1}\nnot json' | mustmatch --jsonl '{"a":1}' 2>&1 | \
    mustmatch --contains "JSON parse error"
```

## Command Execution Mode

Run a command and assert on its output with `mustmatch exec`:

```bash
# Assert exit code
mustmatch exec --exit-code 0 -- echo "hello"

# Assert stdout contains text
mustmatch exec --stdout-contains "hello" -- echo "hello world"

# Assert stderr is empty
mustmatch exec --stderr "" -- echo "output"

# Assert command fails
mustmatch exec --exit-code 1 -- false

# Multiple assertions
mustmatch exec --exit-code 0 --stdout-contains "done" --stderr "" -- echo "done"
```

### Combined JSON Output

Match all outputs at once with `--output-json` (supports wildcards):

```bash
# Match exit code and ignore stdout content
mustmatch exec --output-json '{"exit_code": 0, "stdout": "*", "stderr": ""}' -- echo "hello"
```

### Exec Options

| Option                | Description                           |
|-----------------------|---------------------------------------|
| `--exit-code N`       | Expected exit code                    |
| `--stdout TEXT`       | Expected stdout (exact)               |
| `--stdout-contains`   | Stdout must contain                   |
| `--stdout-not-contains` | Stdout must NOT contain             |
| `--stdout-regex`      | Stdout must match regex               |
| `--stdout-not-regex`  | Stdout must NOT match regex           |
| `--stderr TEXT`       | Expected stderr (exact)               |
| `--stderr-contains`   | Stderr must contain                   |
| `--stderr-not-contains` | Stderr must NOT contain             |
| `--stderr-regex`      | Stderr must match regex               |
| `--stderr-not-regex`  | Stderr must NOT match regex           |
| `--output-json`       | Match combined output as JSON         |
| `--timeout N`         | Command timeout in seconds            |

## Full Options List

```
mustmatch [OPTIONS] [EXPECTED]

Comparison modes:
  --contains             Substring match
  --regex                Regex pattern match
  --json                 JSON semantic comparison
  --jsonl                JSON Lines (order matters)
  --jsonl-set            JSON Lines (unordered)
  --jsonl-key FIELD      Match by key field
  --jsonl-contains       Subset matching

Negative assertions:
  --not-contains         Assert substring is absent
  --not-regex            Assert regex does not match

Normalization:
  --strip-ansi           Remove ANSI escape codes
  --normalize-newlines   Convert CRLF to LF
  --trim                 Strip leading/trailing whitespace
  --collapse-whitespace  Collapse whitespace runs
  -i, --ignore-case      Case-insensitive comparison

Transformation:
  --replace REGEX=>REPL  Replace pattern (repeatable)
  --redact REGEX         Replace with <redacted> (repeatable)
  --json-ignore PATH     Ignore JSON path (repeatable, supports [*])

Files:
  -f, --expected-file    Read expected from file
  --update               Update file on mismatch

Output:
  -q, --quiet            Suppress all output
  --color MODE           auto | always | never
  --diff-context N       Context lines in diff (default: 3)
  --diff-format FORMAT   unified | side-by-side | inline | none

Info:
  --version              Show version and exit
  --help                 Show help and exit

Subcommands:
  mustmatch exec          Execute command and assert on output
  mustmatch test          Run markdown documentation tests
```
