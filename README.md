# mustmatch

**Assert CLI output. Test your documentation. Keep your docs honest.**

```bash skip
# Verify command output
echo "hello" | mustmatch "hello"

# Test for substrings
ls -la | mustmatch like "README"

# Semantic JSON comparison
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'

# Regex patterns
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Assert errors DON'T appear
echo "success" | mustmatch not like "error"

# Test all code blocks in your docs (example command)
# mustmatch test docs/
```

## The Problem

Your documentation is **lying to you**.

- That `--version` flag? Changed 6 months ago, docs still show the old format.
- Those curl examples? Half of them 404 now.
- That 10-step tutorial? Breaks at step 3.
- Your DevOps runbook? Untested, unverified, ready to fail at 3am.

**Manual testing doesn't scale. Documentation rots.**

## The Solution: Document-Driven Development

mustmatch introduces a new development paradigm: **Document-Driven Development (DDD)**.

You've done Test-Driven Development (TDD). You've tried Behavior-Driven Development (BDD). Now there's a third way:

**Your documentation IS your test suite. Your tests ARE your documentation.**

```bash
# This isn't just an example—it's a test that runs in CI
mustmatch --version | mustmatch like "mustmatch"
```

If this example breaks, your CI fails. If CI passes, this example works. **Your docs can never lie.**

### DDD vs TDD vs BDD

| Approach | You Write | Benefits |
|----------|-----------|----------|
| **TDD** | Tests, then code | Verified correctness, better design |
| **BDD** | Specifications, then code | Business alignment, readable tests |
| **DDD** | Documentation with examples, then code | Always-current docs, verified public interface, perfect onboarding |

With Document-Driven Development:
1. Write documentation with real examples
2. Run `mustmatch test docs/`
3. Implement until all examples pass
4. Refactor with confidence—docs verify your public interface
5. Ship with documentation that proves itself

## Install

```bash skip
pip install mustmatch
```

## Quick Start

### 1. Pipe Command Output

```bash
# Exact match
echo "hello" | mustmatch "hello"          # Exit 0 ✓

# Contains substring
echo "hello world" | mustmatch like "world"   # Exit 0 ✓

# Negation
echo "success" | mustmatch not like "error"   # Exit 0 ✓

# Use in scripts
if echo "healthy" | mustmatch "healthy"; then
    echo "Service is up"
fi
```

### 2. Smart Comparison Modes

mustmatch auto-detects what you need:

```bash
# JSON (field order doesn't matter)
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# JSON subset
echo '{"status":"ok","data":{"count":5}}' | mustmatch like '{"status":"ok"}'

# Regex (wrap in /slashes/)
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
```

### 3. Test Your Documentation

Write docs with examples:

````markdown
# My Project

Check the version:

```bash
mustmatch --version | mustmatch like "mustmatch"
```

List files:

```bash
ls -la | mustmatch like "README"
```
````

Test them:

```bash skip
mustmatch test README.md        # Test one file
mustmatch test docs/            # Test all markdown
mustmatch test -v docs/         # Verbose output
```

Or with pytest:

```bash skip
pytest docs/
```

**Every code block becomes a test. If it's in your docs, it must work.**

## Core Use Cases

### Keep Documentation Up-to-Date

```bash skip
# Your README has this example:
echo '{"version":"2.0"}' | mustmatch like '{"version":"2.0"}'

# In CI:
mustmatch test README.md

# If the API changes to {"ver":"2.0"}, CI fails ✗
# You MUST update the docs to ship ✓
```

**Stale docs become a build failure, not a customer complaint.**

### DevOps Script Verification

```bash skip
#!/bin/bash
# deploy.sh - Self-verifying deployment script

# Verify service is running
curl -s localhost:8080/health | mustmatch '{"status":"healthy"}' || exit 1

# Verify database is accessible
psql -t -c "SELECT 1" | mustmatch "1" || exit 1

# Verify disk space
df -h / | mustmatch not like "100%" || exit 1

echo "✓ All checks passed"
```

**Your runbooks verify themselves. No more silent failures.**

### Continuous Integration

```yaml
# .github/workflows/docs.yml
name: Documentation
on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test docs/
      # Docs are now a quality gate ✓
```

**Breaking changes caught before merge. Documentation is now CI/CD.**

### Living Tutorials

````markdown
# Getting Started Tutorial

First, create a file:

```bash skip
echo "hello" > test.txt
```

Verify it exists:

```bash
ls test.txt | mustmatch "test.txt"
```

Read it back:

```bash
cat test.txt | mustmatch "hello"
```
````

```bash skip
# Run the tutorial as a test
mustmatch test tutorial.md

# Every step verified ✓
# New users can trust every example
```

## How It Works

### Exit Codes (Unix Philosophy)

