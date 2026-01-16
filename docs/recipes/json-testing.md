# JSON Testing Recipes

Practical patterns for testing JSON output with mustmatch.

## Basic JSON Matching

### Exact Match

Field order doesn't matter:

```bash
# These are equivalent
echo '{"a":1,"b":2}' | mustmatch '{"a":1,"b":2}'
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'
```

Values must match exactly:

```bash skip
echo '{"count":42}' | mustmatch '{"count":42}'       # ✓
echo '{"count":42}' | mustmatch '{"count":"42"}'     # ✗ types differ
```

### Subset Matching

Use `like` to match only specific fields:

```bash
# Full response
echo '{"id":1,"name":"Alice","email":"alice@example.com","created":"2024-01-01"}' | \
    mustmatch like '{"id":1,"name":"Alice"}'  # ✓ only check these fields
```

### Nested Objects

```bash
# Match nested structure
echo '{"user":{"id":1,"profile":{"name":"Alice"}}}' | \
    mustmatch like '{"user":{"profile":{"name":"Alice"}}}'
```

## API Testing

### REST Endpoints

```bash skip
# GET request
curl -s https://api.example.com/users/1 | \
    mustmatch like '{"id":1,"name"'

# POST request
curl -s -X POST https://api.example.com/users \
    -H "Content-Type: application/json" \
    -d '{"name":"Bob"}' | \
    mustmatch like '{"id"'  # Just verify ID exists

# Check status
curl -s https://api.example.com/health | \
    mustmatch '{"status":"healthy"}'
```

### Error Responses

```bash skip
# Verify error structure
curl -s https://api.example.com/invalid | \
    mustmatch like '{"error":{"code"'

# Verify specific error
curl -s https://api.example.com/invalid | \
    mustmatch like '{"error":{"code":404}}'
```

### Authentication

```bash skip
# Get token
TOKEN=$(curl -s -X POST https://api.example.com/auth \
    -d '{"user":"demo","pass":"demo"}' | \
    grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Use token
curl -s https://api.example.com/protected \
    -H "Authorization: Bearer $TOKEN" | \
    mustmatch like '{"data"'
```

## Arrays

### Array Length

```bash skip
# Arrays need exact match (order matters)
echo '[1,2,3]' | mustmatch '[1,2,3]'        # ✓
echo '[1,2,3]' | mustmatch '[3,2,1]'        # ✗ order differs

# Subset: check if element exists
echo '[{"id":1},{"id":2},{"id":3}]' | \
    mustmatch like '{"id":2}'  # ✓ ID 2 exists somewhere
```

### Empty Arrays

```bash
echo '{"users":[]}' | mustmatch '{"users":[]}'
```

### Array of Objects

```bash
# Full match
echo '[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]' | \
    mustmatch '[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]'

# Subset: verify one object exists
echo '[{"id":1,"status":"ok"},{"id":2,"status":"ok"}]' | \
    mustmatch like '{"id":1,"status":"ok"}'
```

## Complex Structures

### Deeply Nested

```bash
echo '{
  "data": {
    "user": {
      "profile": {
        "name": "Alice",
        "age": 30
      }
    }
  }
}' | mustmatch like '{"data":{"user":{"profile":{"name":"Alice"}}}}'
```

### Mixed Types

```bash
echo '{
  "string": "value",
  "number": 42,
  "boolean": true,
  "null": null,
  "array": [1, 2, 3],
  "object": {"nested": "value"}
}' | mustmatch like '{"string":"value","number":42,"boolean":true}'
```

## Ignoring Fields

### Timestamps

Can't match exact timestamps, use `like` to ignore:

```bash
# Check everything except timestamp
echo '{"id":1,"name":"Alice","timestamp":"2024-01-01T12:00:00Z"}' | \
    mustmatch like '{"id":1,"name":"Alice"}'
```

### Generated IDs

```bash
# Just verify ID exists, don't check value
echo '{"id":"550e8400-e29b-41d4-a716-446655440000","name":"Alice"}' | \
    mustmatch like '{"name":"Alice"}'

# Or use regex for the whole response
echo '{"id":"550e8400-e29b-41d4-a716-446655440000"}' | \
    mustmatch '/"id":"[0-9a-f-]{36}"/'
```

## JSONL (JSON Lines)

### Streaming Output

```bash
# Multiple JSON objects, one per line
printf '{"event":"start","time":1}\n{"event":"end","time":2}' | \
    mustmatch like '{"event":"start"}'
```

