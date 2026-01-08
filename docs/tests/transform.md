# Pattern Transformation Tests

Tests for `--replace` and `--redact` options.

## Basic replace

```bash
echo "finished in 1.23s" | \
    expect --replace '\d+\.\d+s' '<time>' "finished in <time>"
```

## Multiple replacements

```bash
echo "user: alice, id: 12345" | \
    expect --replace '\d+' '<id>' --replace 'alice' '<user>' "user: <user>, id: <id>"
```

## Replace with empty string

```bash
echo "hello123world" | outmatchall --replace '\d+' '' "helloworld"
```

## Basic redact

```bash
echo "token: abc123xyz" | outmatchall --redact 'abc\w+xyz' "token: <redacted>"
```

## Multiple redactions

```bash
echo "key=secret1 pass=secret2" | \
    expect --redact 'secret\d' "key=<redacted> pass=<redacted>"
```

## Replace UUID

```bash
echo "id: 550e8400-e29b-41d4-a716-446655440000" | \
    expect --replace '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' '<uuid>' \
    "id: <uuid>"
```

## Replace timestamp

```bash
echo "2024-01-15T10:30:00Z" | \
    expect --replace '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z' '<timestamp>' "<timestamp>"
```

## Replace path

```bash
echo "output: /tmp/abc123/result.txt" | \
    expect --replace '/tmp/[a-z0-9]+' '<tmpdir>' "output: <tmpdir>/result.txt"
```

## Redact with contains

```bash
echo "auth: Bearer eyJhbGciOiJIUzI1NiJ9" | \
    expect --redact 'Bearer \S+' --contains "<redacted>"
```
