# Text Matching

mustmatch supports exact, contains, and regex matching with auto-detection.

## Exact Match (default)

Output must match character-for-character:

```bash
echo "hello world" | mustmatch "hello world"
printf "hello\n" | mustmatch "hello"
printf "line one\nline two" | mustmatch "line one
line two"
```

Unicode and special characters work:

```bash
printf "Hello 世界" | mustmatch "Hello 世界"
```

Mismatch returns exit code 1:

```bash
echo "hello" | mustmatch "world" || test $? -eq 1
```

## Contains (`like`)

Use `like` to check if output includes a substring:

```bash
echo "hello world" | mustmatch like "world"
echo "hello world" | mustmatch like "hello"
```

Works across multiple lines:

```bash
printf "line one\nline two\nline three" | mustmatch like "line two"
```

## Regex (auto-detected)

Wrap patterns in `/.../' for regex matching:

```bash
echo "finished in 1.23s" | mustmatch "/finished in \d+\.\d+s/"
echo "abc123xyz" | mustmatch "/[a-z]+\d+[a-z]+/"
```

Use anchors for full match:

```bash
echo "hello world" | mustmatch "/^hello.*world$/"
```

## Case-Insensitive

Use `-i` for case-insensitive comparison:

```bash
echo "Hello World" | mustmatch -i "hello world"
echo "HELLO" | mustmatch -i like "hello"
```

## Negation

Use `not` to assert something is NOT present:

```bash
echo "hello world" | mustmatch not "error"
echo "hello world" | mustmatch not like "error"
echo "success" | mustmatch not "/error|fail/"
```

## Edge Cases

Empty output and large output work correctly:

```bash
printf "" | mustmatch ""
python3 -c "print('x' * 100)" | mustmatch "$(python3 -c "print('x' * 100)")"
```
