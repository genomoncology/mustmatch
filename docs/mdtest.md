# Markdown Test Runner

Test your documentation by running bash code blocks with `mustmatch test`.

## Basic Usage

```console
mustmatch test docs/              # Test all markdown in directory
mustmatch test README.md          # Test single file
mustmatch test docs/ README.md    # Test multiple paths
```

Test this documentation:

```bash
mustmatch test docs/cli.md --quiet
```

## Output Modes

**Default** - Shows pass/fail per block with summary:

```bash
mustmatch test docs/cli.md 2>&1 | mustmatch --contains "Results:"
```

**Quiet** (`-q`) - Just the summary:

```bash
mustmatch test docs/cli.md --quiet | mustmatch --regex '\d+ passed'
```

**Verbose** (`-v`) - Full output including commands:

```bash
mustmatch test docs/cli.md --verbose 2>&1 | \
    mustmatch --contains "Block (line"
```

**TAP** - Test Anything Protocol format:

```bash
mustmatch test docs/cli.md --tap | mustmatch --contains "TAP version"
```

## Report Files

Generate reports for CI integration:

```bash
# Create a simple test file for report generation
echo -e '```bash\necho hello\n```' > /tmp/simple.md

# JUnit XML (for Jenkins, GitLab CI, etc.)
mustmatch test /tmp/simple.md --junit-xml /tmp/report.xml -q
cat /tmp/report.xml | mustmatch --contains "testsuite"

# JSON report
mustmatch test /tmp/simple.md --json /tmp/report.json -q
cat /tmp/report.json | mustmatch --contains '"passed":'

rm /tmp/simple.md /tmp/report.xml /tmp/report.json
```

## Filtering Tests

Run specific tests by name pattern or line number:

```bash
# Include only tests matching pattern
mustmatch test docs/matching.md --include "Exact" -q | \
    mustmatch --contains "passed"

# Exclude tests matching pattern
mustmatch test docs/matching.md --exclude "Empty" -q | \
    mustmatch --contains "passed"

# Run block at specific line
mustmatch test docs/cli.md --line 8 -q | \
    mustmatch --contains "1 passed"
```

## Block Directives

Control block execution with HTML comments before the code fence.

### Skip a Block

```markdown
<!-- mustmatch: skip -->
` ` `bash
# This won't run
exit 1
` ` `
```

Test that skip works:

```bash
cat << 'EOF' > /tmp/skip-test.md
<!-- mustmatch: skip -->
` ` `bash
exit 1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/skip-test.md
mustmatch test /tmp/skip-test.md -q | mustmatch --contains "1 skipped"
```

### Conditional Skip

Skip based on environment variable:

```markdown
<!-- mustmatch: skip-if=CI -->
` ` `bash
# Skipped when CI=1
open https://example.com
` ` `
```

```bash
cat << 'EOF' > /tmp/skipif-test.md
<!-- mustmatch: skip-if=SKIP_ME -->
` ` `bash
exit 1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/skipif-test.md
SKIP_ME=1 mustmatch test /tmp/skipif-test.md -q | \
    mustmatch --contains "1 skipped"
```

### Custom Timeout

Override the default 30-second timeout:

```markdown
<!-- mustmatch: timeout=60 -->
` ` `bash
# Has 60 seconds to complete
long-running-command
` ` `
```

```bash
cat << 'EOF' > /tmp/timeout-test.md
<!-- mustmatch: timeout=5 -->
` ` `bash
sleep 0.1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/timeout-test.md
mustmatch test /tmp/timeout-test.md -q
```

### Block Environment Variables

Set variables for a specific block:

```markdown
<!-- mustmatch: env=DEBUG=1,VERBOSE=true -->
` ` `bash
test "$DEBUG" = "1"
` ` `
```

```bash
cat << 'EOF' > /tmp/env-test.md
<!-- mustmatch: env=TEST_VAR=hello -->
` ` `bash
test "$TEST_VAR" = "hello"
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/env-test.md
mustmatch test /tmp/env-test.md -q
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
mustmatch test docs/cli.md -q
```

Override with `--cwd`:

```bash
mustmatch test docs/cli.md --cwd /tmp -q
```

Pass environment variables with `--env`:

```bash
cat << 'EOF' > /tmp/envflag-test.md
` ` `bash
test -n "$MY_VAR"
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/envflag-test.md
mustmatch test /tmp/envflag-test.md --env MY_VAR=hello -q
```

## Test Names

Blocks get names from the nearest preceding heading or from
a comment on the first line of the block:

```markdown
## Installation

` ` `bash
# This block is named "Installation"
pip install mustmatch
` ` `

` ` `bash
# Custom Name
# This block is named "Custom Name" (first comment line)
echo hello
` ` `
```

Verify naming works:

```bash
mustmatch test docs/cli.md -v 2>&1 | \
    mustmatch --contains "Version"
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
mustmatch test /tmp/fail-test.md -v 2>&1 | \
    mustmatch --contains "Exit code 42"
```

Stop on first failure to focus on one issue:

```bash
mustmatch test docs/cli.md --fail-fast -q 2>&1 | \
    mustmatch --contains "passed"
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
mustmatch test /tmp/excluded-test -q | mustmatch --contains "1 passed"
```
