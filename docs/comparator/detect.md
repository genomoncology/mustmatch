# Mode Detection

Tests for auto-detecting comparison mode from syntax.

## Detect regex mode

```python
from mustmatch.services.comparator import detect_mode, CompareMode

assert detect_mode("/pattern/") == CompareMode.REGEX
assert detect_mode("/\\d+/") == CompareMode.REGEX
```

## Detect JSON object mode

```python
from mustmatch.services.comparator import detect_mode, CompareMode

assert detect_mode('{"a": 1}') == CompareMode.JSON
assert detect_mode('{ "key": "value" }') == CompareMode.JSON
```

## Detect JSON array mode

```python
from mustmatch.services.comparator import detect_mode, CompareMode

assert detect_mode('[1, 2, 3]') == CompareMode.JSON
assert detect_mode('["a", "b"]') == CompareMode.JSON
```

## Detect JSONL mode

```python
from mustmatch.services.comparator import detect_mode, CompareMode

jsonl = '{"a": 1}\n{"b": 2}'
assert detect_mode(jsonl) == CompareMode.JSONL
```

## Default to exact mode

```python
from mustmatch.services.comparator import detect_mode, CompareMode

assert detect_mode("hello") == CompareMode.EXACT
assert detect_mode("123") == CompareMode.EXACT
assert detect_mode("/not closed") == CompareMode.EXACT
```

## Extract regex pattern

```python
from mustmatch.services.comparator import extract_regex_pattern

assert extract_regex_pattern("/hello/") == "hello"
assert extract_regex_pattern("/\\d+/") == "\\d+"
assert extract_regex_pattern("/pattern/i") == "pattern"
```

## Unified compare function

```python
from mustmatch.services.comparator import compare, CompareMode

# Exact mode
result = compare("hello", "hello", mode=CompareMode.EXACT)
assert result.matches

# Contains mode
result = compare("hello world", "hello", mode=CompareMode.CONTAINS)
assert result.matches

# Regex mode
result = compare("v1.2.3", r"v\d+\.\d+\.\d+", mode=CompareMode.REGEX)
assert result.matches

# JSON mode
result = compare('{"a": 1}', '{"a": 1}', mode=CompareMode.JSON)
assert result.matches

# Case insensitive
result = compare("HELLO", "hello", ignore_case=True)
assert result.matches
```
