# Block Extraction

Tests for extracting code blocks from markdown.

## Extract bash blocks

````python
from mustmatch.services.parser import parse_markdown

md = """
# Test

```bash
echo "hello"
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 1
assert result.blocks[0].language == "bash"
assert 'echo "hello"' in result.blocks[0].content
````

## Extract python blocks

````python
from mustmatch.services.parser import parse_markdown

md = """
# Test

```python
print("hello")
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 1
assert result.blocks[0].language == "python"
assert 'print("hello")' in result.blocks[0].content
````

## Multiple blocks

````python
from mustmatch.services.parser import parse_markdown

md = """
# Test

```bash
echo "one"
```

```python
print("two")
```

```bash
echo "three"
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 3
assert result.blocks[0].language == "bash"
assert result.blocks[1].language == "python"
assert result.blocks[2].language == "bash"
````

## Heading context

````python
from mustmatch.services.parser import parse_markdown

md = """
# Section One

## Subsection A

```bash
echo "a"
```

## Subsection B

```bash
echo "b"
```

# Section Two

```bash
echo "c"
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 3

# First block under "Section One > Subsection A"
assert result.blocks[0].name == "Subsection A"
assert result.blocks[0].context == ["Section One", "Subsection A"]

# Second block under "Section One > Subsection B"
assert result.blocks[1].name == "Subsection B"
assert result.blocks[1].context == ["Section One", "Subsection B"]

# Third block under "Section Two"
assert result.blocks[2].name == "Section Two"
assert result.blocks[2].context == ["Section Two"]
````

## Parse directives

````python
from mustmatch.services.parser import parse_markdown

md = """
```bash skip
echo "skipped"
```

```bash timeout=5
echo "with timeout"
```

```python skip=ci
print("skip on CI")
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 3

assert "skip" in result.blocks[0].directives
assert result.blocks[0].directives["skip"] == ""

assert "timeout" in result.blocks[1].directives
assert result.blocks[1].directives["timeout"] == "5"

assert "skip" in result.blocks[2].directives
assert result.blocks[2].directives["skip"] == "ci"
````

## Ignore non-code blocks

````python
from mustmatch.services.parser import parse_markdown

md = """
# Test

```json
{"not": "executable"}
```

```yaml
key: value
```

```bash
echo "this is executable"
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 1
assert result.blocks[0].language == "bash"
````
