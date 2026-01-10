# JSON Comparison

Compare JSON semantically with `--json`. Field order, whitespace, and formatting don't matter.

## Basic Usage

```bash
# Field order independence
echo '{"name": "alice", "age": 30}' | outmatch --json '{"age": 30, "name": "alice"}'

# Nested structures
echo '{"user": {"name": "alice", "age": 30}}' | outmatch --json '{"user": {"age": 30, "name": "alice"}}'

# All JSON types
echo '{"active": true, "data": null}' | outmatch --json '{"data": null, "active": true}'
echo '{"int": 42, "float": 3.14}' | outmatch --json '{"float": 3.14, "int": 42}'
```

## Arrays

Array order matters (unlike objects):

```bash
echo '[1, 2, 3]' | outmatch --json '[1, 2, 3]'
echo '[1, 2, 3]' | outmatch --json '[3, 2, 1]' || test $? -eq 1
```

## Ignoring Fields

Use `--json-ignore` with JSONPath to exclude volatile fields:

```bash
# Ignore top-level field
echo '{"id": 1, "ts": "2024-01-01"}' | outmatch --json --json-ignore '$.ts' '{"id": 1}'

# Multiple ignores
echo '{"id": 1, "ts": "x", "hash": "y"}' | outmatch --json --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'

# Nested paths
echo '{"user": {"name": "alice", "created": "2024-01-01"}}' | outmatch --json --json-ignore '$.user.created' '{"user": {"name": "alice"}}'

# Array indexing
echo '{"items": [1, 2, 3]}' | outmatch --json --json-ignore '$.items[0]' '{"items": [1, 2, 3]}'

# Non-existent paths silently succeed
echo '{"id": 1}' | outmatch --json --json-ignore '$.nonexistent' '{"id": 1}'
echo '{"id": 1}' | outmatch --json --json-ignore '$.a.b.c' '{"id": 1}'
echo '{"items": [1]}' | outmatch --json --json-ignore '$.items[99]' '{"items": [1]}'
```

Alternate path syntax:

```bash
echo '{"name": "alice", "id": 1}' | outmatch --json --json-ignore '$name' '{"id": 1}'
echo '{"data": {"items": ["a", "b", "c"]}}' | outmatch --json --json-ignore '$.data.items[1]' '{"data": {"items": ["a", "b", "c"]}}'
```

## Errors

```bash
echo "not json" | outmatch --json '{"id": 1}' 2>&1 | outmatch --contains "not valid JSON"
echo '{"id": 1}' | outmatch --json "not json" 2>&1 | outmatch --contains "not valid JSON"
echo '{"name": "alice"}' | outmatch --json '{"name": "bob"}' 2>&1 | outmatch --contains "mismatch"
```
