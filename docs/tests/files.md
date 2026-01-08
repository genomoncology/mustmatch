# File Operations Tests

Tests for file-based expected values and update mode.

## Expected from file

```bash
echo "test content" > /tmp/expected_test.txt
echo "test content" | outmatchall -f /tmp/expected_test.txt
rm /tmp/expected_test.txt
```

## Long flag

```bash
echo "test" > /tmp/expected_test2.txt
echo "test" | outmatchall --expected-file /tmp/expected_test2.txt
rm /tmp/expected_test2.txt
```

## File not found

```bash
echo "test" | outmatchall -f /nonexistent/path.txt 2>&1 | outmatchall --contains "not found"
```

## File with modes

```bash
echo '{"id": 1}' > /tmp/expected_json.txt
echo '{"id": 1}' | outmatchall --json -f /tmp/expected_json.txt
rm /tmp/expected_json.txt
```

## Update mode creates file

```bash
rm -f /tmp/update_test.txt
echo "new content" | outmatchall -f /tmp/update_test.txt --update
cat /tmp/update_test.txt | outmatchall "new content"
rm /tmp/update_test.txt
```

## Update mode overwrites file

```bash
echo "old content" > /tmp/update_test2.txt
echo "new content" | outmatchall -f /tmp/update_test2.txt --update
cat /tmp/update_test2.txt | outmatchall "new content"
rm /tmp/update_test2.txt
```