```bash skip
echo "ok" | mustmatch "ok"              # Exit 0 (match)
echo "ok" | mustmatch "fail"            # Exit 1 (no match)
mustmatch "missing args"                # Exit 2 (error)

# Use in conditionals
if echo "ready" | mustmatch "ready"; then
    echo "Proceeding..."
fi

# Use with &&/||
deploy-service && \
    curl localhost:8080 | mustmatch '{"status":"ok"}' && \
    echo "Deploy successful"
```

### Auto-Detection

No need to specify modes—mustmatch figures it out:

```bash
# Detects: exact match
echo "hello" | mustmatch "hello"

# Detects: regex (from /slashes/)
echo "v1.2.3" | mustmatch '/v\d+\.\d+\.\d+/'

# Detects: JSON (from {braces})
echo '{"a":1}' | mustmatch '{"a":1}'

# Detects: JSONL (multiple JSON lines)
# printf '{"id":1}\n{"id":2}' | mustmatch like '{"id":1}'  # (see docs for JSONL)
```

### Text Normalization

mustmatch automatically cleans up output:

```bash
# ANSI color codes stripped automatically
ls --color=always | mustmatch like "README"

# Whitespace normalized (leading/trailing trimmed)
echo "  hello  " | mustmatch "hello"

# Newlines normalized (CRLF → LF)
printf "hello\r\n" | mustmatch "hello"
```

## Comparison Modes

### Exact Match

```bash
echo "hello" | mustmatch "hello"        # ✓ exact match
echo "hello" | mustmatch "HELLO"        # ✗ case matters
echo "hello" | mustmatch -i "HELLO"     # ✓ case-insensitive
```

### Contains (`like`)

```bash
echo "hello world" | mustmatch like "world"    # ✓ contains
# echo "hello world" | mustmatch like "goodbye"  # ✗ not found (would fail)
```

### Negation (`not`)

```bash
echo "success" | mustmatch not "error"         # ✓ not equal
echo "success" | mustmatch not like "error"    # ✓ doesn't contain
# echo "error occurred" | mustmatch not like "error"  # ✗ contains it (would fail)
```

### Regex (`/pattern/`)

```bash
# Dates
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Version numbers
echo "v1.2.3" | mustmatch '/^v\d+\.\d+\.\d+$/'

# UUIDs
echo "550e8400-e29b-41d4-a716-446655440000" | \
    mustmatch '/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/'
```

### JSON (semantic)

```bash
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'  # ✓ same

# Subset matching with 'like'
echo '{"status":"ok","count":42,"time":"2024-01-01"}' | \
    mustmatch like '{"status":"ok"}'  # ✓ subset

# Exact structure
# echo '{"a":1,"b":2}' | mustmatch '{"a":1}'  # ✗ missing 'b' (would fail)
```

### JSONL (JSON Lines)

```bash skip
# Multiple JSON objects, one per line
# (JSONL support - see docs/recipes/json-testing.md for examples)
printf '{"id":1,"status":"ok"}\n{"id":2,"status":"ok"}' | \
    mustmatch like '{"status":"ok"}'
```

## Documentation Testing

### Basic Testing

````markdown
# Your docs (README.md)

```bash
echo "hello" | mustmatch "hello"
```

```python
x = 1 + 1
assert x == 2
```
````

```bash skip
# Test it
mustmatch test README.md

# Output:
# PASS README.md:3 [bash]
# PASS README.md:7 [python]
# 2 passed
```

### Test Options

```bash skip
# Verbose: see each test
mustmatch test -v docs/

# Fail fast: stop on first failure
mustmatch test -x docs/

# Test specific language
mustmatch test --lang bash docs/
mustmatch test --lang python docs/

# Custom timeout (default: 30s)
mustmatch test --timeout 60 docs/

# Memory mode: share Python state between blocks
mustmatch test --memory tutorial.md
```

### Block Directives

````markdown
```bash skip
# This block is skipped (maybe requires external setup)
echo "not run"
```

```bash skip
# This slow operation gets 60 seconds (skipped in tests)
sleep 5
```
````

### Memory Mode for Tutorials

````markdown
# Tutorial: Building a Counter

First, create a counter:

```python
counter = 0
```

Increment it:

```python
counter += 1
assert counter == 1
```

Increment again:

```python
counter += 1
assert counter == 2
```
````

```bash skip
# Run with memory mode to share state between blocks
mustmatch test --memory tutorial.md
# All blocks share the same 'counter' variable ✓
```

## pytest Integration

mustmatch provides a pytest plugin that auto-discovers markdown:

```bash skip
# Install with dev dependencies
pip install mustmatch pytest

# Run tests
pytest docs/                    # Auto-discovers *.md files
pytest docs/ -v                 # Verbose
pytest docs/ --mustmatch-lang=bash      # Only bash blocks
pytest docs/ --mustmatch-memory         # Memory mode
```

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["docs"]
```

Now `pytest` automatically tests your markdown.

## Real-World Examples

### Verify Infrastructure State

```bash skip
#!/bin/bash
# health-check.sh

