# File Operations Tests

Tests for file-based expected values and update mode.

## Expected from file

```bash
echo "test content" > /tmp/expected_test.txt
echo "test content" | outmatch -f /tmp/expected_test.txt
rm /tmp/expected_test.txt
```

## Long flag

```bash
echo "test" > /tmp/expected_test2.txt
echo "test" | outmatch --expected-file /tmp/expected_test2.txt
rm /tmp/expected_test2.txt
```

## File not found

```bash
echo "test" | outmatch -f /nonexistent/path.txt 2>&1 | outmatch --contains "not found"
```

## File with modes

```bash
echo '{"id": 1}' > /tmp/expected_json.txt
echo '{"id": 1}' | outmatch --json -f /tmp/expected_json.txt
rm /tmp/expected_json.txt
```

## Update mode creates file

```bash
rm -f /tmp/update_test.txt
echo "new content" | outmatch -f /tmp/update_test.txt --update
cat /tmp/update_test.txt | outmatch "new content"
rm /tmp/update_test.txt
```

## Update mode overwrites file

```bash
echo "old content" > /tmp/update_test2.txt
echo "new content" | outmatch -f /tmp/update_test2.txt --update
cat /tmp/update_test2.txt | outmatch "new content"
rm /tmp/update_test2.txt
```
