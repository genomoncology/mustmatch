# Fixtures And Tables

Markdown tables are first-class fixture data for Python blocks. Rows can be coerced into typed values, and `each_row` executes one test per row. The `md` fixture also exposes document structure for context-aware assertions.

## Using Each Row

This table drives an `each_row` block. Numeric columns are auto-coerced while `str:` headers stay as raw strings.

| input | output | str:label |
|-------|--------|-----------|
| 2     | 4      | row-a     |
| 3     | 6      | row-b     |

```python each_row
doubled = row.input * 2
result = {"input": row.input, "output": doubled, "label": row.label}
label_copy = row.label
```

## Scenarios Fixture

When a Python block follows a table, that table is available as `scenarios`.
This gives concise access to typed `TableRow` values without hard-coding a table slug.

| sample | expected_hits |
|--------|---------------|
| BRAF   | 1             |
| EGFR   | 2             |

```python
assert len(scenarios) == 2
assert scenarios[0].sample == "BRAF"
assert scenarios[1].expected_hits == 2

counts = {row.sample: row.expected_hits for row in scenarios}
assert counts["BRAF"] == 1
assert counts["EGFR"] == 2
```

## Document Fixture

`md` exposes collected sections and tables. This lets blocks validate document wiring as part of executable docs.

```python
first_table = md.tables[0]
assert first_table.name == "Using Each Row"
assert md.current_section.title == "Document Fixture"
```
