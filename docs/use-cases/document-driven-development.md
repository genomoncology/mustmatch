# Document-Driven Development (DDD)

## What is Document-Driven Development?

Document-Driven Development is a software development paradigm where:

1. **Documentation comes first** — before implementation
2. **Examples are executable** — every code example must work
3. **Docs are tests** — CI verifies documentation
4. **Tests are docs** — users read actual integration tests

It's similar to Test-Driven Development and Behavior-Driven Development, but focused on the documentation layer.

## The Evolution: TDD → BDD → DDD

### Test-Driven Development (TDD)

**Year:** ~2003 (Kent Beck)

**Philosophy:** Write tests before code

```python
# 1. Write test (fails)
def test_add():
    assert add(2, 3) == 5

# 2. Implement (passes)
def add(a, b):
    return a + b

# 3. Refactor
```

**Benefits:**
- Verified correctness
- Better design
- Regression prevention
- Refactoring confidence

**Limitations:**
- Tests aren't user-facing
- Doesn't verify documentation
- Users don't read tests

### Behavior-Driven Development (BDD)

**Year:** ~2006 (Dan North)

**Philosophy:** Write specifications in business language

```gherkin
# 1. Write specification
Feature: Calculator
  Scenario: Adding numbers
    Given a calculator
    When I add 2 and 3
    Then the result is 5

# 2. Implement step definitions
# 3. Implement feature
```

**Benefits:**
- Business alignment
- Readable by non-developers
- Behavior-focused
- Living documentation

**Limitations:**
- Separate from user docs
- Translation layer needed
- Users still don't read Gherkin

### Document-Driven Development (DDD)

**Year:** 2024+ (now)

**Philosophy:** Documentation IS the specification AND the test

````markdown
# 1. Write documentation
## Calculator Usage

```bash
calculator add 2 3 | mustmatch "5"
```

# 2. Run tests (fails)
mustmatch test README.md

# 3. Implement until docs pass
````

**Benefits:**
- Documentation verified by CI
- Examples always work
- Users read actual tests
- Perfect onboarding
- No translation layer

## The DDD Workflow

### Phase 1: Document First

Write documentation with real, working examples:

````markdown
# myapi Documentation

## Authentication

Get an API token:

```bash skip
curl -X POST https://api.example.com/auth \
  -d '{"username":"demo","password":"demo"}' | \
  mustmatch like '"token"'
```

## List Users

```bash skip
curl https://api.example.com/users \
  -H "Authorization: Bearer $TOKEN" | \
  mustmatch like '{"users":[{"id"'
```
````

### Phase 2: Run Tests (Red)

```bash skip
mustmatch test README.md
# FAIL: Connection refused (API not implemented yet)
```

### Phase 3: Implement (Green)

Build the API until examples work:

```python
# api.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/auth', methods=['POST'])
def auth():
    return jsonify({'token': 'abc123'})

@app.route('/users')
def users():
    return jsonify({'users': [{'id': 1, 'name': 'Alice'}]})
```

### Phase 4: Verify

```bash skip
# Start server
python api.py &

# Test docs
mustmatch test README.md
# 2 passed ✓

# Ship it!
```

### Phase 5: Refactor

Change implementation, docs verify public interface:

```python
# Refactor to use database
@app.route('/users')
def users():
    users = db.query(User).all()  # Implementation changed
    return jsonify({'users': [u.to_dict() for u in users]})
```

```bash skip
mustmatch test README.md
# 2 passed ✓ — public interface unchanged
```

## Comparison Table

| Aspect | TDD | BDD | DDD |
|--------|-----|-----|-----|
| **Primary Artifact** | Unit tests | Specifications | Documentation |
| **Audience** | Developers | Business + Devs | Users + Devs |
| **Language** | Code | Gherkin/Natural | Examples |
| **Verification** | Unit tests | Integration tests | Doc tests |
| **User-Facing** | No | Partially | Yes |
| **Maintenance** | Separate tests | Separate specs | Docs = tests |
| **Onboarding** | Limited | Good | Excellent |
| **API Design** | Internal focus | Behavior focus | Interface focus |

## When to Use DDD

### Excellent For

**CLI Tools:**
````markdown
```bash skip
mytool --help | mustmatch like "Usage:"
mytool process data.txt | mustmatch like "Success"
```
````

**APIs:**
````markdown
```bash skip
curl api.example.com/users | mustmatch like '{"users":[{"id"'
```
````

**DevOps Scripts:**
````markdown
```bash skip
./deploy.sh | mustmatch like "Deployment successful"
systemctl status myapp | mustmatch "active (running)"
```
````

**Tutorials:**
````markdown
```python
# Step 1: Import
from mylib import Client

# Step 2: Connect
client = Client()
assert client.status() == "connected"
```
````

### Not Ideal For

**Complex Business Logic:**
```python
# Better with TDD
def calculate_tax(income, deductions, credits):
    # Complex logic better tested with unit tests
    pass
```

**UI Testing:**
```python
# Better with Selenium/Playwright
browser.click('#submit-button')
```

**Performance Testing:**
```python
# Better with specialized tools
import timeit
```

**State Machines:**
```python
# Better with property-based testing
from hypothesis import given
```

## Combining Approaches

Use multiple paradigms together:

