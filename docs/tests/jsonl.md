# JSONL Comparison

Compare line-delimited JSON (JSONL) with multiple modes for different use cases.

JSONL is JSON with one object per line. Log files, data exports, and streaming APIs often use this format. outmatch provides four comparison modes depending on whether order matters and how you want to match records.

## Choosing a JSONL Mode

| Mode | Order | Matching | Use when... |
|------|-------|----------|-------------|
| `--jsonl` | Matters | Exact | Output order is deterministic |
| `--jsonl-set` | Ignored | Exact | Order varies but records are stable |
| `--jsonl-key` | Ignored | By key | Records have unique IDs |
| `--jsonl-contains` | Ignored | Subset | You only care about specific records |

---

## Basic JSONL (`--jsonl`)

Compares records in order with field-order independence within each record.

```bash
echo '{"id": 1}' | outmatch --jsonl '{"id": 1}'
```

Multiple records must appear in the same order:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
```

Wrong order fails:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 2}
{"id": 1}' || test $? -eq 1
```

Record count must match:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}' 2>&1 | \
    outmatch --contains "count mismatch"
```

Blank lines are ignored:

```bash
printf '{"id": 1}\n\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'
```

---

## Set Mode (`--jsonl-set`)

Compares records regardless of order. Both sides must have the same records.

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 2}
{"id": 1}'
```

Duplicates are compared as-is:

```bash
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 1}'
```

Missing records are reported:

```bash
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing"
```

Extra records are reported:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "Extra"
```

---

## Key Mode (`--jsonl-key`)

Matches records by a key field, allowing different order but requiring matching keys.

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

Missing key field is an error:

```bash
echo '{"name": "alice"}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "missing key field"
```

```bash
echo '{"id": 1}' | outmatch --jsonl-key id '{"name": "alice"}' 2>&1 | \
    outmatch --contains "missing key"
```

Value mismatch for same key is reported:

```bash
echo '{"id": 1, "name": "alice"}' | \
    outmatch --jsonl-key id '{"id": 1, "name": "bob"}' 2>&1 | \
    outmatch --contains "Mismatch"
```

Duplicate keys are rejected:

```bash
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Duplicate key"
```

```bash
echo '{"id": 1}' | outmatch --jsonl-key id '{"id": 1}
{"id": 1}' 2>&1 | \
    outmatch --contains "Duplicate key"
```

Missing and extra keys are reported:

```bash
printf '{"id": 1}\n{"id": 3}' | outmatch --jsonl-key id '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing keys"
```

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Extra keys"
```

---

## Contains Mode (`--jsonl-contains`)

Checks that expected records exist somewhere in the output. Order and extra records don't matter.

Find a single record by partial match:

```bash
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-contains '{"id": 1}'
```

Find multiple records:

```bash
printf '{"id": 1}\n{"id": 2}\n{"id": 3}' | outmatch --jsonl-contains '{"id": 1}
{"id": 3}'
```

Match by any fields:

```bash
echo '{"id": 1, "name": "alice", "age": 30}' | outmatch --jsonl-contains '{"name": "alice"}'
```

Missing record fails:

```bash
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-contains '{"id": 999}' 2>&1 | \
    outmatch --contains "Missing"
```

Non-dict values work too:

```bash
printf '1\n2\n3' | outmatch --jsonl-contains '2'
```

---

## Using json-ignore with JSONL

All JSONL modes support `--json-ignore` for volatile fields:

```bash
echo '{"id": 1, "ts": "x"}' | outmatch --jsonl --json-ignore '$.ts' '{"id": 1}'
```

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-set --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
```

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-key id --json-ignore '$.ts' '{"id": 2}
{"id": 1}'
```

```bash
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-contains --json-ignore '$.ts' '{"id": 1}'
```

---

## Nested Objects

Field order independence applies at all nesting levels:

```bash
echo '{"user": {"name": "alice", "age": 30}}' | \
    outmatch --jsonl '{"user": {"age": 30, "name": "alice"}}'
```

---

## Error Handling

Invalid JSON produces a parse error:

```bash
echo "not json" | outmatch --jsonl '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

```bash
echo "not json" | outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

```bash
echo "not json" | outmatch --jsonl-key id '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

```bash
echo "not json" | outmatch --jsonl-contains '{"id": 1}' 2>&1 | outmatch --contains "JSON parse error"
```

---

## Edge Cases

Many missing/extra records are truncated in output:

```bash
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}
{"id": 3}
{"id": 4}
{"id": 5}
{"id": 6}
{"id": 7}' 2>&1 | outmatch --contains "and 1 more"
```

```bash
printf '{"id": 1}\n{"id": 2}\n{"id": 3}\n{"id": 4}\n{"id": 5}\n{"id": 6}\n{"id": 7}' | \
    outmatch --jsonl-set '{"id": 1}' 2>&1 | outmatch --contains "and 1 more"
```
