# Exact Match Tests

Tests for exact string matching (default mode).

## Basic exact match

```bash
echo "hello world" | outmatchall "hello world"
```

## Trailing newline normalization

Output with trailing newline should match expected without:

```bash
printf "hello world\n" | outmatchall "hello world"
```

## Expected with trailing newline

Expected with trailing newline should match output without:

```bash
printf "hello world" | outmatchall "hello world
"
```

## Multi-line exact match

```bash
printf "line one\nline two" | outmatchall "line one
line two"
```

## Empty string match

```bash
printf "" | outmatchall ""
```

## Unicode content

```bash
printf "Hello 世界 🌍" | outmatchall "Hello 世界 🌍"
```

## Special characters

```bash
printf '{"key": "value"}' | outmatchall '{"key": "value"}'
```

## Mismatch returns exit code 1

```bash
echo "hello" | outmatchall "world" || test $? -eq 1
```

## Large output

```bash
python3 -c "print('x' * 1000)" | outmatchall "$(python3 -c "print('x' * 1000)")"
```
