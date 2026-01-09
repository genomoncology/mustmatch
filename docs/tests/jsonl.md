# JSONL Mode Tests

Tests for JSONL comparison modes.

## Basic JSONL match

```bash
echo '{"id": 1}' | outmatch --jsonl '{"id": 1}'
```

## Field order independence

```bash
echo '{"name": "alice", "age": 30}' | outmatch --jsonl '{"age": 30, "name": "alice"}'
```

## Multiple records

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
```

## Record order matters

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 2}
{"id": 1}' || test $? -eq 1
```

## Record count mismatch

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}' 2>&1 | \
    outmatch --contains "count mismatch"
```

## Nested objects in JSONL

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    outmatch --jsonl '{"user": {"age": 30, "name": "alice"}}'
```

## Invalid JSON in JSONL

```bash
echo "not json" | outmatch --jsonl '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

## JSONL with ignore path

```bash
echo '{"id": 1, "ts": "x"}' | outmatch --jsonl --json-ignore '$.ts' '{"id": 1}'
```

## Blank lines ignored

```bash
printf '{"id": 1}\n\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
```

# JSONL Set Mode

Order-independent comparison with `--jsonl-set`.

## Set order independence

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 2}
{"id": 1}'
```

## Set duplicate handling

```bash
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 1}'
```

## Set missing record

```bash
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing"
```

## Set extra record

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "Extra"
```

# JSONL Key Mode

Match by key field with `--jsonl-key`.

## Key-based matching

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

## Missing key field in actual

```bash
echo '{"name": "alice"}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "missing key field"
```

## Missing key field in expected

```bash
echo '{"id": 1}' | outmatch --jsonl-key id '{"name": "alice"}' 2>&1 | \
    outmatch --contains "missing key"
```

## Key value mismatch

```bash
echo '{"id": 1, "name": "alice"}' | \
    outmatch --jsonl-key id '{"id": 1, "name": "bob"}' 2>&1 | \
    outmatch --contains "Mismatch"
```

# JSONL Contains Mode

Subset matching with `--jsonl-contains`.

## Single record contains

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-contains '{"id": 1}'
```

## Multiple expected records

```bash
printf '{"id": 1}\n{"id": 2}\n{"id": 3}' | outmatch --jsonl-contains '{"id": 1}
{"id": 3}'
```

## Partial field match

```bash
echo '{"id": 1, "name": "alice", "age": 30}' | outmatch --jsonl-contains '{"name": "alice"}'
```

## Missing record fails

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-contains '{"id": 999}' 2>&1 | \
    outmatch --contains "Missing"
```

# Edge Cases

## Invalid JSON in jsonl-set mode

```bash
echo "not json" | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

## Invalid JSON in jsonl-key mode

```bash
echo "not json" | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

## Invalid JSON in jsonl-contains mode

```bash
echo "not json" | outmatch --jsonl-contains '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

## JSONL set with json-ignore

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-set --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
```

## JSONL key with json-ignore

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-key id --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
```

## JSONL contains with json-ignore

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-contains --json-ignore '$.ts' '{"id": 1}'
```

## Duplicate key in actual records

```bash
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Duplicate key"
```

## Duplicate key in expected records

```bash
echo '{"id": 1}' | outmatch --jsonl-key id '{"id": 1}
{"id": 1}' 2>&1 | \
    outmatch --contains "Duplicate key"
```

## Missing and extra keys reported

```bash
printf '{"id": 1}\n{"id": 3}' | outmatch --jsonl-key id '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing keys"
```

## Extra keys reported

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Extra keys"
```

## Non-dict records in jsonl-contains

```bash
printf '1\n2\n3' | outmatch --jsonl-contains '2'
```

## Many missing records truncated

```bash
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}
{"id": 3}
{"id": 4}
{"id": 5}
{"id": 6}
{"id": 7}' 2>&1 | outmatch --contains "and 1 more"
```

## Many extra records truncated

```bash
printf '{"id": 1}\n{"id": 2}\n{"id": 3}\n{"id": 4}\n{"id": 5}\n{"id": 6}\n{"id": 7}' | \
    outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "and 1 more"
```