# Check service is running
systemctl is-active myapp | mustmatch "active" || {
    echo "Service is down!"
    exit 1
}

# Check port is open
ss -tlnp | mustmatch like ":8080" || {
    echo "Port 8080 not listening!"
    exit 1
}

# Check disk space
df -h / | mustmatch not like "100%" || {
    echo "Disk full!"
    exit 1
}

echo "✓ All health checks passed"
```

### API Testing in Documentation

````markdown
# API Documentation

## Get User

```bash skip
curl -s https://api.example.com/users/1 | \
    mustmatch like '{"id":1,"name"'
```

## Create User

```bash skip
curl -s -X POST https://api.example.com/users \
    -H "Content-Type: application/json" \
    -d '{"name":"Alice"}' | \
    mustmatch like '{"id"'
```
````

### Regression Testing

```bash skip
# When you fix a bug, add the fixed behavior to docs

# Bug: version used to output "version 1.0"
# Fixed: now outputs "v1.0"

# Add to README:
# ```bash
# mustmatch --version | mustmatch like "mustmatch"
# ```

# Now regression is impossible—CI tests the docs
```

## CLI Reference

```
Usage:
    command | mustmatch [OPTIONS] [not] [like] EXPECTED
    mustmatch test [OPTIONS] PATHS

Match stdin:
    -i, --ignore-case    Case-insensitive comparison
    -q, --quiet          Suppress output
    --version            Show version
    -h, --help           Show help

Test markdown:
    -v, --verbose        Show each test result
    -q, --quiet          Minimal output
    -x, --fail-fast      Stop on first failure
    --timeout N          Timeout per block (default: 30)
    --lang LANG          Language: bash, python, all
    --memory             Share Python state between blocks

Exit codes:
    0    Match succeeded / All tests passed
    1    Match failed / Some tests failed
    2    Invalid arguments
```

## Python API

Use mustmatch programmatically:

```python
from mustmatch import check_md_file, compare, CompareMode

# Test a markdown file
passed = check_md_file("README.md", lang="bash")

# Direct comparison
from mustmatch import compare, CompareMode

result = compare(
    actual='{"a":1,"b":2}',
    expected='{"b":2,"a":1}',
    mode=CompareMode.JSON
)

if result.matches:
    print("✓ Match")
else:
    print(f"✗ {result.message}")
```

## Document-Driven Development Workflow

1. **Write documentation first** with real, working examples
2. **Run `mustmatch test docs/`** — examples fail (red)
3. **Implement features** until examples pass (green)
4. **Refactor** with confidence—docs verify public interface
5. **Ship** with documentation that proves itself

Benefits:
- **Never stale** — docs are tested in CI
- **Always accurate** — broken examples = failed build
- **Perfect onboarding** — new devs can trust every example
- **API-first design** — docs force you to think about ergonomics
- **Living specifications** — docs are executable requirements

## Why mustmatch?

| Traditional Approach | With mustmatch |
|---------------------|----------------|
| Write docs, hope they're right | Docs are tests, must be right |
| Examples rot over time | Examples fail CI if they rot |
| Manual smoke testing | Automated doc testing |
| "Trust me, it works" | "CI passed, it works" |
| Documentation debt | Documentation asset |

## Philosophy

mustmatch follows the Unix philosophy:

- **Do one thing well**: verify output
- **Compose with pipes**: `cmd | mustmatch expected`
- **Exit codes, not exceptions**: `$?` tells you everything
- **Text streams**: works with any command
- **No magic**: reads stdin, compares, exits

## Comparison to Other Tools

**vs `grep`**: grep finds patterns, mustmatch asserts matches (and JSON, and more)

**vs `test`/`[[ ]]`**: bash test is for files/numbers, mustmatch is for command output

**vs pytest**: pytest is for unit tests, mustmatch is for integration/docs/CLI testing

**vs `expect`**: expect is for interactive programs, mustmatch is for output verification

**Use mustmatch when:**
- Testing CLI tools
- Verifying documentation
- Writing DevOps scripts
- Testing APIs (with curl)
- Creating verified tutorials

## Contributing

```bash skip
git clone https://github.com/botassembly/mustmatch
cd mustmatch
uv sync --extra dev
uv run pytest docs/
uv run ruff check src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT

## Documentation

- [Complete Guide](docs/guide.md) — comprehensive tutorial
- [Use Cases](docs/use-cases/) — real-world examples
- [Reference](docs/reference/) — technical details
- [Philosophy](docs/philosophy/) — why we built this

---

**mustmatch** — Because your documentation should never lie.
