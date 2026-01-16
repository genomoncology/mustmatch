# JSONL Comparison

JSONL (JSON Lines) is a format where each line is a separate JSON object. mustmatch auto-detects JSONL when the expected value contains multiple JSON objects separated by newlines.

## Basic Match

JSONL comparison checks each line matches in order:

```python
from mustmatch import compare, CompareMode

actual = '{"name": "Alice"}\n{"name": "Bob"}'
expected = '{"name": "Alice"}\n{"name": "Bob"}'

result = compare(actual, expected, mode=CompareMode.JSONL)
assert result.matches
```

## Order Matters

Unlike single JSON objects where key order doesn't matter, JSONL lines must appear in the same order:

```python
from mustmatch import compare, CompareMode

actual = '{"a": 1}\n{"b": 2}'
expected = '{"b": 2}\n{"a": 1}'  # Different order

result = compare(actual, expected, mode=CompareMode.JSONL)
assert not result.matches
```

## Subset Match

With `subset=True`, check if expected lines appear anywhere in actual (as subsets):

```python
from mustmatch import compare, CompareMode

actual = '{"name": "Alice", "role": "admin"}\n{"name": "Bob", "role": "user"}'
expected = '{"name": "Alice"}'  # Just checking for Alice

result = compare(actual, expected, mode=CompareMode.JSONL, subset=True)
assert result.matches
```

## Invalid JSON

When a line contains invalid JSON, the comparison fails with a clear message:

```python
from mustmatch import compare, CompareMode

actual = 'not valid json\n{"a": 1}'
expected = '{"a": 1}'

result = compare(actual, expected, mode=CompareMode.JSONL)
assert not result.matches
assert "Invalid JSON" in result.message
```

## Auto-Detection

JSONL is auto-detected when the expected value has multiple lines starting with `{`:

```python
from mustmatch.services.comparator import detect_mode, CompareMode

# Single JSON object
assert detect_mode('{"a": 1}') == CompareMode.JSON

# Multiple JSON objects = JSONL
assert detect_mode('{"a": 1}\n{"b": 2}') == CompareMode.JSONL
```
