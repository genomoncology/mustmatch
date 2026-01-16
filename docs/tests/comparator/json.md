# JSON Comparison

Tests for the `json_match()` comparison function.

## Identical JSON objects match

```python
from mustmatch.services.comparator import json_match

result = json_match('{"a": 1, "b": 2}', '{"a": 1, "b": 2}')
assert result.matches
```

## Key order doesn't matter

```python
from mustmatch.services.comparator import json_match

result = json_match('{"b": 2, "a": 1}', '{"a": 1, "b": 2}')
assert result.matches
```

## Different values don't match

```python
from mustmatch.services.comparator import json_match

result = json_match('{"a": 1}', '{"a": 2}')
assert not result.matches
```

## Subset matching

```python
from mustmatch.services.comparator import json_match

# With subset=True, actual only needs to contain expected fields
result = json_match('{"a": 1, "b": 2, "c": 3}', '{"a": 1}', subset=True)
assert result.matches

# Without subset, must be exact
result = json_match('{"a": 1, "b": 2}', '{"a": 1}', subset=False)
assert not result.matches
```

## JSON arrays

```python
from mustmatch.services.comparator import json_match

result = json_match('[1, 2, 3]', '[1, 2, 3]')
assert result.matches

result = json_match('[1, 2, 3]', '[3, 2, 1]')
assert not result.matches  # Order matters for arrays
```

## Nested objects

```python
from mustmatch.services.comparator import json_match

actual = '{"user": {"name": "Alice", "age": 30}}'
expected = '{"user": {"name": "Alice", "age": 30}}'
result = json_match(actual, expected)
assert result.matches
```

## Invalid JSON

```python
from mustmatch.services.comparator import json_match

result = json_match('not json', '{"a": 1}')
assert not result.matches
assert "Invalid JSON" in result.message
```

## Ignore paths

```python
from mustmatch.services.comparator import json_match

actual = '{"id": 123, "name": "test", "timestamp": "2024-01-01"}'
expected = '{"id": 456, "name": "test", "timestamp": "2024-12-31"}'

# Without ignoring, they don't match
result = json_match(actual, expected)
assert not result.matches

# Ignoring id and timestamp, they match
result = json_match(actual, expected, ignore_paths=["$.id", "$.timestamp"])
assert result.matches
```
