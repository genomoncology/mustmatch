# File Operations

Load expected values from files and update them automatically with `--expected-file` and `--update`.

For longer expected output or snapshot testing, storing expected values in files is cleaner than inline strings. The update mode makes it easy to regenerate snapshots when output legitimately changes.

## How do I load expected values from a file?

Use `-f` or `--expected-file`:

```bash
echo "test content" > /tmp/expected_test.txt
echo "test content" | outmatch -f /tmp/expected_test.txt
rm /tmp/expected_test.txt
```

```bash
echo "test" > /tmp/expected_test2.txt
echo "test" | outmatch --expected-file /tmp/expected_test2.txt
rm /tmp/expected_test2.txt
```

## What happens if the file doesn't exist?

Exit code 2 with an error message:

```bash
echo "test" | outmatch -f /nonexistent/path.txt 2>&1 | outmatch --contains "not found"
```

## Can I use file mode with other comparison modes?

Yes. Combine with any mode flag:

```bash
echo '{"id": 1}' > /tmp/expected_json.txt
echo '{"id": 1}' | outmatch --json -f /tmp/expected_json.txt
rm /tmp/expected_json.txt
```

## How do I update expected files automatically?

Use `--update` to write current output to the expected file:

```bash
rm -f /tmp/update_test.txt
echo "new content" | outmatch -f /tmp/update_test.txt --update
cat /tmp/update_test.txt | outmatch "new content"
rm /tmp/update_test.txt
```

Existing files are overwritten:

```bash
echo "old content" > /tmp/update_test2.txt
echo "new content" | outmatch -f /tmp/update_test2.txt --update
cat /tmp/update_test2.txt | outmatch "new content"
rm /tmp/update_test2.txt
```

Use this workflow: run tests normally, review failures, then re-run with `--update` to accept new expected values.
