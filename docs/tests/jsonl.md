# JSONL Comparison

Compare line-delimited JSON with four modes:

| Mode | Order | Matching |
|------|-------|----------|
| `--jsonl` | Matters | Exact |
| `--jsonl-set` | Ignored | Exact |
| `--jsonl-key` | By key | By key field |
| `--jsonl-contains` | Ignored | Subset |

## Basic JSONL (`--jsonl`)

Order-sensitive comparison with field-order independence:

```bash
echo '{"id": 1}' | outmatch --jsonl '{"id": 1}'
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 2}
{"id": 1}' || test $? -eq 1
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}' 2>&1 | outmatch --contains "count mismatch"
printf '{"id": 1}\n\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
echo '{"user": {"name": "alice", "age": 30}}' | outmatch --jsonl '{"user": {"age": 30, "name": "alice"}}'
```

## Set Mode (`--jsonl-set`)

Order-independent exact comparison:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 2}
{"id": 1}'
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 1}'
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing"
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "Extra"
```

## Key Mode (`--jsonl-key`)

Match by key field:

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | outmatch --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
echo '{"name": "alice"}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "missing key field"
echo '{"id": 1}' | outmatch --jsonl-key id '{"name": "alice"}' 2>&1 | outmatch --contains "missing key"
echo '{"id": 1, "name": "alice"}' | outmatch --jsonl-key id '{"id": 1, "name": "bob"}' 2>&1 | outmatch --contains "Mismatch"
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "Duplicate key"
echo '{"id": 1}' | outmatch --jsonl-key id '{"id": 1}
{"id": 1}' 2>&1 | outmatch --contains "Duplicate key"
printf '{"id": 1}\n{"id": 3}' | outmatch --jsonl-key id '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing keys"
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "Extra keys"
```

## Contains Mode (`--jsonl-contains`)

Subset matching:

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | outmatch --jsonl-contains '{"id": 1}'
printf '{"id": 1}\n{"id": 2}\n{"id": 3}' | outmatch --jsonl-contains '{"id": 1}
{"id": 3}'
echo '{"id": 1, "name": "alice", "age": 30}' | outmatch --jsonl-contains '{"name": "alice"}'
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-contains '{"id": 999}' 2>&1 | outmatch --contains "Missing"
printf '1\n2\n3' | outmatch --jsonl-contains '2'
```

## Ignoring Fields

All modes support `--json-ignore`:

```bash
echo '{"id": 1, "ts": "x"}' | outmatch --jsonl --json-ignore '$.ts' '{"id": 1}'
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | outmatch --jsonl-set --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | outmatch --jsonl-key id --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | outmatch --jsonl-contains --json-ignore '$.ts' '{"id": 1}'
```

## Errors

```bash
echo "not json" | outmatch --jsonl '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
echo "not json" | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
echo "not json" | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
echo "not json" | outmatch --jsonl-contains '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

## Edge Cases

```bash
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}
{"id": 3}
{"id": 4}
{"id": 5}
{"id": 6}
{"id": 7}' 2>&1 | outmatch --contains "and 1 more"

printf '{"id": 1}\n{"id": 2}\n{"id": 3}\n{"id": 4}\n{"id": 5}\n{"id": 6}\n{"id": 7}' | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "and 1 more"
```
