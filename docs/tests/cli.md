# CLI Options

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Match |
| 1 | Mismatch |
| 2 | Error (invalid arguments, missing file, bad regex) |

```bash
echo "hello" | outmatch "hello" && test $? -eq 0
echo "hello" | outmatch "world" || test $? -eq 1
echo "test" | outmatch 2>&1 || test $? -eq 2
```

## Quiet Mode

Use `-q` or `--quiet` for exit code only:

```bash
output=$(echo "hello" | outmatch --quiet "world" 2>&1) || true
test -z "$output"

output=$(echo "hello" | outmatch -q "world" 2>&1) || true
test -z "$output"

(echo "hello" | outmatch -q "world" 2>&1 || true) | outmatch ""
```

## Color Control

```bash
echo "hello" | outmatch --color never "world" 2>&1 | (! grep -q $'\033') || echo "no ansi codes"
echo "hello" | outmatch --color always "world" 2>&1 | outmatch --contains "FAIL"
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "FAIL"
```

## File-Based Expected Values

Use `-f` for expected values from files:

```bash
echo "test content" > /tmp/expected_test.txt
echo "test content" | outmatch -f /tmp/expected_test.txt
rm /tmp/expected_test.txt

echo "test" > /tmp/expected_test2.txt
echo "test" | outmatch --expected-file /tmp/expected_test2.txt
rm /tmp/expected_test2.txt

echo '{"id": 1}' > /tmp/expected_json.txt
echo '{"id": 1}' | outmatch --json -f /tmp/expected_json.txt
rm /tmp/expected_json.txt
```

Missing file returns error:

```bash
echo "test" | outmatch -f /nonexistent/path.txt 2>&1 | outmatch --contains "not found"
```

## Snapshot Updates

Use `--update` to write output to expected file:

```bash
rm -f /tmp/update_test.txt
echo "new content" | outmatch -f /tmp/update_test.txt --update
cat /tmp/update_test.txt | outmatch "new content"
rm /tmp/update_test.txt

echo "old content" > /tmp/update_test2.txt
echo "new content" | outmatch -f /tmp/update_test2.txt --update
cat /tmp/update_test2.txt | outmatch "new content"
rm /tmp/update_test2.txt
```

## Error Messages

```bash
echo "test" | outmatch --replace 'bad' "test" 2>&1 | outmatch --contains "REGEX=>REPL"
outmatch -f /nonexistent/file.txt 2>&1 < /dev/null | outmatch --contains "file not found"
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
echo "not json" | outmatch --json '{}' 2>&1 | outmatch --contains "not valid JSON"
echo '{}' | outmatch --json 'not json' 2>&1 | outmatch --contains "not valid JSON"
printf '{"a":1}\nnot json' | outmatch --jsonl '{"a":1}' 2>&1 | outmatch --contains "JSON parse error"
echo "test" | outmatch 2>&1 | outmatch --contains "expected"
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "expected"
echo "match" | outmatch "match" && echo "exit 0 works" | outmatch "exit 0 works"
```
