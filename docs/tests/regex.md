# Regex Mode Tests

Tests for regex pattern matching with `--regex`.

## Basic regex

```bash
echo "finished in 1.23s" | outmatch --regex 'finished in \d+\.\d+s'
```

## Multiline regex

Regex mode uses DOTALL, so `.` matches newlines:

```bash
printf "line1\nline2\nline3" | outmatch --regex 'line1.*line3'
```

## Anchored pattern

```bash
echo "hello world" | outmatch --regex '^hello.*world$'
```

## Character classes

```bash
echo "abc123xyz" | outmatch --regex '[a-z]+\d+[a-z]+'
```

## Alternation

```bash
echo "success" | outmatch --regex 'success|failure'
```

## Pattern not found fails

```bash
echo "hello" | outmatch --regex '\d+' || test $? -eq 1
```

## Invalid regex returns error

```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
```

## Case sensitivity

Regex is case-sensitive by default:

```bash
echo "HELLO" | outmatch --regex 'hello' || test $? -eq 1
```

## Optional groups

```bash
echo "color" | outmatch --regex 'colou?r'
```

```bash
echo "colour" | outmatch --regex 'colou?r'
```
