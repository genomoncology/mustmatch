# Output Options Tests

Tests for output formatting options.

## Quiet mode suppresses output

```bash
output=$(echo "hello" | outmatchall --quiet "world" 2>&1) || true
test -z "$output"
```

## Quiet short flag

```bash
output=$(echo "hello" | outmatchall -q "world" 2>&1) || true
test -z "$output"
```

## Color never

```bash
echo "hello" | outmatchall --color never "world" 2>&1 | \
    (! grep -q $'\033') || echo "no ansi codes"
```

## Color always

When color is always, ANSI codes should be present in error output:

```bash
echo "hello" | outmatchall --color always "world" 2>&1 | outmatchall --contains "FAIL"
```

## Error shows FAIL prefix

```bash
echo "actual" | outmatchall "expected" 2>&1 | outmatchall --contains "FAIL"
```

## Exit code 0 on match

```bash
echo "hello" | outmatchall "hello"
test $? -eq 0
```

## Exit code 1 on mismatch

```bash
echo "hello" | outmatchall "world" || test $? -eq 1
```

## Exit code 2 on error

Missing expected argument:

```bash
echo "test" | outmatchall 2>&1 || test $? -eq 2
```