```
Project Structure:
├── README.md           # DDD: User-facing examples
├── docs/
│   ├── tutorial.md     # DDD: Step-by-step guide
│   └── api.md          # DDD: API examples
├── tests/
│   ├── unit/           # TDD: Internal logic
│   ├── integration/    # TDD: Component interaction
│   └── features/       # BDD: Business requirements
└── src/
    └── myproject/      # Implementation
```

**Strategy:**
- **DDD** for public interface (CLI, API, tutorials)
- **TDD** for internal logic (algorithms, utilities)
- **BDD** for business rules (workflows, processes)

## Case Study: Building a CLI Tool

### Traditional Approach

```bash
# 1. Write implementation
# src/mycli.py
def main():
    print("Hello")

# 2. Write tests (separate)
# tests/test_cli.py
def test_main():
    result = subprocess.run(['mycli'])
    assert result.stdout == "Hello"

# 3. Write docs (separate)
# README.md
# Usage:
# $ mycli
# Hello

# Problem: 3 artifacts to maintain
```

### DDD Approach

````markdown
# 1. Write docs first
# README.md

## Usage

```bash
mycli | mustmatch "Hello"
```

# 2. Run tests
mustmatch test README.md  # FAIL

# 3. Implement
# src/mycli.py
def main():
    print("Hello")

# 4. Tests pass
mustmatch test README.md  # PASS

# Solution: 1 artifact (docs), tested automatically
````

## Real-World Examples

### Example 1: CLI Tool

````markdown
# jq-like Tool

Filter JSON:

```bash skip
echo '{"name":"Alice","age":30}' | mytool '.name' | \
    mustmatch '"Alice"'
```

Array access:

```bash skip
echo '{"users":[{"id":1},{"id":2}]}' | mytool '.users[0].id' | \
    mustmatch '1'
```
````

**Workflow:**
1. Write examples
2. `mustmatch test README.md` → fails
3. Implement JSON filtering
4. Tests pass → ship

### Example 2: REST API

````markdown
# User API

Create user:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}' | \
  mustmatch like '{"id"'
```

Get user:

```bash
curl http://localhost:8080/users/1 | \
  mustmatch like '{"id":1,"name":"Alice"}'
```
````

**Workflow:**
1. Document API
2. Run tests → fails (no server)
3. Implement endpoints
4. Tests pass → API matches docs exactly

### Example 3: Infrastructure

````markdown
# Deployment Runbook

Deploy service:

```bash skip
kubectl apply -f service.yaml | \
    mustmatch like "service/myapp created"
```

Verify pods:

```bash skip
kubectl get pods | mustmatch like "myapp"
kubectl get pods | mustmatch like "Running"
```

Check health:

```bash skip
curl http://myapp/health | mustmatch '{"status":"healthy"}'
```
````

**Workflow:**
1. Document runbook
2. Test in staging → fails at step 3
3. Fix health check
4. Tests pass → production ready

## Benefits in Practice

### 1. Onboarding Velocity

**Without DDD:**
- New dev reads docs
- Tries example
- Example doesn't work
- Asks for help
- **Time wasted: hours**

**With DDD:**
- New dev reads docs
- Tries example
- Example works (CI verified it)
- Continues learning
- **Time wasted: zero**

### 2. Refactoring Confidence

**Without DDD:**
- Refactor internal code
- Manually test CLI
- Miss edge case
- User reports bug
- **User trust: broken**

**With DDD:**
- Refactor internal code
- `mustmatch test docs/` passes
- Ship with confidence
- Users never see bugs
- **User trust: maintained**

### 3. API Evolution

**Without DDD:**
- Change API response format
- Forget to update docs
- Users follow old docs
- Integration breaks
- **Support tickets: many**

**With DDD:**
- Change API response
- CI fails (docs test old format)
- Update docs to match new format
- CI passes → ship
- **Support tickets: zero**

## Tradeoffs

### Advantages

✓ Documentation always accurate
✓ Examples always work
✓ One artifact to maintain
✓ Perfect onboarding
✓ API-first thinking
✓ Integration tests for free
✓ Refactoring safety

### Disadvantages

✗ Can't document unimplemented features
✗ Examples must be runnable
✗ Test setup can be complex
✗ Slower documentation process
✗ Not suitable for all testing

### When It's Worth It

DDD has overhead but pays off when:
- Documentation is critical (open source, APIs, CLIs)
- Users frequently hit broken examples
- Onboarding is a bottleneck
- Public interface stability matters
- Integration testing is needed anyway

## Getting Started with DDD

### Week 1: Experiment

```bash skip
# Pick one doc page
# Add runnable examples
# Run: mustmatch test README.md
```

### Week 2: Expand

```bash
# Add more docs
# Set up CI
# Enforce passing tests
```

### Week 3: Adopt

```bash
# Make DDD default for new features
# Document first, implement second
# Ship when docs pass
```

### Week 4: Evangelize

```bash
# Share results with team
# Measure: broken examples = 0
# Measure: onboarding time ↓
# Measure: documentation trust ↑
```

## Conclusion

Document-Driven Development is the natural evolution of TDD and BDD for user-facing software. By making documentation executable, we ensure it never lies, onboarding is smooth, and refactoring is safe.

**The DDD Promise:**

> If your docs pass, your examples work.
> If your examples work, users succeed.
> If users succeed, your project thrives.

Start with one doc page. Make it executable. Watch the benefits compound.
