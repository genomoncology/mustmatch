# Exact Match Comparison

Tests for the `exact()` comparison function.

## Identical strings match

```python
from mustmatch.services.comparator import exact

result = exact("hello", "hello")
assert result.matches
assert result.message == ""
```

## Different strings don't match

```python
from mustmatch.services.comparator import exact

result = exact("hello", "world")
assert not result.matches
assert "hello" in result.message or "world" in result.message
```

## Empty strings match

```python
from mustmatch.services.comparator import exact

result = exact("", "")
assert result.matches
```

## Whitespace matters

```python
from mustmatch.services.comparator import exact

result = exact("hello ", "hello")
assert not result.matches

result = exact("hello\n", "hello")
assert not result.matches
```

## Multiline strings

```python
from mustmatch.services.comparator import exact

text = """line 1
line 2
line 3"""

result = exact(text, text)
assert result.matches
```
