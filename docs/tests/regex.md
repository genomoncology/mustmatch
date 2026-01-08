# Regex Mode Tests

Tests for regex pattern matching with `--regex`.

## Basic regex

```bash
echo "finished in 1.23s" | outmatchall --regex 'finished in \d+\.\d+s'
```

## Multiline regex

Regex mode uses DOTALL, so `.` matches newlines:

```bash
printf "line1\nline2\nline3" | outmatchall --regex 'line1.*line3'
```

## Anchored pattern

```bash
echo "hello world" | outmatchall --regex '^hello.*world$'
```

## Character classes

```bash
echo "abc123xyz" | outmatchall --regex '[a-z]+\d+[a-z]+'
```

## Alternation

```bash
echo "success" | outmatchall --regex 'success|failure'
```

## Pattern not found fails

```bash
echo "hello" | outmatchall --regex '\d+' || test $? -eq 1
```

## Invalid regex returns error

```bash
echo "test" | outmatchall --regex '[invalid' 2>&1 | outmatchall --contains "Invalid regex"
```

## Case sensitivity

Regex is case-sensitive by default:

```bash
echo "HELLO" | outmatchall --regex 'hello' || test $? -eq 1
```

## Optional groups

```bash
echo "color" | outmatchall --regex 'colou?r'
```

```bash
echo "colour" | outmatchall --regex 'colou?r'
```
