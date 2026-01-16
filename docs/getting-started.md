# Getting Started with mustmatch

A 10-minute guide to testing CLI output and documentation.

## Installation

```bash skip
pip install mustmatch
```

Verify:

```bash
mustmatch --version | mustmatch like "mustmatch"
```

## Part 1: CLI Output Assertions (5 minutes)

### Step 1: Basic Matching

Try exact string matching:

```bash skip
# Should pass (exit 0)
echo "hello" | mustmatch "hello"
echo "Exit code: $?"

# Should fail (exit 1)
echo "hello" | mustmatch "goodbye"
echo "Exit code: $?"
```

### Step 2: Substring Matching

Use `like` to check if output contains text:

```bash
# Check if README exists
ls -la | mustmatch like "README"

# Check help output
mustmatch --help | mustmatch like "Usage:"
```

### Step 3: Negation

Use `not` to assert something is absent:

```bash
# Verify no errors
echo "Operation successful" | mustmatch not like "error"
echo "Operation successful" | mustmatch not like "failed"
```

### Step 4: JSON Comparison

JSON is compared semantically:

```bash
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Subset matching
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

### Step 5: Regular Expressions

Wrap patterns in `/slashes/`:

```bash
# Date format
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Any number
echo "Count: 42" | mustmatch '/Count: \d+/'
```

### Step 6: Using in Scripts

```bash skip
#!/bin/bash
set -e  # Exit on error

# Verify service is running
echo "Running health check..."
curl -s http://localhost:8080/health | \
    mustmatch '{"status":"healthy"}' || {
    echo "Service is down!"
    exit 1
}

echo "✓ Service is healthy"
```

## Part 2: Documentation Testing (5 minutes)

### Step 1: Create Test Documentation

Create a file called `test-doc.md`:

````bash
cat > test-doc.md << 'EOF'
# Test Documentation

## Example 1: Echo

```bash
echo "hello world" | mustmatch like "world"
```

## Example 2: Date Format

```bash
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
```

## Example 3: JSON

```bash
echo '{"status":"ok"}' | mustmatch '{"status":"ok"}'
```
EOF
````

### Step 2: Run Tests

```bash skip
# Test the file
mustmatch test test-doc.md
```

You should see:
```
3 passed
```

### Step 3: Verbose Output

```bash skip
# See each test
mustmatch test -v test-doc.md
```

Output:
```
PASS test-doc.md:5 [bash]
PASS test-doc.md:11 [bash]
PASS test-doc.md:17 [bash]
3 passed
```

### Step 4: Test a Directory

Create multiple docs:

```bash skip
mkdir -p examples
cat > examples/intro.md << 'EOF'
# Introduction

```bash
echo "intro" | mustmatch "intro"
```
EOF

cat > examples/advanced.md << 'EOF'
# Advanced

```bash
echo '{"advanced":true}' | mustmatch like '{"advanced":true}'
```
EOF

# Test all markdown in directory
mustmatch test examples/
```

### Step 5: Python Blocks

````bash
cat > python-example.md << 'EOF'
# Python Example

```python
x = 1 + 1
assert x == 2
print(f"x is {x}")
```

```python
# Another block
result = "hello".upper()
assert result == "HELLO"
```
EOF

# Test Python blocks
mustmatch test python-example.md
````

### Step 6: Memory Mode

For stateful tutorials:

````bash
cat > tutorial.md << 'EOF'
# Tutorial: Counter

Create a counter:

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
EOF

# Run with memory mode (shares state)
mustmatch test --memory tutorial.md
````

## Part 3: Real-World Example

Create a complete example:

````bash
cat > myproject-readme.md << 'EOF'
# My Project

## Installation

Check Python is installed:

```bash
python3 --version | mustmatch like "Python"
```

## Basic Usage

Test help output:

```bash skip
echo "Usage: myapp [OPTIONS]" | mustmatch like "Usage:"
```

## JSON API

Test JSON response:

```bash
echo '{"status":"ok","version":"1.0"}' | \
    mustmatch like '{"status":"ok"}'
