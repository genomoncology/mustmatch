# JSON Normalization

Tests for JSON-specific normalization.

## Normalize JSON whitespace

```python
from mustmatch.services.normalizer import normalize_json_whitespace

# Pretty JSON to compact
pretty = '{\n  "a": 1,\n  "b": 2\n}'
result = normalize_json_whitespace(pretty)
assert result == '{"a":1,"b":2}'
```

## Normalize sorts keys

```python
from mustmatch.services.normalizer import normalize_json_whitespace

result = normalize_json_whitespace('{"b": 2, "a": 1}')
assert result == '{"a":1,"b":2}'
```

## Invalid JSON returns unchanged

```python
from mustmatch.services.normalizer import normalize_json_whitespace

result = normalize_json_whitespace("not json")
assert result == "not json"
```

## Normalize with all options

```python
from mustmatch.services.normalizer import normalize, NormalizeOptions

text = "  \x1b[31mHELLO\x1b[0m  \r\n"

# With all options enabled
opts = NormalizeOptions(
    strip_ansi=True,
    normalize_newlines=True,
    trim=True,
    collapse_whitespace=True,
    ignore_case=True,
)
result = normalize(text, opts)
assert result == "hello"
```

## Normalize with no options

```python
from mustmatch.services.normalizer import normalize, NormalizeOptions

text = "  hello  \n"

opts = NormalizeOptions(
    strip_ansi=False,
    normalize_newlines=False,
    trim=False,
    collapse_whitespace=False,
    ignore_case=False,
)
result = normalize(text, opts)
assert result == text
```
