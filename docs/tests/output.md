# Output Options Tests

Tests for output formatting options.

## Quiet mode suppresses output

```bash
output=$(echo "hello" | expect --quiet "world" 2>&1) || true
test -z "$output"
```

## Quiet short flag

```bash
output=$(echo "hello" | expect -q "world" 2>&1) || true
test -z "$output"
```

## Color never

```bash
echo "hello" | expect --color never "world" 2>&1 | \
    (! grep -q $'\033') || echo "no ansi codes"
```

## Color always

When color is always, ANSI codes should be present in error output:

```bash
echo "hello" | expect --color always "world" 2>&1 | expect --contains "FAIL"
```

## Error shows FAIL prefix

```bash
echo "actual" | expect "expected" 2>&1 | expect --contains "FAIL"
```

## Exit code 0 on match

```bash
echo "hello" | expect "hello"
test $? -eq 0
```

## Exit code 1 on mismatch

```bash
echo "hello" | expect "world" || test $? -eq 1
```

## Exit code 2 on error

Missing expected argument:

```bash
echo "test" | expect 2>&1 || test $? -eq 2
```
