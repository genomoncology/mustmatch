# CLI Reference

Complete reference for the mustmatch command-line interface.

## Synopsis

```
mustmatch [OPTIONS] [not] [like] EXPECTED
mustmatch test [OPTIONS] PATHS
mustmatch --version
mustmatch --help
```

## Commands

### Match Command (Default)

Reads stdin and compares to expected value.

```
mustmatch [OPTIONS] [not] [like] EXPECTED
```

**Positional Arguments:**
- `not` (optional) - Invert the match
- `like` (optional) - Use substring/subset matching
- `EXPECTED` (required) - Expected value

**Options:**
- `-i, --ignore-case` - Case-insensitive comparison
- `-q, --quiet` - Suppress error output
- `-h, --help` - Show help message

**Exit Codes:**
- `0` - Match succeeded
- `1` - Match failed
- `2` - Invalid arguments

**Examples:**

```bash
# Exact match
echo "hello" | mustmatch "hello"

# Substring match
echo "hello world" | mustmatch like "world"

# Negation
echo "success" | mustmatch not "error"

# Combination
echo "SUCCESS" | mustmatch -i not like "error"
```

### Test Command

Test code blocks in markdown files.

```
mustmatch test [OPTIONS] PATHS...
```

**Positional Arguments:**
- `PATHS` - Files or directories to test (default: current directory)

**Options:**
- `-v, --verbose` - Show result for each test
- `-q, --quiet` - Minimal output (only summary)
- `-x, --fail-fast` - Stop on first failure
- `--timeout N` - Timeout per block in seconds (default: 30)
- `--lang LANG` - Language filter: `bash`, `python`, or `all` (default: `all`)
- `--memory` - Share Python state between blocks
- `-h, --help` - Show help message

**Exit Codes:**
- `0` - All tests passed
- `1` - Some tests failed
- `2` - Invalid arguments

**Examples:**

```bash skip
# Test single file
mustmatch test README.md

# Test directory
mustmatch test docs/

# Verbose output
mustmatch test -v docs/

# Fail fast
mustmatch test -x docs/

# Test only bash blocks
mustmatch test --lang bash docs/

# Test with memory mode
mustmatch test --memory tutorial.md

# Multiple paths
mustmatch test README.md docs/ examples/
```

### Version Command

Show version information.

```
mustmatch --version
```

**Output:**
```
mustmatch 0.0.0.dev0
```

### Help Command

Show help message.

```
mustmatch --help
mustmatch -h
```

## Comparison Modes

Automatically detected from syntax:

### Exact Match

Default mode when expected value is plain text.

```bash
echo "hello" | mustmatch "hello"
```

### Contains (like)

Use `like` keyword for substring matching.

```bash
echo "hello world" | mustmatch like "world"
```

For JSON, `like` means subset matching:

```bash
echo '{"a":1,"b":2}' | mustmatch like '{"a":1}'
```

### Negation (not)

Use `not` keyword to invert any match.

```bash
echo "success" | mustmatch not "error"
echo "success" | mustmatch not like "error"
```

### Regular Expression

Wrap pattern in `/slashes/` for regex matching.

```bash
echo "v1.2.3" | mustmatch '/v\d+\.\d+\.\d+/'
```

### JSON

Starts with `{` or `[` for semantic JSON comparison.

```bash
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'
```

### JSONL

Multiple JSON objects on separate lines.

```bash skip
printf '{"id":1}\n{"id":2}' | mustmatch '{"id":1}\n{"id":2}'
```

## Text Normalization

mustmatch automatically normalizes text:

### Always Applied

1. **Strip ANSI escape sequences** - Color codes removed
2. **Normalize newlines** - CRLF → LF
3. **Trim whitespace** - Leading/trailing whitespace removed

```bash
# These all match
echo "  hello  " | mustmatch "hello"
printf "hello\r\n" | mustmatch "hello"
echo -e "\033[31mhello\033[0m" | mustmatch "hello"
```

### Optional

**Case-insensitive** (with `-i` flag):

```bash
echo "HELLO" | mustmatch -i "hello"
```

## Block Directives

Control test behavior in markdown code fences.

### Skip Directive

Skip a code block:

````markdown
```bash skip
echo "not executed"
```
````

### Timeout Directive

Custom timeout per block:

````markdown
```bash skip timeout=60
sleep 10
echo "slow operation"
```
````

Default timeout is 30 seconds.

### Combined Directives

````markdown
```bash skip timeout=120
# Both directives applied
```
````

