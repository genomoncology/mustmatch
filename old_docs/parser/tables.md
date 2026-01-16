# Table Extraction

Tests for extracting tables from markdown.

## Simple table

```python
from mustmatch.services.parser import parse_markdown

md = """
# Test

| name  | age |
|-------|-----|
| Alice | 30  |
| Bob   | 25  |
"""

result = parse_markdown(md)
assert len(result.tables) == 1
assert result.tables[0].headers == ["name", "age"]
assert len(result.tables[0].rows) == 2
assert result.tables[0].rows[0] == ["Alice", "30"]
assert result.tables[0].rows[1] == ["Bob", "25"]
```

## Table context from headings

```python
from mustmatch.services.parser import parse_markdown

md = """
# Users

## Active Users

| name  |
|-------|
| Alice |

## Inactive Users

| name |
|------|
| Bob  |
"""

result = parse_markdown(md)
assert len(result.tables) == 2
assert result.tables[0].context == ["Users", "Active Users"]
assert result.tables[1].context == ["Users", "Inactive Users"]
```

## Get table for block

````python
from mustmatch.services.parser import parse_markdown, get_table_for_block

md = """
# Test Cases

| input | expected |
|-------|----------|
| 1     | 2        |
| 2     | 4        |

```python
# This block should have access to the table above
for row in table:
    assert int(row["expected"]) == int(row["input"]) * 2
```
"""

result = parse_markdown(md)
assert len(result.blocks) == 1
assert len(result.tables) == 1

table = get_table_for_block(result, result.blocks[0])
assert table is not None
assert table.headers == ["input", "expected"]
````

## Table with empty cells

```python
from mustmatch.services.parser import parse_markdown

md = """
| a | b | c |
|---|---|---|
| 1 |   | 3 |
|   | 2 |   |
"""

result = parse_markdown(md)
assert len(result.tables) == 1
assert result.tables[0].rows[0] == ["1", "", "3"]
assert result.tables[0].rows[1] == ["", "2", ""]
```
