# JSON Mode Tests

Tests for JSON semantic comparison with `--json`.

## Basic JSON match

```bash
echo '{"name": "alice", "age": 30}' | outmatch --json '{"name": "alice", "age": 30}'
```

## Field order independence

```bash
echo '{"name": "alice", "age": 30}' | outmatch --json '{"age": 30, "name": "alice"}'
```

## Nested objects

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    outmatch --json '{"user": {"age": 30, "name": "alice"}}'
```

## Arrays

```bash
echo '[1, 2, 3]' | outmatch --json '[1, 2, 3]'
```

## Array order matters

Arrays preserve order (this should fail):

```bash
echo '[1, 2, 3]' | outmatch --json '[3, 2, 1]' || test $? -eq 1
```

## Boolean and null values

```bash
echo '{"active": true, "data": null}' | outmatch --json '{"data": null, "active": true}'
```

## Numbers

```bash
echo '{"int": 42, "float": 3.14}' | outmatch --json '{"float": 3.14, "int": 42}'
```

## Invalid actual JSON fails

```bash
echo "not json" | outmatch --json '{"id": 1}' 2>&1 | outmatch --contains "not valid JSON"
```

## Invalid expected JSON fails

```bash
echo '{"id": 1}' | outmatch --json "not json" 2>&1 | outmatch --contains "not valid JSON"
```

## JSON mismatch shows diff

```bash
echo '{"name": "alice"}' | outmatch --json '{"name": "bob"}' 2>&1 | outmatch --contains "mismatch"
```

## JSON with ignore path

Ignore a timestamp field:

```bash
echo '{"id": 1, "ts": "2024-01-01"}' | outmatch --json --json-ignore '$.ts' '{"id": 1}'
```

## Multiple ignore paths

```bash
echo '{"id": 1, "ts": "x", "hash": "y"}' | \
    outmatch --json --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'
```

## Nested ignore path

```bash
echo '{"user": {"name": "alice", "created": "2024-01-01"}}' | \
    outmatch --json --json-ignore '$.user.created' '{"user": {"name": "alice"}}'
```

## Ignore array element

The ignore is applied to both sides, so both inputs have the element to remove:

```bash
echo '{"items": [1, 2, 3]}' | outmatch --json --json-ignore '$.items[0]' '{"items": [1, 2, 3]}'
```

## Ignore nested array element

```bash
echo '{"data": {"items": ["a", "b", "c"]}}' | \
    outmatch --json --json-ignore '$.data.items[1]' '{"data": {"items": ["a", "b", "c"]}}'
```

## Ignore path without dot

```bash
echo '{"name": "alice", "id": 1}' | outmatch --json --json-ignore '$name' '{"id": 1}'
```

## Ignore non-existent path

Ignoring a path that doesn't exist should succeed silently:

```bash
echo '{"id": 1}' | outmatch --json --json-ignore '$.nonexistent' '{"id": 1}'
```

## Ignore nested non-existent path

```bash
echo '{"id": 1}' | outmatch --json --json-ignore '$.a.b.c' '{"id": 1}'
```

## Ignore array index out of bounds

```bash
echo '{"items": [1]}' | outmatch --json --json-ignore '$.items[99]' '{"items": [1]}'
```
