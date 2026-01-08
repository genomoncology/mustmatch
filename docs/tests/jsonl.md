# JSONL Mode Tests

Tests for JSONL comparison modes.

## Basic JSONL match

```bash
echo '{"id": 1}' | expect --jsonl '{"id": 1}'
```

## Field order independence

```bash
echo '{"name": "alice", "age": 30}' | expect --jsonl '{"age": 30, "name": "alice"}'
```

## Multiple records

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl '{"id": 1}
{"id": 2}'
```

## Record order matters

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl '{"id": 2}
{"id": 1}' || test $? -eq 1
```

## Record count mismatch

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl '{"id": 1}' 2>&1 | \
    expect --contains "count mismatch"
```

## Nested objects in JSONL

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    expect --jsonl '{"user": {"age": 30, "name": "alice"}}'
```

## Invalid JSON in JSONL

```bash
echo "not json" | expect --jsonl '{"id": 1}' 2>&1 | expect --contains "JSON parse error"
```

## JSONL with ignore path

```bash
echo '{"id": 1, "ts": "x"}' | expect --jsonl --json-ignore '$.ts' '{"id": 1}'
```

## Blank lines ignored

```bash
printf '{"id": 1}\n\n{"id": 2}' | expect --jsonl '{"id": 1}
{"id": 2}'
```

# JSONL Set Mode

Order-independent comparison with `--jsonl-set`.

## Set order independence

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl-set '{"id": 2}
{"id": 1}'
```

## Set duplicate handling

```bash
printf '{"id": 1}\n{"id": 1}' | expect --jsonl-set '{"id": 1}
{"id": 1}'
```

## Set missing record

```bash
echo '{"id": 1}' | expect --jsonl-set '{"id": 1}
{"id": 2}' 2>&1 | expect --contains "Missing"
```

## Set extra record

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl-set '{"id": 1}' 2>&1 | expect --contains "Extra"
```

# JSONL Key Mode

Match by key field with `--jsonl-key`.

## Key-based matching

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    expect --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

## Missing key field

```bash
echo '{"name": "alice"}' | expect --jsonl-key id '{"id": 1}' 2>&1 | \
    expect --contains "missing key field"
```

## Key value mismatch

```bash
echo '{"id": 1, "name": "alice"}' | \
    expect --jsonl-key id '{"id": 1, "name": "bob"}' 2>&1 | \
    expect --contains "Mismatch"
```

# JSONL Contains Mode

Subset matching with `--jsonl-contains`.

## Single record contains

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    expect --jsonl-contains '{"id": 1}'
```

## Multiple expected records

```bash
printf '{"id": 1}\n{"id": 2}\n{"id": 3}' | expect --jsonl-contains '{"id": 1}
{"id": 3}'
```

## Partial field match

```bash
echo '{"id": 1, "name": "alice", "age": 30}' | expect --jsonl-contains '{"name": "alice"}'
```

## Missing record fails

```bash
printf '{"id": 1}\n{"id": 2}' | expect --jsonl-contains '{"id": 999}' 2>&1 | \
    expect --contains "Missing"
```
