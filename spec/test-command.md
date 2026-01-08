# Spec: `outmatch test` Command

**Phase 2: Standalone Markdown Testing**

---

## Overview

The `outmatch test` command runs bash blocks in markdown files and reports results. It's a standalone test runner that doesn't require pytest or any test framework.

**Design goals:**
1. **Universal**: Works with any project (Python, Rust, Go, etc.)
2. **Simple**: Just point it at markdown files
3. **Fast**: Parallel execution by default
4. **Actionable**: Clear errors with line numbers

---

## Command Interface

```bash
outmatch test [OPTIONS] [FILES_OR_DIRS...]
```

### Positional Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `FILES_OR_DIRS` | Path(s) | Markdown files or directories to test (default: current directory) |

**Examples:**
```bash
outmatch test README.md                  # Single file
outmatch test docs/                      # Directory (recursive)
outmatch test docs/cli/ docs/api/        # Multiple paths
outmatch test docs/**/*.md               # Glob pattern
```

### Options

#### Verbosity

| Flag | Short | Description |
|------|-------|-------------|
| `--quiet` | `-q` | Only show pass/fail counts |
| `--verbose` | `-v` | Show full diffs for failures |
| (default) | | Show block-level pass/fail |

#### Execution Control

| Flag | Description | Default |
|------|-------------|---------|
| `--fail-fast` | Stop on first failure | `false` |
| `--parallel N` | Max concurrent blocks | `4` |
| `--timeout SECONDS` | Per-block timeout | `30` |
| `--shell PATH` | Shell to use | `/bin/bash` |

#### Filtering

| Flag | Description |
|------|-------------|
| `--include PATTERN` | Only run blocks matching pattern (regex) |
| `--exclude PATTERN` | Skip blocks matching pattern |
| `--line N` | Only run block at line N |

#### Output Format

| Flag | Description |
|------|-------------|
| `--junit-xml FILE` | Write JUnit XML report |
| `--json FILE` | Write JSON report |
| `--tap` | TAP (Test Anything Protocol) output |

#### Environment

| Flag | Description |
|------|-------------|
| `--env KEY=VALUE` | Set environment variable (repeatable) |
| `--cwd PATH` | Working directory for blocks |

---

## Markdown Parsing

### Block Detection

Detect bash code blocks using standard markdown fences:

````markdown
```bash
echo "hello"
```

```sh
# Also recognized
echo "world"
```

```shell
# Also recognized
echo "!"
```
````

**Block identifiers:** ` ```bash `, ` ```sh `, ` ```shell `

**Ignored blocks:**
- ` ```bash-example ` (example, not executable)
- ` ```text `, ` ```console ` (output examples)
- Any non-bash language tag

### Block Metadata (Optional)

Support markdown comments for block configuration:

````markdown
<!-- outmatch: timeout=60 -->
```bash
long_running_command
```

<!-- outmatch: skip -->
```bash
# This block won't run
```

<!-- outmatch: env=DEBUG=1,VERBOSE=1 -->
```bash
mycli --debug
```
````

**Metadata directives:**
- `timeout=N` - Override timeout for this block
- `skip` - Skip this block
- `skip-if=CONDITION` - Skip if env var set
- `env=KEY=VALUE,KEY2=VALUE2` - Set environment

---

## Execution Model

### Sequential Execution Within File

Blocks in the same file run **sequentially** by default. This allows:

````markdown
Initialize database:
```bash
createdb testdb
```

Run migration:
```bash
migrate --db testdb
```

Test query:
```bash
psql testdb -c "SELECT * FROM users" | outmatch --contains "alice"
```

Cleanup:
```bash
dropdb testdb
```
````

**State**: Each block sees environment changes from previous blocks in the same file.

### Parallel Execution Across Files

Multiple files execute in **parallel** (up to `--parallel` limit):

```
Running tests...
[docs/cli.md    ] ████████████████████ 5/5 blocks
[docs/api.md    ] ████████████████████ 3/3 blocks
[docs/guides.md ] ████████████████████ 7/7 blocks
```

### Isolation

Each file gets:
- Fresh shell process
- Clean environment (unless `--env` specified)
- Working directory set to file's directory or `--cwd`

---

## Assertion Detection

### Explicit Assertions

Detect `| outmatch` patterns in bash blocks:

````markdown
```bash
echo "hello world" | outmatch "hello world"
```
````

**Detection rules:**
1. Line contains `| outmatch` or `|outmatch`
2. Parse outmatch flags and expected value
3. Capture command output before pipe
4. Run outmatch comparison
5. Report result

### Implicit Success

Blocks without `| outmatch` use exit code only:

````markdown
```bash
# Exit 0 = pass, non-zero = fail
make build
```
````

### Chained Assertions

Support multiple assertions in one block:

````markdown
```bash
mycli users | outmatch --jsonl-contains '{"name": "alice"}'
mycli status | outmatch --contains "running"
```
````

Each assertion is tracked separately.

---

## Error Reporting

### Verbosity Levels

#### `--quiet` (Minimal)

```
Running tests in 3 files...
✓ 12 passed, ✗ 1 failed, 13 total
```