```

## Error Handling

Verify no errors appear:

```bash
echo "Operation completed successfully" | \
    mustmatch not like "error"
```
EOF

# Test it
mustmatch test myproject-readme.md
````

## Next Steps

### Add to CI/CD

Create `.github/workflows/docs.yml`:

```yaml
name: Test Documentation
on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test docs/
```

### Test Options

```bash
# Stop on first failure
mustmatch test -x docs/

# Test only bash blocks
mustmatch test --lang bash docs/

# Custom timeout (default: 30s)
mustmatch test --timeout 60 docs/

# Quiet mode (only show summary)
mustmatch test -q docs/
```

### Block Directives

````markdown
Skip a block:

```bash skip
echo "This won't run"
```

Custom timeout:

```bash skip timeout=120
sleep 10
echo "Slow operation"
```
````

### pytest Integration

```bash skip
# Install pytest
pip install pytest

# Test with pytest
pytest docs/

# With options
pytest docs/ -v
pytest docs/ --mustmatch-lang=bash
pytest docs/ --mustmatch-memory
```

## Common Patterns

### Health Checks

```bash skip
curl -s http://localhost:8080/health | \
    mustmatch '{"status":"healthy"}' || exit 1
```

### Deployment Verification

```bash skip
./deploy.sh && \
    curl http://myapp.com | mustmatch like "Welcome" && \
    echo "Deploy successful"
```

### Configuration Validation

```bash skip
cat config.json | \
    mustmatch like '{"database":{"host"' || {
    echo "Invalid config"
    exit 1
}
```

### Log Checking

```bash skip
tail -n 100 app.log | \
    mustmatch not like "ERROR" || {
    echo "Errors found in logs"
    exit 1
}
```

## Tips

### Debug Failed Tests

```bash
# Capture output to see what you got
OUTPUT=$(command)
echo "Output was: $OUTPUT"
echo "$OUTPUT" | mustmatch expected
```

### Combine Checks

```bash skip
# All checks must pass
command | {
    read DATA
    echo "$DATA" | mustmatch like "success" || exit 1
    echo "$DATA" | mustmatch not like "error" || exit 1
    echo "✓ All checks passed"
}
```

### Case Insensitive

```bash
echo "HELLO" | mustmatch -i "hello"
```

## Summary

You've learned:

✓ CLI output assertions with `mustmatch`
✓ Different comparison modes (exact, like, not, regex, JSON)
✓ Testing markdown documentation
✓ Memory mode for stateful tutorials
✓ Real-world patterns

**Key concepts:**

1. **Pipe and match**: `command | mustmatch expected`
2. **Exit codes**: 0 = success, 1 = failure
3. **Auto-detection**: JSON, regex auto-detected from syntax
4. **Test docs**: `mustmatch test docs/`
5. **Document-Driven Development**: Docs are tests, tests are docs

## Learn More

- [Complete Guide](guide.md) - Full tutorial
- [Use Cases](use-cases/) - Real-world examples
- [Reference](reference/cli-reference.md) - All options
- [Philosophy](philosophy/why-test-documentation.md) - Why test docs?

## Quick Reference

```bash skip
# CLI matching
echo "test" | mustmatch "test"                  # Exact
echo "hello world" | mustmatch like "world"     # Contains
echo "ok" | mustmatch not like "error"          # Negation
echo '{"a":1}' | mustmatch '{"a":1}'           # JSON
date +%Y-%m-%d | mustmatch '/^\d{4}/'          # Regex

# Testing docs
mustmatch test README.md                        # Single file
mustmatch test docs/                            # Directory
mustmatch test -v docs/                         # Verbose
mustmatch test -x docs/                         # Fail fast
mustmatch test --lang bash docs/                # Only bash
mustmatch test --memory tutorial.md             # Stateful

# Options
-i, --ignore-case                               # Case insensitive
-q, --quiet                                     # Suppress output
-v, --verbose                                   # Show each test
-x, --fail-fast                                 # Stop on failure
--timeout N                                     # Timeout seconds
--lang bash|python|all                          # Filter language
```

**Start with one doc page. Make it executable. Watch the benefits compound.**
