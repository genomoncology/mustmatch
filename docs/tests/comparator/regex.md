# Regex Comparison

Tests for the `regex()` comparison function.

## Simple pattern matches

```python
from mustmatch.services.comparator import regex

result = regex("hello123", r"\d+")
assert result.matches
```

## Pattern not found

```python
from mustmatch.services.comparator import regex

result = regex("hello", r"\d+")
assert not result.matches
```

## Complex pattern

```python
from mustmatch.services.comparator import regex

result = regex("v1.2.3", r"v\d+\.\d+\.\d+")
assert result.matches
```

## Invalid regex pattern

```python
from mustmatch.services.comparator import regex

result = regex("test", r"[invalid")
assert not result.matches
assert "Invalid regex" in result.message
```

## Anchored pattern

```python
from mustmatch.services.comparator import regex

# Without anchors, matches anywhere
result = regex("prefix-123-suffix", r"\d+")
assert result.matches

# With anchors
result = regex("123", r"^\d+$")
assert result.matches

result = regex("prefix-123", r"^\d+$")
assert not result.matches
```
