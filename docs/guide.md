# mustmatch Complete Guide

## Introduction

mustmatch is a CLI output assertion tool that makes your documentation executable. It solves two problems:

1. **CLI output verification**: Pipe any command to `mustmatch` to verify output
2. **Documentation testing**: Every code block in your markdown becomes a test

But more than that, mustmatch enables a new development paradigm: **Document-Driven Development (DDD)**.

### Document-Driven Development

You know Test-Driven Development (TDD):
- Write tests first
- Watch them fail
- Implement until tests pass
- Verified correctness

You've probably used Behavior-Driven Development (BDD):
- Write specifications in natural language
- Implement behavior
- Business alignment

**Document-Driven Development takes it further:**
- Write documentation with real examples
- Examples ARE tests
- Implementation must make examples work
- Ship with self-proving documentation

### When to Use mustmatch

Use mustmatch when:
- Building CLI tools
- Writing DevOps scripts
- Creating API documentation
- Building tutorials
- Verifying infrastructure state
- Any time command output matters

## Installation

```bash skip
pip install mustmatch
```

Verify installation:

```bash
mustmatch --version | mustmatch like "mustmatch"
```

## Part 1: CLI Output Assertions

### The Basic Pattern

```bash
# Command | mustmatch expected
echo "hello" | mustmatch "hello"        # Exit 0 ✓
echo "hello" | mustmatch "goodbye"      # Exit 1 ✗
```

Exit codes follow Unix conventions:
- `0` = match succeeded
- `1` = match failed
- `2` = invalid arguments

### Using in Scripts

```bash skip
#!/bin/bash

# Simple conditional
if echo "ready" | mustmatch "ready"; then
    echo "Proceeding..."
fi

# Chain with &&
deploy-service && \
    curl localhost:8080/health | mustmatch '{"status":"ok"}' && \
    echo "Deploy successful"

# Exit on failure
curl api.example.com | mustmatch like '"success"' || {
    echo "API call failed"
    exit 1
}
```

### Reading Output

By default, errors go to stderr:

```bash
# Match failure shows diff
echo "actual" | mustmatch "expected"
# Stderr: unified diff output

# Suppress errors with -q
echo "actual" | mustmatch -q "expected"
# Stderr: (nothing)

# Check exit code
echo "test" | mustmatch "test"
echo $?  # 0

echo "test" | mustmatch "other"
echo $?  # 1
```

## Part 2: Comparison Modes

mustmatch auto-detects the comparison mode from syntax.

### Exact String Match (Default)

```bash skip
# Character-for-character comparison
echo "hello world" | mustmatch "hello world"      # ✓
echo "hello world" | mustmatch "hello"            # ✗ not exact

# Case sensitive by default
echo "Hello" | mustmatch "hello"                  # ✗
echo "Hello" | mustmatch -i "hello"               # ✓ with -i flag
```

### Contains/Substring (`like`)

```bash skip
# Check if substring exists anywhere
echo "hello world" | mustmatch like "world"       # ✓
echo "hello world" | mustmatch like "goodbye"     # ✗

# Useful for partial matching
ls -la | mustmatch like "README"
date | mustmatch like "2026"
```

### Negation (`not`)

Invert any match:

```bash skip
# Assert NOT equal
echo "success" | mustmatch not "error"            # ✓

# Assert NOT contains
echo "success" | mustmatch not like "error"       # ✓
echo "error occurred" | mustmatch not like "error"  # ✗

# Combine with other modes
echo '{"status":"ok"}' | mustmatch not like '"error"'  # ✓
```

### Regular Expressions (`/pattern/`)

Wrap patterns in slashes:

```bash
# Date format
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Version numbers
echo "v1.2.3" | mustmatch '/^v\d+\.\d+\.\d+$/'

# Email addresses
echo "user@example.com" | mustmatch '/^[a-z]+@[a-z]+\.[a-z]+$/'

# Any digit
echo "123" | mustmatch '/^\d+$/'

# Flexible matching
echo "Status: OK" | mustmatch '/Status: (OK|GOOD|SUCCESS)/'
```

### JSON Comparison (Auto-detected)

JSON objects and arrays are compared semantically:

