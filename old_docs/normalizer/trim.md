# Trim and Normalize

Tests for text normalization options.

## Trim strips whitespace

```python
from mustmatch.services.normalizer import normalize, NormalizeOptions

opts = NormalizeOptions(trim=True)
result = normalize("  hello  ", opts)
assert result == "hello"
```

## CRLF to LF

```python
from mustmatch.services.normalizer import normalize, NormalizeOptions

opts = NormalizeOptions(normalize_newlines=True, trim=False)
result = normalize("line1\r\nline2\r\n", opts)
assert result == "line1\nline2\n"
```

## Collapse whitespace

```python
from mustmatch.services.normalizer import collapse_whitespace

result = collapse_whitespace("hello    world")
assert result == "hello world"

result = collapse_whitespace("hello\t\tworld")
assert result == "hello world"
```

## Preserve newlines when collapsing

```python
from mustmatch.services.normalizer import collapse_whitespace

result = collapse_whitespace("line1   text\nline2   text")
assert result == "line1 text\nline2 text"
```

## Default options

```python
from mustmatch.services.normalizer import default_options, normalize

opts = default_options()
assert opts.strip_ansi == True
assert opts.normalize_newlines == True
assert opts.trim == True

# Apply defaults
text = "  \x1b[31mhello\x1b[0m  \r\n"
result = normalize(text, opts)
assert result == "hello"
```
