# Output Options

Control how outmatch reports results with output formatting flags.

## How do I suppress all output?

Use `--quiet` or `-q` to get only the exit code:

```bash
output=$(echo "hello" | outmatch --quiet "world" 2>&1) || true
test -z "$output"
```

```bash
output=$(echo "hello" | outmatch -q "world" 2>&1) || true
test -z "$output"
```

Useful in scripts where you only need pass/fail logic.

## How do I control colored output?

Use `--color` with `never`, `always`, or `auto`:

```bash
echo "hello" | outmatch --color never "world" 2>&1 | \
    (! grep -q $'\033') || echo "no ansi codes"
```

```bash
echo "hello" | outmatch --color always "world" 2>&1 | outmatch --contains "FAIL"
```

Default is `auto`, which detects if output is a terminal.

## What do the exit codes mean?

| Code | Meaning |
|------|---------|
| 0 | Match |
| 1 | Mismatch |
| 2 | Error (invalid arguments, missing file, bad regex) |

```bash
echo "hello" | outmatch "hello"
test $? -eq 0
```

```bash
echo "hello" | outmatch "world" || test $? -eq 1
```

```bash
echo "test" | outmatch 2>&1 || test $? -eq 2
```

## What does mismatch output look like?

A FAIL prefix with details about the difference:

```bash
echo "actual" | outmatch "expected" 2>&1 | outmatch --contains "FAIL"
```