## Environment Variables

None currently. Configuration is via command-line flags only.

## Configuration Files

No configuration files. All options are command-line only.

## Exit Codes Summary

| Code | Meaning | Command |
|------|---------|---------|
| 0 | Success | Both |
| 1 | Match failed / Tests failed | Both |
| 2 | Invalid arguments | Both |

## Output Format

### Match Command

**On success:**
- Exit 0
- No output (unless error redirection shows it)

**On failure:**
- Exit 1
- Stderr: diff (for exact match) or error message

**Quiet mode:**
- Exit code only, no stderr output

### Test Command

**Default output:**
```
5 passed, 2 failed, 1 skipped
```

**Verbose output:**
```
PASS docs/intro.md:5 [bash]
PASS docs/intro.md:12 [python]
FAIL docs/api.md:8 unnamed - exit 1
  Error: Connection refused
3 passed, 1 failed
```

**Quiet output:**
```
(nothing unless failures)
```

## Input/Output

### Match Command

**Input:** stdin (command output)
**Output:** exit code, stderr (errors)

```bash
# Typical usage
command | mustmatch expected

# Capture output
OUTPUT=$(command)
echo "$OUTPUT" | mustmatch expected
```

### Test Command

**Input:** markdown files
**Output:** test results to stdout/stderr, exit code

```bash
# Typical usage
mustmatch test docs/

# Capture output
mustmatch test docs/ 2>&1 | tee test-results.txt
```

## Working Directory

### Match Command

Uses current working directory for any operations.

### Test Command

Bash blocks run with `cwd` set to the markdown file's parent directory:

```
docs/
  api.md          # Bash blocks here run in docs/
  tutorials/
    intro.md      # Bash blocks here run in docs/tutorials/
```

This allows relative paths in examples:

````markdown
<!-- docs/tutorials/intro.md -->

```bash
ls ../api.md | mustmatch "api.md"
```
````

## Error Messages

### Match Command

**Exact match failure:**
```
--- expected
+++ actual
@@ -1 +1 @@
-hello
+goodbye
```

**Contains failure:**
```
Expected substring not found: 'world'
Actual: 'hello'
```

**Regex failure:**
```
Pattern /\d+/ did not match
Actual: 'no numbers'
```

**JSON failure:**
```
--- expected
+++ actual
@@ -1,3 +1,3 @@
 {
-  "a": 1
+  "a": 2
 }
```

**Negation failure:**
```
FAIL: Expected NOT to match, but it did
```

### Test Command

**Block failure:**
```
FAIL docs/api.md:15 unnamed - exit 1
  Error message here
```

**Timeout:**
```
FAIL docs/slow.md:8 slow-operation - timeout after 30s
```

**No markdown files:**
```
No markdown files found
```

## stdin Detection

mustmatch detects if stdin is a TTY:

```bash
# stdin is TTY (interactive) - show help
mustmatch

# stdin has data - read it
echo "hello" | mustmatch "hello"
```

## Language Support

### Bash

Runs via subprocess:

```python
subprocess.run(['bash', '-c', code], ...)
```

### Python

Runs via `exec()` in controlled namespace:

```python
exec(code, globals_dict)
```

## Comparison to Other Tools

| Tool | Purpose | mustmatch Equivalent |
|------|---------|---------------------|
| `grep` | Find patterns | `mustmatch like "pattern"` |
| `test`/`[[]]` | Test conditions | `mustmatch` (for output) |
| `diff` | Compare files | `mustmatch` (exact mode) |
| `jq` | Query JSON | `mustmatch` (JSON mode) |

## Tips

### Debugging Failed Matches

```bash
# See what mustmatch received
OUTPUT=$(command)
echo "Output: $OUTPUT"
echo "$OUTPUT" | mustmatch expected
```

### Using with set -e

```bash skip
#!/bin/bash
set -e  # Exit on error

# Any mustmatch failure stops script
echo "test" | mustmatch "test" || exit 1
```

### Combining Multiple Checks

```bash skip
# All must pass
command | {
    read DATA
    echo "$DATA" | mustmatch like "success" || exit 1
    echo "$DATA" | mustmatch not like "error" || exit 1
    echo "✓ All checks passed"
}
```

### Testing mustmatch Itself

```bash
# Test help output
mustmatch --help | mustmatch like "Usage:"

# Test version
mustmatch --version | mustmatch like "mustmatch"

# Test exit codes
echo "test" | mustmatch "test"
echo $?  # Should be 0
```
