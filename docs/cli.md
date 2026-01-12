# CLI Reference

Complete reference for outmatch command-line options.

## Version

```bash
outmatch --version | outmatch --contains "0.3.0"
```

## Exit Codes

| Code | Meaning                                      |
|------|----------------------------------------------|
| 0    | Match - output matched expected value        |
| 1    | Mismatch - output differs from expected      |
| 2    | Error - invalid arguments, bad regex, etc.   |

```bash
# Exit 0 on match
echo "hello" | outmatch "hello"

# Exit 1 on mismatch
echo "hello" | outmatch "world" || test $? -eq 1

# Exit 2 on error (missing expected value)
echo "test" | outmatch 2>&1 || test $? -eq 2
```

## Quiet Mode

Suppress all output, use exit code only. Useful in scripts:

```bash
# -q / --quiet suppresses output
if echo "hello" | outmatch -q "hello"; then
    echo "matched"
fi
```

Verify no output is produced:

```bash
output=$(echo "hello" | outmatch --quiet "world" 2>&1) || true
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
echo "hello" | outmatch --color never "world" 2>&1 | \
    outmatch --contains "FAIL"

# Force color
echo "hello" | outmatch --color always "world" 2>&1 | \
    outmatch --contains "FAIL"
```

## Diff Context

Control how many context lines appear in diffs with `--diff-context`:

```bash
# Default is 3 lines of context
echo "actual" | outmatch "expected" 2>&1 | \
    outmatch --contains "actual"

# Show more context
echo "actual" | outmatch --diff-context 5 "expected" 2>&1 | \
    outmatch --contains "actual"
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
echo "hello world" | outmatch --diff-format side-by-side "hello there" 2>&1 | \
    outmatch --contains "expected"

# Inline word-level diff
echo "hello world" | outmatch --diff-format inline "hello there" 2>&1 | \
    outmatch --contains "[-there-]"

# No diff output
echo "hello" | outmatch --diff-format none "world" 2>&1 | \
    outmatch "FAIL: Exact match failed."
```

## Negative Assertions

Assert that content is NOT present with `--not-contains` and `--not-regex`:

```bash
# Assert substring is absent
echo "hello world" | outmatch --not-contains "error"

# Assert regex does not match
echo "success: ok" | outmatch --not-regex "[Ee]rror|FAIL"

# Fails when pattern is found
echo "Error occurred" | outmatch --not-contains "Error" 2>&1 | \
    outmatch --contains "Expected NOT to contain"
```

## File-Based Expected Values

Read expected value from a file with `-f` / `--expected-file`:

```bash
# Create expected file
echo "test content" > /tmp/expected.txt
echo "test content" | outmatch -f /tmp/expected.txt
rm /tmp/expected.txt

# Works with all comparison modes
echo '{"id": 1}' > /tmp/expected.json
echo '{"id": 1}' | outmatch --json -f /tmp/expected.json
rm /tmp/expected.json
```

Missing files return exit code 2:

```bash
echo "test" | outmatch -f /nonexistent.txt 2>&1 | \
    outmatch --contains "not found"
```

## Snapshot Updates

Update expected files when output changes with `--update`:

```bash
# Create snapshot on first run
rm -f /tmp/snapshot.txt
echo "new content" | outmatch -f /tmp/snapshot.txt --update
cat /tmp/snapshot.txt | outmatch "new content"

# Update existing snapshot
echo "updated" | outmatch -f /tmp/snapshot.txt --update
cat /tmp/snapshot.txt | outmatch "updated"
rm /tmp/snapshot.txt
```

## Error Messages

Common error messages and their meanings:

**Missing expected value:**
```bash
echo "test" | outmatch 2>&1 | outmatch --contains "expected"
```

**Invalid --replace format** (must be `REGEX=>REPL`):
```bash
echo "test" | outmatch --replace 'bad' "test" 2>&1 | \
    outmatch --contains "REGEX=>REPL"
```

**Invalid regex pattern:**
```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | \
    outmatch --contains "Invalid regex"
```

**Invalid JSON in actual output:**
```bash
echo "not json" | outmatch --json '{}' 2>&1 | \
    outmatch --contains "not valid JSON"
```

**Invalid JSON in expected value:**
```bash
echo '{}' | outmatch --json 'not json' 2>&1 | \
    outmatch --contains "not valid JSON"
```

**JSONL parse error:**
```bash
printf '{"a":1}\nnot json' | outmatch --jsonl '{"a":1}' 2>&1 | \
    outmatch --contains "JSON parse error"
```

## Command Execution Mode

Run a command and assert on its output with `outmatch exec`:

```bash
# Assert exit code
outmatch exec --exit-code 0 -- echo "hello"

# Assert stdout contains text
outmatch exec --stdout-contains "hello" -- echo "hello world"

# Assert stderr is empty
outmatch exec --stderr "" -- echo "output"

# Assert command fails
outmatch exec --exit-code 1 -- false

# Multiple assertions
outmatch exec --exit-code 0 --stdout-contains "done" --stderr "" -- echo "done"
```

### Combined JSON Output

Match all outputs at once with `--output-json` (supports wildcards):

```bash
# Match exit code and ignore stdout content
outmatch exec --output-json '{"exit_code": 0, "stdout": "*", "stderr": ""}' -- echo "hello"
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
outmatch [OPTIONS] [EXPECTED]

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
  outmatch exec          Execute command and assert on output
  outmatch test          Run markdown documentation tests
```
