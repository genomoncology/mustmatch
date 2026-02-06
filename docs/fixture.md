# Document Fixture

The `md` fixture lets Python code blocks read the same Markdown structure that humans read: sections, tables, and row data. This keeps specs readable while still being executable.

You can use `md.sections` to inspect heading hierarchy and `md.tables` to consume table-driven examples.

## Sections

This section verifies that heading metadata is available from Python.

| Expected Section |
|------------------|
| Sections |
| Table Access |

```python
titles = [section.title for section in md.sections]
for row in md.tables.sections:
    assert row.expected_section in titles

assert md.current_section is not None
assert md.current_section.title == "Sections"
```

## Table Access

Tables are exposed by heading name and support iteration.

| Name  | Role  |
|-------|-------|
| Alice | admin |
| Bob   | user  |

```python
users = md.tables.table_access
assert len(users) == 2
assert users[0].name == "Alice"
assert users[0]["Role"] == "admin"
assert users.as_dicts()[1]["Name"] == "Bob"
```

## Type Coercion

Cells are auto-coerced for common scalar types. Use `str:` in headers to opt out when a value should stay a string.

| count | ratio | enabled | optional | str:zip_code |
|-------|-------|---------|----------|--------------|
| 1     | 1.5   | true    | None     | 00123        |
| 2     | 2.0   | false   |          | 02108        |

```python
rows = md.tables.type_coercion
assert rows[0].count == 1 and isinstance(rows[0].count, int)
assert rows[0].ratio == 1.5 and isinstance(rows[0].ratio, float)
assert rows[0].enabled is True
assert rows[0].optional is None
assert rows[0].zip_code == "00123" and isinstance(rows[0].zip_code, str)
assert rows[1].optional is None
```

## Row Helpers

`TableRow` also provides helper methods when you need generic iteration or dynamic assertions.

| key_name | value_name |
|----------|------------|
| alpha    | one        |

```python
row = md.tables.row_helpers[0]
assert row.keys() == ["key_name", "value_name"]
assert row.values() == ["alpha", "one"]
assert row.items() == [("key_name", "alpha"), ("value_name", "one")]
```

## Namespace Hook

Projects can inject domain-specific objects into each Python block with `pytest_mustmatch_namespace`. This example is shown as documentation only:

```python skip
# conftest.py

def pytest_mustmatch_namespace():
    return {
        "db": db_client,
        "http": http_client,
    }
```
