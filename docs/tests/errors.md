# Error Handling

Common errors and how to debug them.

All errors return exit code 2 with a descriptive message on stderr. Mismatches return exit code 1.

## Invalid replace syntax

The `--replace` pattern requires `REGEX=>REPLACEMENT`:

```bash
echo "test" | outmatch --replace 'bad' "test" 2>&1 | outmatch --contains "REGEX=>REPL"
```

## Missing expected file

```bash
outmatch -f /nonexistent/file.txt 2>&1 < /dev/null | outmatch --contains "file not found"
```

## Invalid regex pattern

```bash
echo "test" | outmatch --regex '[invalid' 2>&1 | outmatch --contains "Invalid regex"
```

## Invalid JSON in input

```bash
echo "not json" | outmatch --json '{}' 2>&1 | outmatch --contains "not valid JSON"
```

## Invalid JSON in expected

```bash
echo '{}' | outmatch --json 'not json' 2>&1 | outmatch --contains "not valid JSON"
```

## JSONL parse error

```bash
printf '{"a":1}\nnot json' | outmatch --jsonl '{"a":1}' 2>&1 | outmatch --contains "JSON parse error"
```

## Missing expected value

```bash
echo "test" | outmatch 2>&1 | outmatch --contains "expected"
```

## Mismatch output

Mismatches show a helpful diff:

```bash
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "expected"
```

## Quiet mode suppresses all output

```bash
(echo "hello" | outmatch -q "world" 2>&1 || true) | outmatch ""
```

## Chaining commands

Exit codes work correctly for shell logic:

```bash
echo "match" | outmatch "match" && echo "exit 0 works" | outmatch "exit 0 works"
```
