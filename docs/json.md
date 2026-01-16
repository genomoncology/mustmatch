# JSON Comparison

Compare JSON semantically with `--json`. Field order, whitespace,
and formatting don't matter.

## Basic Usage

```bash
# Field order independence
echo '{"name": "alice", "age": 30}' | \
    mustmatch --json '{"age": 30, "name": "alice"}'

# Nested structures
echo '{"user": {"name": "alice", "age": 30}}' | \
    mustmatch --json '{"user": {"age": 30, "name": "alice"}}'

# All JSON types
echo '{"active": true, "data": null}' | \
    mustmatch --json '{"data": null, "active": true}'
echo '{"int": 42, "float": 3.14}' | \
    mustmatch --json '{"float": 3.14, "int": 42}'
```

## Arrays

Array order matters (unlike objects):

```bash
echo '[1, 2, 3]' | mustmatch --json '[1, 2, 3]'
echo '[1, 2, 3]' | mustmatch --json '[3, 2, 1]' || test $? -eq 1
```

## Wildcard Matching

Use `"*"` as a value to match any value (including objects and arrays):

```bash
# Match any id value
echo '{"id": "abc123", "status": "ok"}' | \
    mustmatch --json '{"id": "*", "status": "ok"}'

# Nested wildcards
echo '{"user": {"id": 42, "name": "alice"}}' | \
    mustmatch --json '{"user": {"id": "*", "name": "alice"}}'

# Array element wildcards
echo '{"items": [1, 2, 3]}' | \
    mustmatch --json '{"items": ["*", "*", "*"]}'

# Wildcard matches any type
echo '{"data": {"nested": "complex"}}' | \
    mustmatch --json '{"data": "*"}'
```

This is useful for:
- Matching responses with dynamic IDs or timestamps
- Validating structure without caring about specific values
- Testing with `mustmatch exec --output-json`

## Ignoring Fields

Use `--json-ignore` to exclude volatile fields like timestamps:

```bash
# Ignore top-level field
echo '{"id": 1, "ts": "2024-01-01"}' | \
    mustmatch --json --json-ignore '$.ts' '{"id": 1}'

# Multiple ignores
echo '{"id": 1, "ts": "x", "hash": "y"}' | \
    mustmatch --json \
    --json-ignore '$.ts' \
    --json-ignore '$.hash' \
    '{"id": 1}'

# Nested paths
echo '{"user": {"name": "alice", "ts": "x"}}' | \
    mustmatch --json --json-ignore '$.user.ts' \
    '{"user": {"name": "alice"}}'

# Non-existent paths silently succeed
echo '{"id": 1}' | \
    mustmatch --json --json-ignore '$.nonexistent' '{"id": 1}'
echo '{"id": 1}' | \
    mustmatch --json --json-ignore '$.a.b.c' '{"id": 1}'
```

## Path Syntax

Paths use a simplified JSONPath syntax:

| Syntax           | Meaning                              |
|------------------|--------------------------------------|
| `$.field`        | Top-level field                      |
| `$.a.b`          | Nested field                         |
| `$.arr[0].x`     | Field in array element               |
| `$.arr[*].x`     | Field in ALL array elements          |

### Array Wildcards

Use `[*]` to ignore a field across all array elements:

```bash
# Ignore timestamp in all records
echo '[{"id":1,"ts":"a"},{"id":2,"ts":"b"}]' | \
    mustmatch --json --json-ignore '$[*].ts' '[{"id":1},{"id":2}]'

# Nested array wildcards
echo '{"items":[{"id":1,"created":"x"},{"id":2,"created":"y"}]}' | \
    mustmatch --json --json-ignore '$.items[*].created' \
    '{"items":[{"id":1},{"id":2}]}'
```

## Errors

```bash
# Invalid JSON in actual
echo "not json" | mustmatch --json '{"id": 1}' 2>&1 | \
    mustmatch --contains "not valid JSON"

# Invalid JSON in expected
echo '{"id": 1}' | mustmatch --json "not json" 2>&1 | \
    mustmatch --contains "not valid JSON"

# Value mismatch
echo '{"name": "alice"}' | \
    mustmatch --json '{"name": "bob"}' 2>&1 | \
    mustmatch --contains "mismatch"
```
