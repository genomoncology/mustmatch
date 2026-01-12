# JSONL Comparison

Compare JSON Lines (newline-delimited JSON) with four modes:

| Mode               | Order    | Matching                    |
|--------------------|----------|-----------------------------|
| `--jsonl`          | Matters  | Exact record comparison     |
| `--jsonl-set`      | Ignored  | Exact as unordered set      |
| `--jsonl-key F`    | By key   | Match records by field F    |
| `--jsonl-contains` | Ignored  | Subset/partial matching     |

## Ordered JSONL (`--jsonl`)

Records must appear in the same order. Field order within each
record doesn't matter:

```bash
# Single record
echo '{"id": 1}' | outmatch --jsonl '{"id": 1}'

# Multiple records - order matters
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl '{"id": 1}
{"id": 2}'

# Wrong order fails
printf '{"id": 1}\n{"id": 2}' | \
    outmatch --jsonl '{"id": 2}
{"id": 1}' || test $? -eq 1

# Count mismatch
printf '{"id": 1}\n{"id": 2}' | \
    outmatch --jsonl '{"id": 1}' 2>&1 | \
    outmatch --contains "count mismatch"

# Field order within records doesn't matter
echo '{"b": 2, "a": 1}' | outmatch --jsonl '{"a": 1, "b": 2}'
```

## Set Mode (`--jsonl-set`)

Compare as unordered set. Duplicates are preserved (multiset):

```bash
# Order doesn't matter
printf '{"id": 1}\n{"id": 2}' | outmatch --jsonl-set '{"id": 2}
{"id": 1}'

# Duplicates must match
printf '{"id": 1}\n{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 1}'

# Missing record
echo '{"id": 1}' | outmatch --jsonl-set '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing"

# Extra record
printf '{"id": 1}\n{"id": 2}' | \
    outmatch --jsonl-set '{"id": 1}' 2>&1 | \
    outmatch --contains "Extra"
```

## Key Mode (`--jsonl-key`)

Match records by a key field, ignoring order:

```bash
# Match by id field - order doesn't matter
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

Key mode detects various errors:

```bash
# Missing key in actual
echo '{"name": "alice"}' | \
    outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "missing key field"

# Missing key in expected
echo '{"id": 1}' | \
    outmatch --jsonl-key id '{"name": "alice"}' 2>&1 | \
    outmatch --contains "missing key"

# Value mismatch for same key
echo '{"id": 1, "name": "alice"}' | \
    outmatch --jsonl-key id '{"id": 1, "name": "bob"}' 2>&1 | \
    outmatch --contains "Mismatch"

# Duplicate keys
printf '{"id": 1}\n{"id": 1}' | \
    outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Duplicate key"

# Missing keys
printf '{"id": 1}\n{"id": 3}' | \
    outmatch --jsonl-key id '{"id": 1}
{"id": 2}' 2>&1 | outmatch --contains "Missing keys"

# Extra keys
printf '{"id": 1}\n{"id": 2}' | \
    outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "Extra keys"
```

## Contains Mode (`--jsonl-contains`)

Check if actual contains all expected records. Partial field
matching is supported:

```bash
# Find record with id=1 (other fields ignored)
printf '{"id": 1, "name": "alice"}\n{"id": 2, "name": "bob"}' | \
    outmatch --jsonl-contains '{"id": 1}'

# Multiple expected records
printf '{"id": 1}\n{"id": 2}\n{"id": 3}' | \
    outmatch --jsonl-contains '{"id": 1}
{"id": 3}'

# Partial field match
echo '{"id": 1, "name": "alice", "age": 30}' | \
    outmatch --jsonl-contains '{"name": "alice"}'

# Missing record
printf '{"id": 1}\n{"id": 2}' | \
    outmatch --jsonl-contains '{"id": 999}' 2>&1 | \
    outmatch --contains "Missing"

# Works with primitives too
printf '1\n2\n3' | outmatch --jsonl-contains '2'
```

## Ignoring Fields

All JSONL modes support `--json-ignore`:

```bash
# With --jsonl
echo '{"id": 1, "ts": "x"}' | \
    outmatch --jsonl --json-ignore '$.ts' '{"id": 1}'

# With --jsonl-set
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-set --json-ignore '$.ts' '{"id": 2}
{"id": 1}'

# With --jsonl-key
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-key id --json-ignore '$.ts' '{"id": 2}
{"id": 1}'

# With --jsonl-contains
printf '{"id": 1, "ts": "x"}\n{"id": 2, "ts": "y"}' | \
    outmatch --jsonl-contains --json-ignore '$.ts' '{"id": 1}'
```

## Parse Errors

All modes report JSON parse errors:

```bash
echo "not json" | outmatch --jsonl '{"id": 1}' 2>&1 | \
    outmatch --contains "JSON parse error"

echo "not json" | outmatch --jsonl-set '{"id": 1}' 2>&1 | \
    outmatch --contains "JSON parse error"

echo "not json" | outmatch --jsonl-key id '{"id": 1}' 2>&1 | \
    outmatch --contains "JSON parse error"

echo "not json" | outmatch --jsonl-contains '{"id": 1}' 2>&1 | \
    outmatch --contains "JSON parse error"
```
