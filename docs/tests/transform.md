# Pattern Transformations

Replace or redact dynamic values before comparison with `--replace` and `--redact`.

Timestamps, UUIDs, session tokens, file paths - these change between runs. Transform them into stable placeholders so your tests stay deterministic.

## How do I replace dynamic values?

Use `--replace` with the pattern `REGEX=>REPLACEMENT`:

```bash
echo "finished in 1.23s" | outmatch --replace '\d+\.\d+s=><time>' "finished in <time>"
```

The regex matches the dynamic part, and the replacement becomes stable text.

## Can I chain multiple replacements?

Yes. Add multiple `--replace` flags:

```bash
echo "user: alice, id: 12345" | outmatch --replace '\d+=><id>' --replace 'alice=><user>' "user: <user>, id: <id>"
```

Each replacement is applied in order.

## How do I remove dynamic values entirely?

Use an empty replacement:

```bash
echo "hello123world" | outmatch --replace '\d+=>' "helloworld"
```

## What's the difference between replace and redact?

`--redact` always replaces with `<redacted>`:

```bash
echo "token: abc123xyz" | outmatch --redact 'abc\w+xyz' "token: <redacted>"
```

Chain multiple redactions:

```bash
echo "key=secret1 pass=secret2" | \
    outmatch --redact 'secret\d' "key=<redacted> pass=<redacted>"
```

Use `--redact` for sensitive values where you don't need a descriptive placeholder.

## What are common replacement patterns?

**UUIDs:**
```bash
echo "id: 550e8400-e29b-41d4-a716-446655440000" | outmatch --replace '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}=><uuid>' "id: <uuid>"
```

**ISO timestamps:**
```bash
echo "2024-01-15T10:30:00Z" | outmatch --replace '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z=><timestamp>' "<timestamp>"
```

**Temp paths:**
```bash
echo "output: /tmp/abc123/result.txt" | outmatch --replace '/tmp/[a-z0-9]+=><tmpdir>' "output: <tmpdir>/result.txt"
```

## Can I use transformations with other modes?

Yes. Redact works with contains:

```bash
echo "auth: Bearer eyJhbGciOiJIUzI1NiJ9" | \
    outmatch --redact 'Bearer \S+' --contains "<redacted>"
```

Transformations are applied before the comparison mode runs.
