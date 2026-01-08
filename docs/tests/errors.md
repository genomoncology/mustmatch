# Error Handling Tests

Tests for error conditions and edge cases.

## Invalid --replace syntax

Missing `=>` separator returns exit code 2:

```bash
echo "test" | outmatch --replace 'bad' "test" 2>&1 | outmatch --contains "REGEX=>REPL"
```

## File not found

Missing expected file returns exit code 2:

```bash
outmatch -f /nonexistent/file.txt 2>&1 < /dev/null | outmatch --contains "file not found"
```

## Invalid regex

Bad regex pattern returns exit code 2:

```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
```

## Invalid JSON in actual

Non-JSON input with --json mode fails:

```bash
echo "not json" | outmatch --json '{}' 2>&1 | outmatch --contains "not valid JSON"
```

## Invalid JSON in expected

Bad JSON in expected value fails:

```bash
echo '{}' | outmatch --json 'not json' 2>&1 | outmatch --contains "not valid JSON"
```

## JSONL parse error

Invalid JSONL input fails:

```bash
printf '{"a":1}\nnot json' | outmatch --jsonl '{"a":1}' 2>&1 | outmatch --contains "JSON parse error"
```

## Missing expected value

No expected value provided:

```bash
echo "test" | outmatch 2>&1 | outmatch --contains "expected"
```

## Mismatch shows diff

Mismatch outputs helpful diff:

```bash
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "expected"
```

## Quiet mode suppresses output

```bash
(echo "hello" | outmatch -q "world" 2>&1 || true) | outmatch ""
```

## Exit codes work correctly

```bash
echo "match" | outmatch "match" && echo "exit 0 works" | outmatch "exit 0 works"
```