```bash skip
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'  # ✓

# Nested structures
echo '{"data":{"id":1}}' | mustmatch '{"data":{"id":1}}'  # ✓

# Arrays
echo '[1,2,3]' | mustmatch '[1,2,3]'              # ✓
echo '[1,2,3]' | mustmatch '[3,2,1]'              # ✗ order matters in arrays

# Subset matching with 'like'
echo '{"status":"ok","count":42,"timestamp":"2024-01-01"}' | \
    mustmatch like '{"status":"ok"}'              # ✓ only check status

# Nested subset
echo '{"data":{"user":{"id":1,"name":"Alice"}}}' | \
    mustmatch like '{"data":{"user":{"id":1}}}'   # ✓
```

### JSONL (JSON Lines)

Multiple JSON objects, one per line:

```bash skip
# Exact JSONL comparison
printf '{"id":1}\n{"id":2}' | mustmatch '{"id":1}\n{"id":2}'  # ✓

# Subset matching—any line can match
printf '{"id":1,"status":"ok"}\n{"id":2,"status":"ok"}' | \
    mustmatch like '{"status":"ok"}'              # ✓ both lines match

# Find specific object in stream
printf '{"id":1}\n{"id":2}\n{"id":3}' | \
    mustmatch like '{"id":2}'                     # ✓ line 2 matches
```

## Part 3: Documentation Testing

### Why Test Documentation?

Traditional documentation problems:
- Examples break, nobody notices
- Manual testing is tedious
- CI doesn't verify docs
- New developers hit broken examples

With mustmatch:
- Every example is a test
- CI fails if examples break
- Documentation is always current
- Onboarding is smooth

### The `test` Command

```bash skip
# Test a single file
mustmatch test README.md

# Test a directory (recursive)
mustmatch test docs/

# Current directory
mustmatch test .
```

### What Gets Tested

All fenced code blocks in bash or Python:

````markdown
# My Documentation

This bash block runs:

```bash
echo "hello" | mustmatch "hello"
```

This Python block runs:

```python
x = 1 + 1
assert x == 2
```

This is ignored (no language):

```
just text
```
````

### Test Output

```bash skip
mustmatch test README.md
# 2 passed

mustmatch test -v README.md
# PASS README.md:5 [bash]
# PASS README.md:9 [python]
# 2 passed

mustmatch test -q README.md
# (silent unless failures)
```

### Test Options

```bash skip
# Verbose: show each test
mustmatch test -v docs/

# Fail fast: stop on first failure
mustmatch test -x docs/

# Filter by language
mustmatch test --lang bash docs/      # Only bash blocks
mustmatch test --lang python docs/    # Only Python blocks

# Timeout (default: 30 seconds per block)
mustmatch test --timeout 60 docs/

# Memory mode (share Python state)
mustmatch test --memory tutorial.md
```

### Block Directives

Control test behavior in the code fence info string:

````markdown
Skip this block:

```bash skip
echo "not executed"
```

Custom timeout:

```bash skip timeout=60
sleep 10
echo "slow operation"
```
````

### Working Directory

Bash blocks run with `cwd` set to the markdown file's directory:

````markdown
<!-- /docs/api.md -->

```bash
# This runs in /docs/, so relative paths work
ls ../src | mustmatch like "mustmatch"
```
````

## Part 4: Document-Driven Development

### The DDD Workflow

1. **Write documentation first**

````markdown
# myproject README.md

## Installation

```bash skip
pip install myproject
```

## Usage

```bash skip
myproject --version | mustmatch like "myproject"
```
````

2. **Run tests (they fail)**

```bash skip
mustmatch test README.md
# FAIL: myproject command not found
```

3. **Implement features**

Create `myproject` CLI that outputs version.

4. **Tests pass**

```bash skip
mustmatch test README.md
# 2 passed ✓
```

5. **Refactor with confidence**

Change implementation, tests verify public interface still works.

6. **Ship**

Your documentation proves itself.

### DDD vs TDD vs BDD

**Test-Driven Development (TDD):**
```python
# test_calculator.py
def test_add():
    assert add(2, 3) == 5

# Then implement add()
```

**Behavior-Driven Development (BDD):**
```gherkin
# calculator.feature
Given a calculator
When I add 2 and 3
Then the result is 5

# Then implement steps
```

**Document-Driven Development (DDD):**
````markdown
# README.md

