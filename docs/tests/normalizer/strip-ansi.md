# Strip ANSI Escape Sequences

Tests for ANSI escape sequence removal.

## Color codes are stripped

```python
from mustmatch.services.normalizer import strip_ansi

# Red text
text = "\x1b[31mhello\x1b[0m"
result = strip_ansi(text)
assert result == "hello"
```

## Multiple colors

```python
from mustmatch.services.normalizer import strip_ansi

text = "\x1b[31mred\x1b[0m and \x1b[32mgreen\x1b[0m"
result = strip_ansi(text)
assert result == "red and green"
```

## Bold and other styles

```python
from mustmatch.services.normalizer import strip_ansi

text = "\x1b[1mbold\x1b[0m \x1b[4munderline\x1b[0m"
result = strip_ansi(text)
assert result == "bold underline"
```

## Plain text unchanged

```python
from mustmatch.services.normalizer import strip_ansi

text = "hello world"
result = strip_ansi(text)
assert result == "hello world"
```

## Empty string

```python
from mustmatch.services.normalizer import strip_ansi

result = strip_ansi("")
assert result == ""
```