Exit code 0 if all pass, 1 if any fail.

#### Default (Block-level)

```
Running tests in docs/cli.md...

  ✓ Block 1 (line 23): Basic usage
  ✓ Block 2 (line 45): Version check
  ✗ Block 3 (line 67): Help text
  ✓ Block 4 (line 89): List command

Results: 3 passed, 1 failed, 4 total
```

Shows which blocks failed with line numbers.

#### `--verbose` (Full diffs)

```
Running tests in docs/cli.md...

  ✓ Block 1 (line 23): Basic usage
  ✗ Block 3 (line 67): Help text

    Command: findterms --help | outmatch --contains "Usage:"

    Expected (contains):
      Usage:

    Actual:
      findterms - Fast term extraction

      USAGE:
        findterms [OPTIONS] <COMMAND>

    Error: Substring not found

    docs/cli.md:67-72

Results: 3 passed, 1 failed, 4 total
```

Shows full diffs with context.

### Error Message Format

**Components:**
1. File and line number (`docs/cli.md:67`)
2. Block description (extracted from heading or first comment)
3. Failed command
4. Expected vs actual
5. Error type (mismatch, timeout, exit code, etc.)

**Line number calculation:**
- Report starting line of bash fence
- Include ending line if block spans multiple lines
- Format: `file.md:23-45` for multi-line blocks

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All tests passed |
| `1` | One or more tests failed |
| `2` | Invalid usage (bad arguments, file not found) |
| `124` | Timeout exceeded |

---

## Output Formats

### JUnit XML

```bash
outmatch test docs/ --junit-xml=test-results.xml
```

**Format:**
```xml
<testsuite name="outmatch" tests="13" failures="1" errors="0" time="5.2">
  <testcase classname="docs.cli" name="Block 1 (line 23)" time="0.4"/>
  <testcase classname="docs.cli" name="Block 3 (line 67)" time="0.8">
    <failure message="Assertion failed">
      Expected (contains): Usage:
      Actual: findterms - Fast term extraction
    </failure>
  </testcase>
</testsuite>
```

**Use case:** CI integration (Jenkins, GitLab CI, GitHub Actions)

### JSON

```bash
outmatch test docs/ --json=results.json
```

**Format:**
```json
{
  "summary": {
    "total": 13,
    "passed": 12,
    "failed": 1,
    "duration": 5.2
  },
  "files": [
    {
      "path": "docs/cli.md",
      "blocks": [
        {
          "line": 23,
          "name": "Basic usage",
          "status": "passed",
          "duration": 0.4
        },
        {
          "line": 67,
          "name": "Help text",
          "status": "failed",
          "error": "Assertion failed",
          "expected": "Usage:",
          "actual": "findterms - Fast term extraction",
          "duration": 0.8
        }
      ]
    }
  ]
}
```

**Use case:** Custom reporting, dashboards

### TAP (Test Anything Protocol)

```bash
outmatch test docs/ --tap
```

**Format:**
```tap
TAP version 13
1..13
ok 1 - docs/cli.md:23 Basic usage
ok 2 - docs/cli.md:45 Version check
not ok 3 - docs/cli.md:67 Help text
  ---
  message: Assertion failed
  expected: Usage:
  actual: findterms - Fast term extraction
  ...
ok 4 - docs/cli.md:89 List command
```

**Use case:** TAP-compatible test harnesses

---

## Implementation Details

### File Discovery

**Algorithm:**
1. Expand globs in `FILES_OR_DIRS`
2. If path is directory, recursively find `*.md` files
3. Filter by `--include` / `--exclude` patterns
4. Sort for deterministic order

**Default patterns:**
- Include: `**/*.md`
- Exclude: `node_modules/`, `.git/`, `_site/`, `build/`

### Markdown Parser

