# JSON Comparison

Compare JSON semantically - field order and whitespace don't matter.
JSON is auto-detected from `{...}` or `[...]`.

## Basic Usage

```bash
# Field order doesn't matter
echo '{"name": "alice", "age": 30}' | mustmatch '{"age": 30, "name": "alice"}'

# Whitespace doesn't matter
echo '{"a":1,"b":2}' | mustmatch '{"a": 1, "b": 2}'
```

## Arrays

Array order matters:

```bash
echo '[1, 2, 3]' | mustmatch '[1, 2, 3]'
echo '[1, 2, 3]' | mustmatch '[3, 2, 1]' || test $? -eq 1
```

## Subset Matching

Use `like` to check that actual contains expected fields:

```bash
# Actual has extra fields - OK with "like"
echo '{"a":1,"b":2,"c":3}' | mustmatch like '{"a":1}'
```

## Ignoring Fields

Use `--ignore` to exclude volatile fields like timestamps:

```bash
# Ignore top-level field
echo '{"id": 1, "ts": "2024-01-01"}' | mustmatch --ignore '$.ts' '{"id": 1}'

# Multiple ignores
echo '{"id": 1, "ts": "x", "hash": "y"}' | mustmatch --ignore '$.ts' --ignore '$.hash' '{"id": 1}'
```

## Path Syntax

| Syntax | Meaning |
|--------|---------|
| `$.field` | Top-level field |
| `$.a.b` | Nested field |
| `$[*].x` | Field in ALL array elements |

## Array Wildcards

Use `[*]` to ignore a field in all array elements:

```bash
# Ignore timestamp in all records
echo '[{"id":1,"ts":"a"},{"id":2,"ts":"b"}]' | mustmatch --ignore '$[*].ts' '[{"id":1},{"id":2}]'
```
