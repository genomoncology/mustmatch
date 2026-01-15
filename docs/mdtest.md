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

**Quiet** (`-q`) - Just the summary:

```bash
mustmatch test docs/cli.md --quiet
```

**Verbose** (`-v`) - Shows all tests with pass/fail:

```bash
mustmatch test docs/cli.md --verbose 2>&1 | mustmatch like "passed"
```

## Filtering Tests

Run specific tests by pattern or line number:

```bash
# Include only tests matching pattern
mustmatch test docs/matching.md --include "Exact" -q

# Run block at specific line
mustmatch test docs/cli.md --line 8 -q
```

## Block Directives

Control block execution with HTML comments before the code fence.

### Skip a Block

```bash
cat << 'EOF' > /tmp/skip-test.md
<!-- mustmatch: skip -->
```bash
exit 1
```
EOF
mustmatch test /tmp/skip-test.md -q
```

### Conditional Skip

Skip based on environment variable:

```bash
cat << 'EOF' > /tmp/skipif-test.md
<!-- mustmatch: skip-if=SKIP_ME -->
```bash
exit 1
```
EOF
SKIP_ME=1 mustmatch test /tmp/skipif-test.md -q
```

### Custom Timeout

```bash
cat << 'EOF' > /tmp/timeout-test.md
<!-- mustmatch: timeout=5 -->
```bash
sleep 0.1
```
EOF
mustmatch test /tmp/timeout-test.md -q
```

### Block Environment Variables

```bash
cat << 'EOF' > /tmp/env-test.md
<!-- mustmatch: env=TEST_VAR=hello -->
```bash
test "$TEST_VAR" = "hello"
```
EOF
mustmatch test /tmp/env-test.md -q
```

## Execution Options

| Flag | Effect |
|------|--------|
| `--fail-fast` | Stop on first failure |
| `--parallel N` | Run N files concurrently (default: 4) |
| `--timeout N` | Per-block timeout in seconds (default: 30) |
| `--shell PATH` | Shell to use (default: /bin/bash) |
| `--cwd PATH` | Working directory for all tests |
| `--env KEY=VAL` | Set environment variable (repeatable) |

## Working Directory

By default, each test runs in its markdown file's directory:

```bash
mustmatch test docs/cli.md -q
```

Override with `--cwd`:

```bash
mustmatch test docs/cli.md --cwd /tmp -q
```

## Report Files

Generate reports for CI integration:

```bash
# Create a simple test file
echo -e '```bash\necho hello\n```' > /tmp/simple.md

# JUnit XML
mustmatch test /tmp/simple.md --junit-xml /tmp/report.xml -q
cat /tmp/report.xml | mustmatch like "testsuite"

rm /tmp/simple.md /tmp/report.xml
```

## Debugging Failures

Use verbose mode to see what went wrong:

```bash
cat << 'EOF' > /tmp/fail-test.md
```bash
exit 42
```
EOF
mustmatch test /tmp/fail-test.md -v 2>&1 | mustmatch like "42"
```

## Excluded Directories

These directories are automatically skipped:

- `node_modules`
- `.git`
- `_site`
- `build`, `dist`
- `__pycache__`, `.pytest_cache`
- `.venv`, `venv`
