# JSONL Testing

JSONL (JSON Lines) format - multiple JSON objects, one per line.

## Exact JSONL Match

JSONL auto-detects from multi-line JSON syntax:

```bash
# Exact match - same objects, same order
printf '{"id":1}\n{"id":2}' | mustmatch '{"id":1}
{"id":2}'
```

Order matters in exact JSONL:

```python
from mustmatch.services.comparator import jsonl_match

# Order matters in exact match
result = jsonl_match('{"id":2}\n{"id":1}', '{"id":1}\n{"id":2}')
assert not result.matches
```

## Subset Matching

Use `like` to check if objects exist:

```bash
cat > /tmp/subset.jsonl << 'EOF'
{"id":1,"status":"ok"}
{"id":2,"status":"ok"}
EOF

cat /tmp/subset.jsonl | mustmatch like '{"status":"ok"}'
rm /tmp/subset.jsonl
```

## Streaming Data

```bash
printf '{"event":"start","time":1}\n{"event":"process","time":2}\n{"event":"end","time":3}' > /tmp/events.jsonl
cat /tmp/events.jsonl | mustmatch like '{"event":"start"}'
cat /tmp/events.jsonl | mustmatch like '{"event":"end"}'
rm /tmp/events.jsonl
```

## Error Handling

Invalid JSON is detected:

```python
from mustmatch.services.comparator import jsonl_match

# Invalid JSON in actual
result = jsonl_match('not json\n{"id":1}', '{"id":1}')
assert not result.matches
assert "Invalid JSON on line 1" in result.message

# Invalid JSON in expected
result = jsonl_match('{"id":1}', 'not json')
assert not result.matches
assert "Invalid JSON in expected" in result.message
```

## Object Not Found

```python
from mustmatch.services.comparator import jsonl_match

# Subset mode - object not found
result = jsonl_match(
    '{"id":1,"status":"ok"}\n{"id":2,"status":"ok"}',
    '{"id":3}',
    subset=True
)
assert not result.matches
assert "Expected object not found" in result.message
```

## Exact vs Subset

```python
from mustmatch.services.comparator import jsonl_match

# Exact match - must be identical
result = jsonl_match('{"id":1}\n{"id":2}', '{"id":1}\n{"id":2}')
assert result.matches

# Different order fails exact match
result = jsonl_match('{"id":2}\n{"id":1}', '{"id":1}\n{"id":2}')
assert not result.matches

# But subset mode checks existence
result = jsonl_match('{"id":1}\n{"id":2}', '{"id":2}', subset=True)
assert result.matches
```
