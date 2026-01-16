# Comparison Modes

mustmatch auto-detects the comparison mode from syntax.

## Exact Match

Default mode - character-for-character comparison:

```bash
echo "hello" | mustmatch "hello"
```

## Contains (`like`)

Check if substring exists:

```bash
echo "hello world" | mustmatch like "world"
echo "hello world" | mustmatch like "hello"
echo "mustmatch is great" | mustmatch like "mustmatch"
```

## Negation (`not`)

Invert any match:

```bash
# Assert NOT equal
echo "success" | mustmatch not "error"

# Assert NOT contains
echo "success" | mustmatch not like "error"
```

## Regex (`/pattern/`)

Wrap patterns in slashes:

```bash
# Date format
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Version numbers
echo "v1.2.3" | mustmatch '/^v\d+\.\d+\.\d+$/'

# Any number
echo "count: 42" | mustmatch '/count: \d+/'
```

## JSON (semantic)

JSON is compared semantically - field order doesn't matter:

```bash
# Same JSON, different field order
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Nested objects
echo '{"data":{"id":1,"name":"test"}}' | mustmatch '{"data":{"id":1,"name":"test"}}'
```

## JSON Subset (`like`)

Match only specific fields:

```bash
# Check only status field
echo '{"status":"ok","count":42,"timestamp":"2024-01-01"}' | \
    mustmatch like '{"status":"ok"}'

# Nested subset
echo '{"data":{"user":{"id":1,"name":"Alice","email":"a@b.com"}}}' | \
    mustmatch like '{"data":{"user":{"id":1}}}'
```

## Case Insensitive (`-i`)

```bash
echo "HELLO" | mustmatch -i "hello"
echo "Hello World" | mustmatch -i like "WORLD"
```

## Quiet Mode (`-q`)

Suppress error output:

```bash
echo "test" | mustmatch -q "other"
echo $?  # 1 (failed silently)
```