```bash
calculator add 2 3 | mustmatch "5"
```

# Then implement calculator
````

### Benefits of DDD

**1. Documentation Never Lies**
- Broken examples = failed CI
- No "trust me, this works"
- Always up-to-date

**2. Perfect Onboarding**
- New developers trust examples
- Copy-paste examples that work
- No surprises

**3. API-First Design**
- Docs force ergonomic thinking
- Public interface is primary concern
- Implementation details secondary

**4. Living Specifications**
- Docs are executable requirements
- Stakeholders read actual usage
- No translation between spec and code

**5. Integration Testing for Free**
- CLI integration tests = docs
- No separate test harness needed
- Tests that users actually read

### When to Use DDD

**Great for:**
- CLI tools
- APIs (with curl examples)
- DevOps scripts
- Tutorials
- Getting started guides
- Integration testing

**Not ideal for:**
- Unit testing (use pytest, unittest)
- Complex business logic (use TDD)
- UI testing (use Selenium, Playwright)
- Performance testing

**Combine with other approaches:**
- TDD for internal logic
- DDD for public interface
- BDD for business requirements

### Tradeoffs

**Pros:**
- Documentation quality improves dramatically
- Examples are always verified
- Lower maintenance (one artifact, not two)
- Better developer experience

**Cons:**
- Slower docs (examples must run)
- Can't document future features (they must work)
- Requires runnable examples (not always possible)
- Test setup can be complex

## Getting Started Tutorial

### Step 1: Simple Pipe Assertion

Create a script:

```bash skip
cat > greet.sh << 'EOF'
#!/bin/bash
echo "Hello, World!"
EOF

chmod +x greet.sh
```

Test it:

```bash
./greet.sh | mustmatch "Hello, World!"
echo "Exit code: $?"
```

### Step 2: Testing Help Text

```bash
# Test your own mustmatch help
mustmatch --help | mustmatch like "Usage:"
mustmatch --help | mustmatch like "Options:"
mustmatch --help | mustmatch not like "ERROR"
```

### Step 3: Your First Markdown Test

Create `example.md`:

````bash
cat > example.md << 'EOF'
# Example Doc

Test echo:

```bash
echo "hello" | mustmatch "hello"
```

Test ls:

```bash
ls example.md | mustmatch "example.md"
```
EOF
````

Test it:

```bash skip
mustmatch test example.md
mustmatch test -v example.md
```

### Step 4: Multi-File Test Suite

```bash skip
mkdir -p docs
cat > docs/intro.md << 'EOF'
# Introduction

```bash
echo "intro" | mustmatch "intro"
```
EOF

cat > docs/tutorial.md << 'EOF'
# Tutorial

```bash
echo "tutorial" | mustmatch "tutorial"
```
EOF

# Test all docs
mustmatch test docs/
```

### Step 5: Adding to CI

Create `.github/workflows/docs.yml`:

```yaml
name: Test Documentation
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test docs/
```

Now every PR verifies your documentation.

## Advanced Usage

### Memory Mode for Stateful Tutorials

````markdown
# Counter Tutorial

Create a counter:

```python
counter = 0
```

Increment it:

```python
counter += 1
print(f"Counter is {counter}")
```

Increment again:

```python
counter += 1
print(f"Counter is {counter}")
```
````

```bash skip
# Run with memory mode
mustmatch test --memory tutorial.md
# All blocks share 'counter' variable
```

### Combining Flags

```bash skip
# Verbose, bash only, fail fast
mustmatch test -v -x --lang bash docs/

# Quiet, custom timeout
mustmatch test -q --timeout 120 docs/

# Memory mode with verbose
mustmatch test --memory -v tutorial.md
```

### pytest Integration

```bash skip
# Install
pip install mustmatch pytest

# Run with pytest
pytest docs/
pytest docs/ -v
pytest docs/ --mustmatch-lang=bash
pytest docs/ --mustmatch-memory

# Configure in pyproject.toml
cat >> pyproject.toml << 'EOF'
[tool.pytest.ini_options]
testpaths = ["docs"]
EOF

# Now just: pytest
```

## Next Steps

- [Use Cases](use-cases/) — real-world examples
- [Reference](reference/) — technical details
- [Recipes](recipes/) — how-to guides
- [Philosophy](philosophy/) — why DDD works
