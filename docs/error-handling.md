# Error Handling

Testing error cases by verifying exact error output.

## Invalid Regex Pattern

```bash
# Verify exact error message (2>&1 captures stderr)
echo "test" | mustmatch '/(?P<invalid)/' 2>&1 | \
    mustmatch "Invalid regex pattern: missing >, unterminated name at position 4"
```

## Invalid JSON in Actual

```bash
# Verify full error message
echo "{invalid json}" | mustmatch '{"a":1}' 2>&1 | \
    mustmatch "Invalid JSON in actual: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
```

## Pattern Not Matching

```bash
# Pattern doesn't match - verify error message
echo "abc" | mustmatch '/\d+/' 2>&1 | \
    mustmatch "Pattern /\d+/ did not match
Actual: 'abc'"
```

## Substring Not Found

```bash
# Substring not found - verify exact error
echo "hello" | mustmatch like "goodbye" 2>&1 | \
    mustmatch "Expected substring not found: 'goodbye'
Actual: 'hello'"
```

## JSON Mismatch Shows Diff

```bash
# JSON value mismatch shows unified diff
echo '{"count":42}' | mustmatch '{"count":99}' 2>&1 | \
    mustmatch like "--- expected"

echo '{"count":42}' | mustmatch '{"count":99}' 2>&1 | \
    mustmatch like "+++ actual"

echo '{"count":42}' | mustmatch '{"count":99}' 2>&1 | \
    mustmatch like '"count": 99'

echo '{"count":42}' | mustmatch '{"count":99}' 2>&1 | \
    mustmatch like '"count": 42'
```

## Negation Failure

```bash
# When negation fails, verify exact message
echo "error found" | mustmatch not like "error" 2>&1 | \
    mustmatch "FAIL: Expected NOT to match, but it did"
```

## Python Error Testing

These test error paths directly:

```python
from mustmatch.services.comparator import json_match, jsonl_match

# Invalid JSON in expected
result = json_match('{"a":1}', '{invalid}')
assert not result.matches
assert "Invalid JSON in expected" in result.message

# JSONL with invalid JSON
result = jsonl_match('not json\n{"id":1}', '{"id":1}')
assert not result.matches
assert "Invalid JSON on line 1" in result.message

# JSONL invalid in expected
result = jsonl_match('{"id":1}', 'not json')
assert not result.matches
assert "Invalid JSON in expected line 1" in result.message

# JSONL object not found
result = jsonl_match('{"id":1}\n{"id":2}', '{"id":3}', subset=True)
assert not result.matches
assert "Expected object not found" in result.message
```

## Bash and Python Runner Errors

```python
from mustmatch.services.runner import run_bash, run_python

# Bash timeout
result = run_bash('sleep 10', timeout=0.1)
assert result.exit_code == -1
assert result.exception is not None

# Python AssertionError
result = run_python('assert False, "test failed"')
assert result.exit_code == 1
assert "AssertionError" in result.stderr
assert "test failed" in result.stderr

# Python ValueError
result = run_python('raise ValueError("test error")')
assert result.exit_code == 1
assert "ValueError" in result.stderr
assert "test error" in result.stderr
```

## Regex Pattern Extraction

```python
from mustmatch.services.comparator import extract_regex_pattern

# Normal /pattern/
assert extract_regex_pattern('/test/') == 'test'

# With flags /pattern/i
assert extract_regex_pattern('/test/i') == 'test'

# No slashes
assert extract_regex_pattern('test') == 'test'
```
