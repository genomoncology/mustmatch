# Output Options Tests

Tests for output formatting options.

## Quiet mode suppresses output

```bash
output=$(echo "hello" | outmatch --quiet "world" 2>&1) || true
test -z "$output"
```

## Quiet short flag

```bash
output=$(echo "hello" | outmatch -q "world" 2>&1) || true
test -z "$output"
```

## Color never

```bash
echo "hello" | outmatch --color never "world" 2>&1 | \
    (! grep -q $'\033') || echo "no ansi codes"
```

## Color always

When color is always, ANSI codes should be present in error output:

```bash
echo "hello" | outmatch --color always "world" 2>&1 | outmatch --contains "FAIL"
```

## Error shows FAIL prefix

```bash
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "FAIL"
```

## Exit code 0 on match

```bash
echo "hello" | outmatch "hello"
test $? -eq 0
```

## Exit code 1 on mismatch

```bash
echo "hello" | outmatch "world" || test $? -eq 1
```

## Exit code 2 on error

Missing expected argument:

```bash
echo "test" | outmatch 2>&1 || test $? -eq 2
```
