# JSON Mode Tests

Tests for JSON semantic comparison with `--json`.

## Basic JSON match

```bash
echo '{"name": "alice", "age": 30}' | outmatchall --json '{"name": "alice", "age": 30}'
```

## Field order independence

```bash
echo '{"name": "alice", "age": 30}' | outmatchall --json '{"age": 30, "name": "alice"}'
```

## Nested objects

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    expect --json '{"user": {"age": 30, "name": "alice"}}'
```

## Arrays

```bash
echo '[1, 2, 3]' | outmatchall --json '[1, 2, 3]'
```

## Array order matters

Arrays preserve order (this should fail):

```bash
echo '[1, 2, 3]' | outmatchall --json '[3, 2, 1]' || test $? -eq 1
```

## Boolean and null values

```bash
echo '{"active": true, "data": null}' | outmatchall --json '{"data": null, "active": true}'
```

## Numbers

```bash
echo '{"int": 42, "float": 3.14}' | outmatchall --json '{"float": 3.14, "int": 42}'
```

## Invalid actual JSON fails

```bash
echo "not json" | outmatchall --json '{"id": 1}' 2>&1 | outmatchall --contains "not valid JSON"
```

## Invalid expected JSON fails

```bash
echo '{"id": 1}' | outmatchall --json "not json" 2>&1 | outmatchall --contains "not valid JSON"
```

## JSON mismatch shows diff

```bash
echo '{"name": "alice"}' | outmatchall --json '{"name": "bob"}' 2>&1 | outmatchall --contains "mismatch"
```

## JSON with ignore path

Ignore a timestamp field:

```bash
echo '{"id": 1, "ts": "2024-01-01"}' | outmatchall --json --json-ignore '$.ts' '{"id": 1}'
```

## Multiple ignore paths

```bash
echo '{"id": 1, "ts": "x", "hash": "y"}' | \
    expect --json --json-ignore '$.ts' --json-ignore '$.hash' '{"id": 1}'
```

## Nested ignore path

```bash
echo '{"user": {"name": "alice", "created": "2024-01-01"}}' | \
    expect --json --json-ignore '$.user.created' '{"user": {"name": "alice"}}'
```
