# Text Matching Modes

mustmatch supports three text matching modes: exact (default), contains,
and regex. For structured data, see [JSON](json.md) and [JSONL](jsonl.md).

## Exact Match (default)

Output must match character-for-character. Trailing newlines are
normalized automatically.

```bash
echo "hello world" | mustmatch "hello world"
printf "hello\n" | mustmatch "hello"
printf "line one\nline two" | mustmatch "line one
line two"
```

Unicode and special characters work:

```bash
printf "Hello 世界 🌍" | mustmatch "Hello 世界 🌍"
printf '{"key": "value"}' | mustmatch '{"key": "value"}'
```

Mismatch returns exit code 1:

```bash
echo "hello" | mustmatch "world" || test $? -eq 1
```

## Contains (`--contains`)

Check if output includes a substring anywhere. Whitespace is
trimmed from expected.

```bash
echo "hello world" | mustmatch --contains "world"
echo "hello world" | mustmatch --contains "hello"
echo "the quick brown fox" | mustmatch --contains "quick brown"
echo "hello world" | mustmatch --contains "  world  "
```

Works across multiple lines:

```bash
printf "line one\nline two\nline three" | \
    mustmatch --contains "line two"
```

Case-sensitive by default:

```bash
echo "Hello World" | mustmatch --contains "hello" || test $? -eq 1
echo "Hello World" | mustmatch --contains --ignore-case "hello"
```

Missing substring returns exit code 1:

```bash
echo "hello" | mustmatch --contains "goodbye" || test $? -eq 1
printf "" | mustmatch --contains "something" || test $? -eq 1
```

## Regex (`--regex`)

Match output against a Python regex pattern. Uses DOTALL mode
(`.` matches newlines) and MULTILINE mode.

```bash
echo "finished in 1.23s" | \
    mustmatch --regex 'finished in \d+\.\d+s'
echo "abc123xyz" | mustmatch --regex '[a-z]+\d+[a-z]+'
echo "success" | mustmatch --regex 'success|failure'
printf "line1\nline2\nline3" | mustmatch --regex 'line1.*line3'
```

Use anchors for full match:

```bash
echo "hello world" | mustmatch --regex '^hello.*world$'
```

Optional groups:

```bash
echo "color" | mustmatch --regex 'colou?r'
echo "colour" | mustmatch --regex 'colou?r'
```

Case-sensitive by default:

```bash
echo "HELLO" | mustmatch --regex 'hello' || test $? -eq 1
```

Invalid regex returns exit code 2:

```bash
echo "test" | mustmatch --regex '[invalid' 2>&1 | \
    mustmatch --contains "Invalid regex"
```

Pattern not found returns exit code 1:

```bash
echo "hello" | mustmatch --regex '\d+' || test $? -eq 1
```

## Edge Cases

Empty output and large output work correctly:

```bash
printf "" | mustmatch ""
python3 -c "print('x' * 1000)" | \
    mustmatch "$(python3 -c "print('x' * 1000)")"
```