### Log Files

```bash
# Check log contains event
cat app.log | mustmatch like '{"level":"error"}'

# Check for specific error
cat app.log | mustmatch like '{"level":"error","message":"Connection failed"}'
```

### Database Exports

```bash skip
# Export to JSONL
psql -t -c "SELECT row_to_json(t) FROM users t LIMIT 2" | \
    mustmatch like '{"id":1}'
```

## Common Patterns

### Health Checks

```bash
# Simple health
curl -s http://localhost:8080/health | \
    mustmatch '{"status":"ok"}'

# Detailed health
curl -s http://localhost:8080/health | \
    mustmatch like '{"status":"ok","checks":{"database":"ok"}}'
```

### Pagination

```bash skip
# Check pagination metadata
curl -s "https://api.example.com/users?page=1" | \
    mustmatch like '{"data":[{' | \
    mustmatch like '{"page":1,"per_page":10}'

# Verify has next page
curl -s "https://api.example.com/users?page=1" | \
    mustmatch like '{"has_next":true}'
```

### Filtering

```bash skip
# Verify filter applied
curl -s "https://api.example.com/users?status=active" | \
    mustmatch like '{"status":"active"}'

# Verify all items match filter (subset)
curl -s "https://api.example.com/users?status=active" | \
    mustmatch like '{"users":[{"status":"active"}]}'
```

### Sorting

```bash skip
# Check first item
curl -s "https://api.example.com/users?sort=name" | \
    mustmatch like '{"users":[{"name":"Alice"'
```

## Error Handling

### Malformed JSON

```bash
# This will fail with clear error
echo 'not json' | mustmatch '{}'
# Output: Invalid JSON in actual: Expecting value...
```

### Missing Fields

```bash skip
# Subset match won't fail on missing fields
echo '{"a":1}' | mustmatch like '{"a":1,"b":2}'  # ✗ 'b' missing

# But full match will
echo '{"a":1}' | mustmatch '{"a":1,"b":2}'  # ✗ 'b' missing
```

## Debugging

### See What You Got

```bash skip
# Capture response
RESPONSE=$(curl -s https://api.example.com/users)

# Inspect it
echo "Got: $RESPONSE"

# Test it
echo "$RESPONSE" | mustmatch like '{"users":[{'
```

### Pretty Print

```bash skip
# Format JSON for inspection
curl -s https://api.example.com/users | jq '.'

# Then test
curl -s https://api.example.com/users | \
    mustmatch like '{"users":[{'
```

### Check Specific Value

```bash skip
# Extract value first
USER_COUNT=$(curl -s https://api.example.com/stats | \
    grep -o '"user_count":[0-9]*' | cut -d: -f2)

echo "User count: $USER_COUNT"

# Verify it matches expectation
curl -s https://api.example.com/stats | \
    mustmatch like "{\"user_count\":$USER_COUNT}"
```

## Testing Multiple Endpoints

```bash skip
#!/bin/bash
set -e

echo "Testing API..."

# Health check
curl -s http://localhost:8080/health | \
    mustmatch '{"status":"ok"}' || {
    echo "✗ Health check failed"
    exit 1
}

# Get users
curl -s http://localhost:8080/api/users | \
    mustmatch like '{"users":[{' || {
    echo "✗ Users endpoint failed"
    exit 1
}

# Get specific user
curl -s http://localhost:8080/api/users/1 | \
    mustmatch like '{"id":1' || {
    echo "✗ User details failed"
    exit 1
}

echo "✓ All API tests passed"
```

## Configuration Files

### Verify Config Format

```bash
# Check config structure
cat config.json | \
    mustmatch like '{"database":{"host"'

# Verify specific settings
cat config.json | \
    mustmatch like '{"debug":false}'
```

### Environment-Specific

```bash
# Production config should have production DB
cat config.production.json | \
    mustmatch like '{"database":{"host":"prod.db.example.com"}}'

# Dev config should have debug enabled
cat config.development.json | \
    mustmatch like '{"debug":true}'
```

## Summary

Key JSON testing patterns:

- **Exact match**: `mustmatch '{...}'`
- **Subset**: `mustmatch like '{...}'`
- **Nested**: Match only the path you care about
- **Arrays**: Order matters, use subset for flexible matching
- **Ignore fields**: Use subset match, omit fields you don't care about
- **JSONL**: One JSON per line, subset matches any line
- **Debug**: Capture response, inspect, then test

JSON testing is semantic—field order doesn't matter, structure does.
