# Writing Test Documents

mustmatch treats Markdown as executable documentation. You explain behavior in prose, define examples in tables, and run code blocks that verify those examples.

## Minimal Workflow

A common flow is:

1. Write an H1 describing the capability.
2. Add an H2 scenario with a short explanation.
3. Add a table that captures expected behavior.
4. Add a small `python each_row` or `bash` block.
5. Run `pytest docs/ -v`.

## Example Spec

````markdown
# Temperature Conversion

## Celsius To Fahrenheit

This section documents expected conversion behavior for common values.

| celsius | fahrenheit |
|---------|------------|
| 0       | 32         |
| 100     | 212        |

```python each_row
from types import SimpleNamespace
result = SimpleNamespace(
    celsius=row.celsius,
    fahrenheit=(row.celsius * 9 / 5) + 32,
)
```
````

## Running The Document

```text
pytest docs/ -v
```

If a row fails, pytest reports the row index and mismatched column so you can update either implementation or documentation.
