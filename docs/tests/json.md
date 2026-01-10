# JSON Comparison

Compare JSON semantically with `--json`.

Use JSON mode when you're comparing structured data. Field order, whitespace, and formatting don't matter - only the actual values.

## Why use JSON mode instead of exact matching?

Because JSON serialization varies. The same data can look different:

```bash
echo '{"name": "alice", "age": 30}' | outmatch --json '{"age": 30, "name": "alice"}'
```

Field order differs, but the data is identical. JSON mode understands this.

## Does it work with nested structures?

Yes. Deep comparison at all levels:

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    outmatch --json '{"user": {"age": 30, "name": "alice"}}'
```

## What about arrays?

Arrays compare element-by-element. Order matters for arrays (unlike object keys):

```bash
echo '[1, 2, 3]' | outmatch --json '[1, 2, 3]'
```

Different order fails:

```bash
echo '[1, 2, 3]' | outmatch --json '[3, 2, 1]' || test $? -eq 1
```

## How do I handle all JSON types?

Booleans, nulls, numbers - all work as expected:

```bash
echo '{"active": true, "data": null}' | outmatch --json '{"data": null, "active": true}'
```

```bash
echo '{"int": 42, "float": 3.14}' | outmatch --json '{"float": 3.14, "int": 42}'
```

## How do I ignore volatile fields?

Use `--json-ignore` with a JSONPath expression to exclude fields that change between runs:

```bash
echo '{"id": 1, "ts": "2024-01-01"}' | outmatch --json --json-ignore '$.ts' '{"id": 1}'
```

Chain multiple ignores for several fields:

```bash
echo '{"id": 1, "ts": "x", "hash": "y"}' | \
    outmatch --json --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'
```

Works with nested paths too:

```bash
echo '{"user": {"name": "alice", "created": "2024-01-01"}}' | \
    outmatch --json --json-ignore '$.user.created' '{"user": {"name": "alice"}}'
```

## What JSONPath syntax is supported?

Basic dot notation and array indexing:

```bash
echo '{"name": "alice", "id": 1}' | outmatch --json --json-ignore '$name' '{"id": 1}'
```

```bash
echo '{"items": [1, 2, 3]}' | outmatch --json --json-ignore '$.items[0]' '{"items": [1, 2, 3]}'
```

```bash
echo '{"data": {"items": ["a", "b", "c"]}}' | \
    outmatch --json --json-ignore '$.data.items[1]' '{"data": {"items": ["a", "b", "c"]}}'
```

Ignoring non-existent paths silently succeeds (no error):

```bash
echo '{"id": 1}' | outmatch --json --json-ignore '$.nonexistent' '{"id": 1}'
```

```bash
echo '{"id": 1}' | outmatch --json --json-ignore '$.a.b.c' '{"id": 1}'
```

```bash
echo '{"items": [1]}' | outmatch --json --json-ignore '$.items[99]' '{"items": [1]}'
```

## What happens with invalid JSON?

Exit code 1 with a clear error message:

```bash
echo "not json" | outmatch --json '{"id": 1}' 2>&1 | outmatch --contains "not valid JSON"
```

```bash
echo '{"id": 1}' | outmatch --json "not json" 2>&1 | outmatch --contains "not valid JSON"
```

## What does mismatch output look like?

A helpful message indicating the difference:

```bash
echo '{"name": "alice"}' | outmatch --json '{"name": "bob"}' 2>&1 | outmatch --contains "mismatch"
```
