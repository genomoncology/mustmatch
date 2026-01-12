# CLI Reference

Complete reference for outmatch command-line options.

## Version

```bash
outmatch --version | outmatch --contains "0.2.0"
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

Normalization:
  --strip-ansi           Remove ANSI escape codes
  --normalize-newlines   Convert CRLF to LF
  --trim                 Strip leading/trailing whitespace
  --collapse-whitespace  Collapse whitespace runs
  -i, --ignore-case      Case-insensitive comparison

Transformation:
  --replace REGEX=>REPL  Replace pattern (repeatable)
  --redact REGEX         Replace with <redacted> (repeatable)
  --json-ignore PATH     Ignore JSON path (repeatable)

Files:
  -f, --expected-file    Read expected from file
  --update               Update file on mismatch

Output:
  -q, --quiet            Suppress all output
  --color MODE           auto | always | never
  --diff-context N       Context lines in diff (default: 3)

Info:
  --version              Show version and exit
  --help                 Show help and exit
```
