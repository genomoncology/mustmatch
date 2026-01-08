# File Operations Tests

Tests for file-based expected values and update mode.

## Expected from file

```bash
echo "test content" > /tmp/expected_test.txt
echo "test content" | expect -f /tmp/expected_test.txt
rm /tmp/expected_test.txt
```

## Long flag

```bash
echo "test" > /tmp/expected_test2.txt
echo "test" | expect --expected-file /tmp/expected_test2.txt
rm /tmp/expected_test2.txt
```

## File not found

```bash
echo "test" | expect -f /nonexistent/path.txt 2>&1 | expect --contains "not found"
```

## File with modes

```bash
echo '{"id": 1}' > /tmp/expected_json.txt
echo '{"id": 1}' | expect --json -f /tmp/expected_json.txt
rm /tmp/expected_json.txt
```

## Update mode creates file

```bash
rm -f /tmp/update_test.txt
echo "new content" | expect -f /tmp/update_test.txt --update
cat /tmp/update_test.txt | expect "new content"
rm /tmp/update_test.txt
```

## Update mode overwrites file

```bash
echo "old content" > /tmp/update_test2.txt
echo "new content" | expect -f /tmp/update_test2.txt --update
cat /tmp/update_test2.txt | expect "new content"
rm /tmp/update_test2.txt
```
