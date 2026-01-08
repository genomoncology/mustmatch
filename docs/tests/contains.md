# Contains Mode Tests

Tests for substring matching with `--contains`.

## Basic contains

```bash
echo "hello world" | outmatch --contains "world"
```

## Contains at start

```bash
echo "hello world" | outmatch --contains "hello"
```

## Contains in middle

```bash
echo "the quick brown fox" | outmatch --contains "quick brown"
```

## Multi-line contains

```bash
printf "line one\nline two\nline three" | outmatch --contains "line two"
```

## Case sensitive by default

Contains should be case-sensitive (this should fail):

```bash
echo "Hello World" | outmatch --contains "hello" || test $? -eq 1
```

## Missing substring fails

```bash
echo "hello world" | outmatch --contains "goodbye" || test $? -eq 1
```

## Empty actual with non-empty expected fails

```bash
printf "" | outmatch --contains "something" || test $? -eq 1
```

## Whitespace handling

Leading/trailing whitespace in expected is stripped:

```bash
echo "hello world" | outmatch --contains "  world  "
```
