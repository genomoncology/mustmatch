# Matching Modes

outmatch supports three text matching modes: exact (default), contains, and regex.

## Exact Match (default)

Output must match character-for-character. Trailing newlines are normalized automatically.

```bash
echo "hello world" | outmatch "hello world"
printf "hello\n" | outmatch "hello"
printf "line one\nline two" | outmatch "line one
line two"
```

Unicode and special characters work:

```bash
printf "Hello 世界 🌍" | outmatch "Hello 世界 🌍"
printf '{"key": "value"}' | outmatch '{"key": "value"}'
```

Mismatch returns exit code 1:

```bash
echo "hello" | outmatch "world" || test $? -eq 1
```

## Contains (`--contains`)

Check if output includes a substring anywhere. Whitespace is trimmed from expected.

```bash
echo "hello world" | outmatch --contains "world"
echo "hello world" | outmatch --contains "hello"
echo "the quick brown fox" | outmatch --contains "quick brown"
printf "line one\nline two\nline three" | outmatch --contains "line two"
echo "hello world" | outmatch --contains "  world  "
```

Case-sensitive by default:

```bash
echo "Hello World" | outmatch --contains "hello" || test $? -eq 1
echo "Hello World" | outmatch --contains --ignore-case "hello"
```

Missing substring returns exit code 1:

```bash
echo "hello" | outmatch --contains "goodbye" || test $? -eq 1
printf "" | outmatch --contains "something" || test $? -eq 1
```

## Regex (`--regex`)

Match output against a Python regex pattern. Uses DOTALL mode (`.` matches newlines).

```bash
echo "finished in 1.23s" | outmatch --regex 'finished in \d+\.\d+s'
echo "abc123xyz" | outmatch --regex '[a-z]+\d+[a-z]+'
echo "success" | outmatch --regex 'success|failure'
printf "line1\nline2\nline3" | outmatch --regex 'line1.*line3'
```

Anchors for full match:

```bash
echo "hello world" | outmatch --regex '^hello.*world$'
```

Optional groups:

```bash
echo "color" | outmatch --regex 'colou?r'
echo "colour" | outmatch --regex 'colou?r'
```

Case-sensitive by default:

```bash
echo "HELLO" | outmatch --regex 'hello' || test $? -eq 1
```

Invalid regex returns exit code 2:

```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
```

Pattern not found returns exit code 1:

```bash
echo "hello" | outmatch --regex '\d+' || test $? -eq 1
```

## Empty and Large Output

```bash
printf "" | outmatch ""
python3 -c "print('x' * 1000)" | outmatch "$(python3 -c "print('x' * 1000)")"
```
