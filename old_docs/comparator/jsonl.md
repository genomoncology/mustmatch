# JSONL Comparison

Tests for JSON Lines comparison.

## JSONL exact match

```python
from mustmatch.services.comparator import jsonl_match

actual = '{"a": 1}\n{"b": 2}'
expected = '{"a": 1}\n{"b": 2}'

result = jsonl_match(actual, expected)
assert result.matches
```

## JSONL order matters

```python
from mustmatch.services.comparator import jsonl_match

actual = '{"a": 1}\n{"b": 2}'
expected = '{"b": 2}\n{"a": 1}'

result = jsonl_match(actual, expected)
assert not result.matches
```

## JSONL subset match

```python
from mustmatch.services.comparator import jsonl_match

actual = '{"a": 1, "extra": "data"}\n{"b": 2}'
expected = '{"a": 1}'

result = jsonl_match(actual, expected, subset=True)
assert result.matches
```

## JSONL subset not found

```python
from mustmatch.services.comparator import jsonl_match

actual = '{"x": 1}\n{"y": 2}'
expected = '{"a": 1}'

result = jsonl_match(actual, expected, subset=True)
assert not result.matches
```

## JSONL invalid JSON in actual

```python
from mustmatch.services.comparator import jsonl_match

result = jsonl_match('not json\n{"a": 1}', '{"a": 1}')
assert not result.matches
assert "Invalid JSON" in result.message
```

## JSONL invalid JSON in expected

```python
from mustmatch.services.comparator import jsonl_match

result = jsonl_match('{"a": 1}', 'not json')
assert not result.matches
assert "Invalid JSON" in result.message
```
