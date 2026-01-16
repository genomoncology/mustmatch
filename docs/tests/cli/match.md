# CLI Match Tests

Tests for the main mustmatch CLI match functionality.

## Exact match success

```bash
echo "hello" | mustmatch "hello"
```

## Exact match failure exits with code 1

```bash expect-exit=1
echo "hello" | mustmatch "world"
```

## Contains match with like

```bash
echo "hello world" | mustmatch like "hello"
```

## Contains match with like failure

```bash expect-exit=1
echo "hello world" | mustmatch like "foo"
```

## Negation with not

```bash
echo "success" | mustmatch not like "error"
```

## Negation failure

```bash expect-exit=1
echo "error occurred" | mustmatch not like "error"
```

## Case insensitive with -i

```bash
echo "HELLO" | mustmatch -i "hello"
```

## JSON auto-detection

```bash
echo '{"a": 1, "b": 2}' | mustmatch '{"b": 2, "a": 1}'
```

## JSON subset with like

```bash
echo '{"a": 1, "b": 2, "c": 3}' | mustmatch like '{"a": 1}'
```

## Regex auto-detection

```bash
echo "version 1.2.3" | mustmatch "/version \d+\.\d+\.\d+/"
```

## Quiet mode suppresses output

Test that -q suppresses error output:

```bash
output=$(echo "hello" | mustmatch -q "world" 2>&1 || true)
test -z "$output"
```

## Version flag

```bash
mustmatch --version | mustmatch like "mustmatch"
```

## Missing expected value exits with code 2

```bash expect-exit=2
echo "hello" | mustmatch
```
