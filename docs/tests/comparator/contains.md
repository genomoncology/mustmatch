# Contains Comparison

Tests for the `contains()` comparison function.

## Substring found

```python
from mustmatch.services.comparator import contains

result = contains("hello world", "world")
assert result.matches
```

## Substring at start

```python
from mustmatch.services.comparator import contains

result = contains("hello world", "hello")
assert result.matches
```

## Substring not found

```python
from mustmatch.services.comparator import contains

result = contains("hello world", "foo")
assert not result.matches
assert "foo" in result.message
```

## Empty substring always matches

```python
from mustmatch.services.comparator import contains

result = contains("hello", "")
assert result.matches
```

## Case sensitive by default

```python
from mustmatch.services.comparator import contains

result = contains("Hello World", "hello")
assert not result.matches
```
