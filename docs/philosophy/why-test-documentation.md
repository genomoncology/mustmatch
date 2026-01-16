# Why Test Documentation?

## The Problem: Documentation Rot

Documentation decays faster than code.

### Example: A Breaking Change

**January:** Write code and docs

```python
# Code
def get_user(id):
    return {"id": id, "name": "Alice"}
```

````markdown
# Docs
```bash
curl /api/users/1
# Returns: {"id": 1, "name": "Alice"}
```
````

**March:** Refactor response format

```python
# Code (changed)
def get_user(id):
    return {
        "user": {
            "id": id,
            "name": "Alice"
        }
    }
```

````markdown
# Docs (unchanged, now wrong)
```bash
curl /api/users/1
# Returns: {"id": 1, "name": "Alice"}  # ❌ WRONG
```
````

**Result:**
- New developer follows docs
- Integration breaks
- Opens support ticket
- Trust in documentation erodes

## The Cost

### Broken Examples

**Scenario:** Tutorial with 10 steps, step 3 is broken

- Developer starts tutorial
- Gets to step 3
- Command fails
- Spends 30 minutes debugging
- Asks in Slack/Discord
- Maintainer says "Oh, that example is outdated"
- **Cost:** 30+ minutes per developer

With 100 new developers per year: **50+ hours wasted**.

### Lost Trust

Once developers hit broken examples:
- Stop trusting documentation
- Ask in chat instead
- Maintainers become human docs
- Documentation becomes decorative

**Vicious cycle:**
1. Docs are sometimes wrong
2. Developers don't trust docs
3. Developers don't use docs
4. Maintainers don't maintain docs
5. Docs become more wrong
6. Trust decreases further

### Opportunity Cost

Developer time spent on broken examples could be spent on:
- Building features
- Fixing real bugs
- Improving the product

## Traditional Solutions (Don't Work)

### Manual Testing

**Approach:** Manually test examples before releases

```bash
# release-checklist.md
- [ ] Test getting started guide
- [ ] Test API examples
- [ ] Test tutorial
- [ ] Test deployment guide
```

**Problems:**
- Tedious (nobody does it)
- Error-prone (miss examples)
- Doesn't scale (more docs = more work)
- Only happens at release (problems found late)

### Separate Integration Tests

**Approach:** Write tests that cover the same ground as docs

```python
# test_api.py
def test_get_user():
    response = client.get('/api/users/1')
    assert response.json()['id'] == 1

# README.md (separate, can still be wrong)
curl /api/users/1
# Returns: {"id": 1}
```

**Problems:**
- Two artifacts to maintain (test and doc)
- Tests can pass while docs are wrong
- Duplication of effort
- Tests aren't user-facing

### Code Comments

**Approach:** Put examples in docstrings

```python
def get_user(id):
    """Get user by ID.

    Example:
        >>> get_user(1)
        {'id': 1, 'name': 'Alice'}
    """
    return db.query(User, id)
```

**Problems:**
- Not discoverable (hidden in code)
- Only covers Python (not CLI, not APIs)
- Doctests are limited
- Users don't read docstrings

## The mustmatch Solution

### Documentation IS Tests

````markdown
# README.md

Get a user:

```bash
curl http://localhost:8080/api/users/1 | \
    mustmatch like '{"id":1,"name":"Alice"}'
```
````

```bash skip
# In CI:
mustmatch test README.md
```

**Benefits:**
- One artifact (docs)
- Always verified
- Users read actual tests
- Breaking changes caught immediately

### The Feedback Loop

**Without mustmatch:**
```
Code change → (time passes) → User hits broken example → Report issue
```
Time to discovery: **days to months**

**With mustmatch:**
```
Code change → CI fails → Fix docs or code → Merge
```
Time to discovery: **seconds**

### Force Function

When docs are tested:
- **Can't** ship broken examples (CI blocks it)
- **Must** update docs when API changes
- **Always** have working onboarding

Documentation becomes a quality gate, not an afterthought.

## Real-World Impact

### Case Study: CLI Tool

**Before mustmatch:**
- 50-page documentation site
- 5-10 support requests per week about broken examples
- 2 hours/week maintainer time on "doc is wrong" issues
- Developers avoid trying the tool (docs unreliable)

**After mustmatch:**
- Same 50 pages, now tested
- Support requests drop to ~1/week (real bugs)
- 0 hours/week on doc issues
- Developer adoption increases (docs reliable)

**ROI:**
- 100+ hours/year saved (maintainer time)
- 200+ hours/year saved (developer time)
- Better reputation (reliable docs)
- Lower support burden

