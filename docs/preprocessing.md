# Output Preprocessing

Normalize and transform output before comparison.

## Normalization Flags

| Flag                    | Effect                              |
|-------------------------|-------------------------------------|
| `--strip-ansi`          | Remove ANSI escape codes            |
| `--normalize-newlines`  | Convert CRLF to LF                  |
| `--trim`                | Remove leading/trailing whitespace  |
| `--collapse-whitespace` | Collapse whitespace runs to space   |
| `--ignore-case` / `-i`  | Case-insensitive comparison         |

```bash
printf '\033[31mred\033[0m' | outmatch --strip-ansi "red"
printf '\033[32mSuccess\033[0m' | \
    outmatch --strip-ansi --contains "Success"
printf "line1\r\nline2" | outmatch --normalize-newlines "line1
line2"
printf "  hello world  \n" | outmatch --trim "hello world"
printf "hello    world\n\nfoo" | \
    outmatch --collapse-whitespace "hello world foo"
echo "Hello World" | outmatch --ignore-case "hello world"
echo "HELLO" | outmatch -i "hello"
echo "Hello World" | outmatch --contains --ignore-case "hello"
```

Combine flags:

```bash
printf '\033[32m  HELLO   WORLD  \033[0m' | \
    outmatch --strip-ansi --trim \
    --collapse-whitespace --ignore-case "hello world"
```

Normalization applies to both actual and expected:

```bash
printf "hello world" | \
    outmatch --collapse-whitespace "hello    world"
```

## Pattern Replacement

Use `--replace 'REGEX=>REPLACEMENT'` for dynamic values like
timestamps, IDs, and paths:

```bash
# Basic replacement
echo "finished in 1.23s" | \
    outmatch --replace '\d+\.\d+s=><time>' "finished in <time>"

# Multiple replacements
echo "user: alice, id: 12345" | \
    outmatch --replace '\d+=><id>' \
    --replace 'alice=><user>' \
    "user: <user>, id: <id>"

# Replace with empty string (delete)
echo "hello123world" | outmatch --replace '\d+=>' "helloworld"
```

## Common Patterns

```bash
# UUIDs
echo "id: 550e8400-e29b-41d4-a716-446655440000" | \
    outmatch --replace \
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}=><uuid>' \
    "id: <uuid>"

# ISO timestamps
echo "2024-01-15T10:30:00Z" | \
    outmatch --replace \
    '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z=><ts>' \
    "<ts>"

# Temp paths
echo "output: /tmp/abc123/result.txt" | \
    outmatch --replace '/tmp/[a-z0-9]+=><tmpdir>' \
    "output: <tmpdir>/result.txt"
```

## Redaction

Use `--redact` to replace with `<redacted>`:

```bash
echo "token: abc123xyz" | \
    outmatch --redact 'abc\w+xyz' "token: <redacted>"

echo "key=secret1 pass=secret2" | \
    outmatch --redact 'secret\d' \
    "key=<redacted> pass=<redacted>"

echo "auth: Bearer eyJhbGciOiJIUzI1NiJ9" | \
    outmatch --redact 'Bearer \S+' --contains "<redacted>"
```