**Requirements:**
- Parse standard markdown fences
- Extract language tag (` ```bash `)
- Capture block content
- Track line numbers
- Extract heading context for block names

**Library options:**
- `markdown-it-py` (Python markdown parser)
- `commonmark` (CommonMark spec implementation)
- Custom regex-based parser (simpler, faster)

**Recommended:** Custom regex parser for speed and control.

### Outmatch Detection Regex

```python
# Detect: cmd | outmatch [flags] "expected"
OUTMATCH_PATTERN = re.compile(
    r'\|\s*outmatch\b'  # Pipe followed by outmatch
)

# Parse outmatch invocation
def parse_outmatch_line(line):
    # Split on pipe
    cmd, assertion = line.split('|', 1)

    # Parse assertion flags and expected
    # This reuses outmatch CLI parser
    args = shlex.split(assertion)
    config = parse_outmatch_args(args)

    return cmd.strip(), config
```

### Execution Pipeline

**Per file:**
1. Parse markdown → list of blocks
2. For each block:
   - Check metadata (skip, timeout, env)
   - Execute bash in subprocess
   - Capture stdout/stderr
   - If contains `| outmatch`: run assertion
   - Otherwise: check exit code
   - Record result
3. Aggregate results

**Parallel execution:**
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=parallel) as executor:
    futures = [executor.submit(test_file, path) for path in files]
    results = [f.result() for f in futures]
```

### Timeout Handling

```python
import subprocess

proc = subprocess.Popen(
    ["bash", "-c", block_content],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

try:
    stdout, stderr = proc.communicate(timeout=timeout)
except subprocess.TimeoutExpired:
    proc.kill()
    return BlockResult(
        status="timeout",
        error=f"Block exceeded {timeout}s timeout"
    )
```

---

## Configuration File

**Optional:** Support `.outmatch.toml` for project defaults:

```toml
[test]
parallel = 8
timeout = 60
fail-fast = false
shell = "/bin/bash"

[test.env]
# Default environment variables
NO_COLOR = "1"
CI = "1"

[test.exclude]
patterns = [
    "**/node_modules/**",
    "**/vendor/**",
]
```

**Location:** Search up from current directory for `.outmatch.toml`

---

## Examples

### Basic Usage

```bash
# Test all markdown in docs/
outmatch test docs/

# Single file
outmatch test README.md

# Quiet mode for CI
outmatch test docs/ --quiet
```

### CI Integration

```yaml
# .github/workflows/test.yml
- name: Test documentation
  run: |
    outmatch test docs/ --junit-xml=results.xml

- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: results.xml
```

### With Environment Variables

```bash
# Set test database URL
outmatch test docs/ --env DATABASE_URL=postgres://localhost/test

# Multiple vars
outmatch test docs/ \
  --env NO_COLOR=1 \
  --env DEBUG=1
```

### Filtering

```bash
# Only run specific section
outmatch test docs/cli.md --line 45

# Skip slow tests
outmatch test docs/ --exclude 'performance|benchmark'

# Only run quickstart
outmatch test docs/ --include 'quickstart|getting-started'
```

### Debugging

```bash
# Verbose output with full diffs
outmatch test docs/cli.md --verbose

# Stop on first failure
outmatch test docs/ --fail-fast

# Increase timeout for slow commands
outmatch test docs/perf.md --timeout 300
```

---

## Edge Cases

### Multi-line Commands

````markdown
```bash
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice"}' \
  | outmatch --json '{"id": 1, "name": "alice"}'
```
````

**Handling:** Bash handles multi-line naturally (backslash continuation).

### Heredocs

````markdown
```bash
cat <<EOF | outmatch "hello world"
hello world
EOF
```
````

**Handling:** Bash handles heredocs naturally.

### Chained Pipes

````markdown
```bash
echo "hello world" | tr '[:lower:]' '[:upper:]' | outmatch "HELLO WORLD"
```
````

**Handling:** Execute full pipeline, only check final outmatch result.

### Exit Code + Assertion

````markdown
```bash
# Command must succeed AND output must match
mycli build && echo "Success" | outmatch "Success"
```
````

**Handling:** Bash `&&` handles conditional execution.

### Background Jobs

````markdown
```bash
# Start server in background
myserver --port 8080 &
SERVER_PID=$!

# Test endpoint
sleep 1
curl localhost:8080/health | outmatch --contains "ok"

# Cleanup
kill $SERVER_PID
```
````

**Handling:** Works naturally - blocks run sequentially in same shell session.

---

## Performance Targets

| Metric | Target |
|--------|--------|
| File discovery | < 100ms for 1000 files |
| Parse single file | < 10ms for 1000-line file |
| Execute empty block | < 50ms |
| Parallel overhead | < 200ms startup |
| Memory per file | < 10MB |

**Optimization strategies:**
- Lazy file parsing (only parse when executing)
- Process pool reuse
- Streaming output (don't buffer entire file)

---

## Testing Strategy

**Self-hosted:** Use `outmatch test` to test itself.

Create `tests/integration/test_command.md` with:
- Basic file execution
- Error cases
- Output format validation
- Parallel execution
- Timeout handling

**Coverage target:** 100% of `outmatch test` code covered by its own tests.

---

## Future Enhancements

### Phase 2.1: Interactive Mode

```bash
outmatch test docs/ --interactive
# On failure: [U]pdate expected, [S]kip, [R]etry, [Q]uit
```

### Phase 2.2: Watch Mode

```bash
outmatch test docs/ --watch
# Reruns on file changes
```

### Phase 2.3: Snapshot Management

```bash
outmatch test docs/ --update-snapshots
# Bulk update all expected values
```

---

## Migration from mktestdocs

**For users coming from mktestdocs + pytest:**

**Before:**
```python
# tests/test_docs.py
from mktestdocs import check_md_file

def test_cli_docs():
    check_md_file("docs/cli.md", lang="bash")
```

**After:**
```bash
# No Python needed
outmatch test docs/cli.md
```

**Benefits:**
- No pytest dependency
- Faster startup
- Better error messages
- Works with any language

---

## Success Metrics

After Phase 2 implementation:

1. **Adoption:** Used in FindTerms and BotAssembly
2. **Speed:** Test 100 markdown files in < 5 seconds
3. **Clarity:** Errors immediately actionable
4. **Reliability:** No false positives from environment differences
5. **Universality:** Works with Rust/Go/any CLI project
