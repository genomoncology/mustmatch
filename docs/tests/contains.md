# Contains Mode Tests

Tests for substring matching with `--contains`.

## Basic contains

```bash
echo "hello world" | expect --contains "world"
```

## Contains at start

```bash
echo "hello world" | expect --contains "hello"
```

## Contains in middle

```bash
echo "the quick brown fox" | expect --contains "quick brown"
```

## Multi-line contains

```bash
printf "line one\nline two\nline three" | expect --contains "line two"
```

## Case sensitive by default

Contains should be case-sensitive (this should fail):

```bash
echo "Hello World" | expect --contains "hello" || test $? -eq 1
```

## Missing substring fails

```bash
echo "hello world" | expect --contains "goodbye" || test $? -eq 1
```

## Empty actual with non-empty expected fails

```bash
printf "" | expect --contains "something" || test $? -eq 1
```

## Whitespace handling

Leading/trailing whitespace in expected is stripped:

```bash
echo "hello world" | expect --contains "  world  "
```
