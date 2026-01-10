# Text Normalization

Normalize output before comparison to handle formatting differences.

Real-world output often includes ANSI color codes, inconsistent whitespace, or case variations. Normalization flags let you ignore these differences and focus on the content that matters.

## What normalization options are available?

| Flag | Effect |
|------|--------|
| `--strip-ansi` | Remove ANSI escape codes (colors, formatting) |
| `--normalize-newlines` | Convert CRLF to LF |
| `--trim` | Remove leading/trailing whitespace |
| `--collapse-whitespace` | Replace runs of whitespace with single space |
| `--ignore-case` / `-i` | Case-insensitive comparison |

## How do I remove color codes from output?

Use `--strip-ansi` to remove ANSI escape sequences:

```bash
printf '\033[31mred\033[0m' | outmatch --strip-ansi "red"
```

Works with any mode:

```bash
printf '\033[32mSuccess\033[0m' | outmatch --strip-ansi --contains "Success"
```

## How do I handle Windows line endings?

Use `--normalize-newlines` to convert CRLF to LF:

```bash
printf "line1\r\nline2" | outmatch --normalize-newlines "line1
line2"
```

## How do I ignore leading and trailing whitespace?

Use `--trim`:

```bash
printf "  hello world  \n" | outmatch --trim "hello world"
```

## How do I handle inconsistent spacing?

Use `--collapse-whitespace` to normalize all whitespace runs to single spaces:

```bash
printf "hello    world\n\nfoo" | outmatch --collapse-whitespace "hello world foo"
```

## How do I ignore case differences?

Use `--ignore-case` or `-i`:

```bash
echo "Hello World" | outmatch --ignore-case "hello world"
```

```bash
echo "HELLO" | outmatch -i "hello"
```

Works with contains mode:

```bash
echo "Hello World" | outmatch --contains --ignore-case "hello"
```

## Can I combine multiple normalization flags?

Yes. All flags work together:

```bash
printf '\033[32m  HELLO   WORLD  \033[0m' | \
    outmatch --strip-ansi --trim --collapse-whitespace --ignore-case "hello world"
```

## Does normalization apply to both sides?

Yes. Both actual output and expected value are normalized:

```bash
printf "hello world" | outmatch --collapse-whitespace "hello    world"
```

This makes expected values more readable without requiring perfect formatting.
