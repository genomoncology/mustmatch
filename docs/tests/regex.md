# Regex Matching

Match output against a regular expression with `--regex`.

Use regex matching when output contains values that change between runs: timestamps, durations, generated IDs, file paths, or performance metrics. The pattern matches if found anywhere in the output.

## When should I use regex vs contains?

Use contains when you're looking for literal text. Use regex when you need pattern flexibility:

```bash
echo "finished in 1.23s" | outmatch --regex 'finished in \d+\.\d+s'
```

The duration changes each run, but the pattern always matches.

## What regex syntax does it use?

Python regex syntax. Common patterns:

- `\d+` - one or more digits
- `\w+` - word characters (letters, digits, underscore)
- `\s+` - whitespace
- `.*` - any characters (greedy)
- `[a-z]+` - character classes
- `(a|b)` - alternation

```bash
echo "abc123xyz" | outmatch --regex '[a-z]+\d+[a-z]+'
```

```bash
echo "success" | outmatch --regex 'success|failure'
```

## How do I match the entire output?

Anchor with `^` (start) and `$` (end):

```bash
echo "hello world" | outmatch --regex '^hello.*world$'
```

Without anchors, the pattern matches anywhere in the output.

## How do I match across multiple lines?

The regex uses DOTALL mode, so `.` matches newlines:

```bash
printf "line1\nline2\nline3" | outmatch --regex 'line1.*line3'
```

## Is matching case-sensitive?

Yes, by default:

```bash
echo "HELLO" | outmatch --regex 'hello' || test $? -eq 1
```

Use `(?i)` for case-insensitive matching, or combine with `--ignore-case`.

## How do I match optional content?

Use `?` for optional characters or groups:

```bash
echo "color" | outmatch --regex 'colou?r'
```

```bash
echo "colour" | outmatch --regex 'colou?r'
```

## What happens with an invalid regex?

Exit code 2 with an error message:

```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
```

## What happens when the pattern doesn't match?

Exit code 1:

```bash
echo "hello" | outmatch --regex '\d+' || test $? -eq 1
```
