# Regex Mode Tests

Tests for regex pattern matching with `--regex`.

## Basic regex

```bash
echo "finished in 1.23s" | expect --regex 'finished in \d+\.\d+s'
```

## Multiline regex

Regex mode uses DOTALL, so `.` matches newlines:

```bash
printf "line1\nline2\nline3" | expect --regex 'line1.*line3'
```

## Anchored pattern

```bash
echo "hello world" | expect --regex '^hello.*world$'
```

## Character classes

```bash
echo "abc123xyz" | expect --regex '[a-z]+\d+[a-z]+'
```

## Alternation

```bash
echo "success" | expect --regex 'success|failure'
```

## Pattern not found fails

```bash
echo "hello" | expect --regex '\d+' || test $? -eq 1
```

## Invalid regex returns error

```bash
echo "test" | expect --regex '[invalid' 2>&1 | expect --contains "Invalid regex"
```

## Case sensitivity

Regex is case-sensitive by default:

```bash
echo "HELLO" | expect --regex 'hello' || test $? -eq 1
```

## Optional groups

```bash
echo "color" | expect --regex 'colou?r'
```

```bash
echo "colour" | expect --regex 'colou?r'
```