### Case Study: API Documentation

**Before mustmatch:**
- API docs with curl examples
- Examples break when endpoints change
- Customers integrate against wrong examples
- Support escalations
- Emergency patches

**After mustmatch:**
- All curl examples tested in CI
- Breaking API changes caught before release
- Customers trust examples
- Fewer integration issues
- Smooth releases

## Psychological Benefits

### For Maintainers

**Confidence:**
- Know examples work
- Refactor without fear
- Ship faster

**Less Stress:**
- No "did I break the docs?" worry
- No emergency doc fixes
- Fewer support tickets

### For Users

**Trust:**
- Examples guaranteed to work
- Copy-paste with confidence
- Faster onboarding

**Better Experience:**
- No time wasted debugging docs
- Smooth learning curve
- Positive first impression

## Philosophy: Documentation as Code

### Code is Tested

```python
def add(a, b):
    return a + b

# Test
assert add(2, 3) == 5
```

Nobody ships code without tests. Why ship docs without tests?

### Documentation Should Be Too

````markdown
# Documentation

```bash
add 2 3 | mustmatch "5"
```
````

If code must prove correctness, so must documentation.

## The Documentation Spectrum

### Level 0: No Docs
- Users figure it out
- High support burden
- Slow adoption

### Level 1: Written Docs
- Better than nothing
- Rot over time
- Trust issues

### Level 2: Manual Testing
- Some verification
- Doesn't scale
- Inconsistent

### Level 3: Tested Docs (mustmatch)
- Always accurate
- Scales automatically
- High trust

### Level 4: Living Docs
- Tested docs
- Auto-generated from code
- Examples from real usage
- (Future state)

## Comparing Approaches

| Approach | Accuracy | Maintenance | Trust | Effort |
|----------|----------|-------------|-------|--------|
| No docs | N/A | Zero | Zero | Zero |
| Manual docs | Low | High | Low | Medium |
| Manual testing | Medium | Very High | Medium | High |
| Separate tests | High (tests) | High | Low (docs) | High |
| **Tested docs** | **High** | **Medium** | **High** | **Medium** |

## Common Objections

### "Our docs are too complex to test"

Start small:
- Test README first
- Test one tutorial
- Add more over time

Complex docs often NEED testing most.

### "Tests will slow down our docs"

Yes, but:
- Fast tests (seconds)
- Catch bugs early (saves time)
- Less support burden (saves more time)
- Net positive

### "We can't test external dependencies"

Use mocks:

```bash skip
# Mock external API
cat > test-api.sh << 'EOF'
#!/bin/bash
echo '{"status":"ok"}'
EOF
```

````markdown
```bash
./test-api.sh | mustmatch '{"status":"ok"}'
```
````

Or test against staging/sandbox.

### "Examples are just for illustration"

If examples are illustrative, why can't they also work?

Users will try them. Broken examples = bad experience.

## When NOT to Test Docs

### Conceptual Explanations

```markdown
# How it works

The system uses a queue to process jobs asynchronously.
```

No code to test—that's fine.

### Pseudo-code

```markdown
# Algorithm

```
for each item:
    if condition:
        process(item)
```
```

Not meant to run—skip testing.

### Future Features

```markdown
# Coming Soon

```bash skip
# Feature not implemented yet
mytool --new-feature
```
```

Can't test unimplemented features. Use `skip` directive:

````markdown
```bash skip
mytool --new-feature
```
````

## Best Practices

### 1. Start Simple

Test basic examples first:

```bash
# Start here
echo "hello" | mustmatch "hello"

# Not here
# Complex 50-line deployment script
```

### 2. Test What Users See

Focus on user-facing docs:
- README
- Getting started
- Tutorials
- API examples

Internal docs less critical.

### 3. Make Tests Fast

Slow tests = don't run tests

```bash skip
# Fast (< 1s per test)
echo "test" | mustmatch "test"

# Slow (> 10s per test)
docker-compose up && sleep 30 && curl ...
```

Use mocks for speed.

### 4. Use CI

```yaml
# .github/workflows/docs.yml
- run: mustmatch test docs/
```

Automate verification.

### 5. Fail Fast

```bash
mustmatch test -x docs/
```

Stop on first failure for rapid iteration.

## Conclusion

Documentation rot is a universal problem with a measurable cost:
- Wasted developer time
- Lost trust
- Higher support burden
- Slower onboarding

Testing documentation fixes this:
- Examples always work
- Trust is high
- Support is low
- Onboarding is smooth

The question isn't "Why test documentation?"

The question is "Why are you shipping untested documentation?"

**Your code has tests. Your docs should too.**
