# Markdown Test Runner

Test your documentation by running bash code blocks with `outmatch test`.

## Basic Usage

```console
outmatch test docs/              # Test all markdown in directory
outmatch test README.md          # Test single file
outmatch test docs/ README.md    # Test multiple paths
```

Test this documentation:

```bash
outmatch test docs/cli.md --quiet
```

## Output Modes

**Default** - Shows pass/fail per block with summary:

```bash
outmatch test docs/cli.md 2>&1 | outmatch --contains "Results:"
```

**Quiet** (`-q`) - Just the summary:

```bash
outmatch test docs/cli.md --quiet | outmatch --regex '\d+ passed'
```

**Verbose** (`-v`) - Full output including commands:

```bash
outmatch test docs/cli.md --verbose 2>&1 | \
    outmatch --contains "Block (line"
```

**TAP** - Test Anything Protocol format:

```bash
outmatch test docs/cli.md --tap | outmatch --contains "TAP version"
```

## Report Files

Generate reports for CI integration:

```bash
# JUnit XML (for Jenkins, GitLab CI, etc.)
outmatch test docs/cli.md --junit-xml /tmp/report.xml -q
cat /tmp/report.xml | outmatch --contains "testsuite"

# JSON report
outmatch test docs/cli.md --json /tmp/report.json -q
cat /tmp/report.json | outmatch --contains '"passed":'
```

## Filtering Tests

Run specific tests by name pattern or line number:

```bash
# Include only tests matching pattern
outmatch test docs/matching.md --include "Exact" -q | \
    outmatch --contains "passed"

# Exclude tests matching pattern
outmatch test docs/matching.md --exclude "Empty" -q | \
    outmatch --contains "passed"

# Run block at specific line
outmatch test docs/cli.md --line 8 -q | \
    outmatch --contains "1 passed"
```

## Block Directives

Control block execution with HTML comments before the code fence.

### Skip a Block

```markdown
<!-- outmatch: skip -->
` ` `bash
# This won't run
exit 1
` ` `
```

Test that skip works:

```bash
cat << 'EOF' > /tmp/skip-test.md
<!-- outmatch: skip -->
` ` `bash
exit 1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/skip-test.md
outmatch test /tmp/skip-test.md -q | outmatch --contains "1 skipped"
```

### Conditional Skip

Skip based on environment variable:

```markdown
<!-- outmatch: skip-if=CI -->
` ` `bash
# Skipped when CI=1
open https://example.com
` ` `
```

```bash
cat << 'EOF' > /tmp/skipif-test.md
<!-- outmatch: skip-if=SKIP_ME -->
` ` `bash
exit 1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/skipif-test.md
SKIP_ME=1 outmatch test /tmp/skipif-test.md -q | \
    outmatch --contains "1 skipped"
```

### Custom Timeout

Override the default 30-second timeout:

```markdown
<!-- outmatch: timeout=60 -->
` ` `bash
# Has 60 seconds to complete
long-running-command
` ` `
```

```bash
cat << 'EOF' > /tmp/timeout-test.md
<!-- outmatch: timeout=5 -->
` ` `bash
sleep 0.1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/timeout-test.md
outmatch test /tmp/timeout-test.md -q
```

### Block Environment Variables

Set variables for a specific block:

```markdown
<!-- outmatch: env=DEBUG=1,VERBOSE=true -->
` ` `bash
test "$DEBUG" = "1"
` ` `
```

```bash
cat << 'EOF' > /tmp/env-test.md
<!-- outmatch: env=TEST_VAR=hello -->
` ` `bash
test "$TEST_VAR" = "hello"
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/env-test.md
outmatch test /tmp/env-test.md -q
```

## Execution Options

| Flag              | Effect                                 |
|-------------------|----------------------------------------|
| `--fail-fast`     | Stop on first failure                  |
| `--parallel N`    | Run N files concurrently (default: 4)  |
| `--timeout N`     | Per-block timeout in seconds (default: 30) |
| `--shell PATH`    | Shell to use (default: /bin/bash)      |
| `--cwd PATH`      | Working directory for all tests        |
| `--env KEY=VAL`   | Set environment variable (repeatable)  |

## Working Directory

By default, each test runs in its markdown file's directory:

```bash
outmatch test docs/cli.md -q
```

Override with `--cwd`:

```bash
outmatch test docs/cli.md --cwd /tmp -q
```

Pass environment variables with `--env`:

```bash
cat << 'EOF' > /tmp/envflag-test.md
` ` `bash
test -n "$MY_VAR"
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/envflag-test.md
outmatch test /tmp/envflag-test.md --env MY_VAR=hello -q
```

## Test Names

Blocks get names from the nearest preceding heading or from
a comment on the first line of the block:

```markdown
## Installation

` ` `bash
# This block is named "Installation"
pip install outmatch
` ` `

` ` `bash
# Custom Name
# This block is named "Custom Name" (first comment line)
echo hello
` ` `
```

Verify naming works:

```bash
outmatch test docs/cli.md -v 2>&1 | \
    outmatch --contains "Version"
```

## Debugging Failures

Use verbose mode to see what went wrong:

```bash
cat << 'EOF' > /tmp/fail-test.md
` ` `bash
exit 42
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/fail-test.md
outmatch test /tmp/fail-test.md -v 2>&1 | \
    outmatch --contains "Exit code 42"
```

Stop on first failure to focus on one issue:

```bash
outmatch test docs/ --fail-fast -q 2>&1 | \
    outmatch --contains "passed"
```

## Excluded Directories

These directories are automatically skipped during discovery:

- `node_modules`
- `.git`
- `_site`
- `build`, `dist`
- `__pycache__`, `.pytest_cache`
- `.venv`, `venv`

```bash
rm -rf /tmp/excluded-test && mkdir -p /tmp/excluded-test/node_modules
echo '```bash' > /tmp/excluded-test/node_modules/bad.md
echo 'exit 1' >> /tmp/excluded-test/node_modules/bad.md
echo '```' >> /tmp/excluded-test/node_modules/bad.md
echo '```bash' > /tmp/excluded-test/good.md
echo 'echo ok' >> /tmp/excluded-test/good.md
echo '```' >> /tmp/excluded-test/good.md
outmatch test /tmp/excluded-test -q | outmatch --contains "1 passed"
```
