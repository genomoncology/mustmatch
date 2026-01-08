# Exact Match Tests

Tests for exact string matching (default mode).

## Basic exact match

```bash
echo "hello world" | expect "hello world"
```

## Trailing newline normalization

Output with trailing newline should match expected without:

```bash
printf "hello world\n" | expect "hello world"
```

## Expected with trailing newline

Expected with trailing newline should match output without:

```bash
printf "hello world" | expect "hello world
"
```

## Multi-line exact match

```bash
printf "line one\nline two" | expect "line one
line two"
```

## Empty string match

```bash
printf "" | expect ""
```

## Unicode content

```bash
printf "Hello 世界 🌍" | expect "Hello 世界 🌍"
```

## Special characters

```bash
printf '{"key": "value"}' | expect '{"key": "value"}'
```

## Mismatch returns exit code 1

```bash
echo "hello" | expect "world" || test $? -eq 1
```

## Large output

```bash
python3 -c "print('x' * 1000)" | expect "$(python3 -c "print('x' * 1000)")"
```
