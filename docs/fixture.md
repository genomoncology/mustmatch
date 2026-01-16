# Document Fixture

Python code blocks have access to an `md` object that provides the document's structure.

## Sections

This document has the following sections:

| Title | Level |
|-------|-------|
| Document Fixture | 1 |
| Sections | 2 |
| Tables | 2 |
| Accessing Tables | 2 |
| Dot Notation | 2 |

```python
# md.sections gives access to all headings
assert len(md.sections) == 5

# Access by index
first = md.sections[0]
assert first.title == "Document Fixture"
assert first.level == 1

# Access by name (normalized: lowercase, underscores)
assert md.sections.sections.title == "Sections"
assert md.sections.tables.title == "Tables"
```

## Tables

Tables are accessible via `md.tables`:

| Name | Type |
|------|------|
| Alice | admin |
| Bob | user |

```python
# md.tables gives access to all tables
assert len(md.tables) == 3  # sections table, users table, features table

# Tables are iterable
users = md.tables[1]  # second table (under "Tables" heading)
assert len(users) == 2
assert users.headers == ["Name", "Type"]
```

## Accessing Tables

Tables can be accessed by their section name:

| Feature | Enabled |
|---------|---------|
| auth | yes |
| logging | no |

```python
# Access table by section name
features = md.tables.accessing_tables
assert len(features) == 2

# Iterate over rows
for row in features:
    assert row.Feature in ("auth", "logging")
    assert row.Enabled in ("yes", "no")
```

## Dot Notation

Rows support dot notation for column access:

```python
# Get the users table
users = md.tables.tables

# Access columns with dot notation
first_user = users[0]
assert first_user.Name == "Alice"
assert first_user.Type == "admin"

# Also works with dictionary syntax
assert first_user["Name"] == "Alice"

# Get all data as plain dicts
dicts = users.as_dicts()
assert dicts == [
    {"Name": "Alice", "Type": "admin"},
    {"Name": "Bob", "Type": "user"},
]
```
