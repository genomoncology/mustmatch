# Exact Match Tests

Tests for exact string matching (default mode).

## Basic exact match

```bash
echo "hello world" | outmatch "hello world"
```

## Trailing newline normalization

Output with trailing newline should match expected without:

```bash
printf "hello world\n" | outmatch "hello world"
```

## Expected with trailing newline

Expected with trailing newline should match output without:

```bash
printf "hello world" | outmatch "hello world
"
```

## Multi-line exact match

```bash
printf "line one\nline two" | outmatch "line one
line two"
```

## Empty string match

```bash
printf "" | outmatch ""
```

## Unicode content

```bash
printf "Hello 世界 🌍" | outmatch "Hello 世界 🌍"
```

## Special characters

```bash
printf '{"key": "value"}' | outmatch '{"key": "value"}'
```

## Mismatch returns exit code 1

```bash
echo "hello" | outmatch "world" || test $? -eq 1
```

## Large output

```bash
python3 -c "print('x' * 1000)" | outmatch "$(python3 -c "print('x' * 1000)")"
```
