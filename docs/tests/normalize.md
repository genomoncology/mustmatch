# Normalization Tests

Tests for text normalization options.

## Strip ANSI

Remove color codes:

```bash
printf '\033[31mred\033[0m' | outmatchall --strip-ansi "red"
```

## Strip ANSI with contains

```bash
printf '\033[32mSuccess\033[0m' | outmatchall --strip-ansi --contains "Success"
```

## Normalize newlines

Convert CRLF to LF:

```bash
printf "line1\r\nline2" | outmatchall --normalize-newlines "line1
line2"
```

## Trim whitespace

```bash
printf "  hello world  \n" | outmatchall --trim "hello world"
```

## Collapse whitespace

```bash
printf "hello    world\n\nfoo" | outmatchall --collapse-whitespace "hello world foo"
```

## Ignore case

```bash
echo "Hello World" | outmatchall --ignore-case "hello world"
```

## Ignore case short flag

```bash
echo "HELLO" | outmatchall -i "hello"
```

## Contains with ignore case

```bash
echo "Hello World" | outmatchall --contains --ignore-case "hello"
```

## Combined normalization

Multiple flags work together:

```bash
printf '\033[32m  HELLO   WORLD  \033[0m' | \
    expect --strip-ansi --trim --collapse-whitespace --ignore-case "hello world"
```

## Normalization applies to both sides

Expected is also normalized:

```bash
echo "hello world" | outmatchall --collapse-whitespace "hello    world"
```
