# Exact Matching

The default mode. Output must match the expected value character-for-character.

Use exact matching when your command produces predictable, stable output. Version strings, formatted data, configuration dumps - anything where consistency matters.

## How do I match output exactly?

Pipe command output to outmatch with the expected string:

```bash
echo "hello world" | outmatch "hello world"
```

Exit code 0 means match. Exit code 1 means mismatch with a diff showing what differed.

## Do I need to worry about trailing newlines?

No. outmatch normalizes trailing newlines automatically. These all match:

```bash
printf "hello world\n" | outmatch "hello world"
```

```bash
printf "hello world" | outmatch "hello world
"
```

This prevents the common frustration of tests failing due to invisible whitespace differences.

## Does it work with multi-line output?

Yes. For multi-line expected values, use literal newlines in your string:

```bash
printf "line one\nline two" | outmatch "line one
line two"
```

Each line must match exactly in order.

## What about unicode and special characters?

Full unicode support, including emoji:

```bash
printf "Hello 世界 🌍" | outmatch "Hello 世界 🌍"
```

JSON and other structured text works as expected:

```bash
printf '{"key": "value"}' | outmatch '{"key": "value"}'
```

## What happens when output doesn't match?

Exit code 1, plus a diff on stderr showing actual vs expected:

```bash
echo "hello" | outmatch "world" || test $? -eq 1
```

Use quiet mode (`-q`) to suppress the diff when you only need the exit code.

## Edge Cases

Empty output matches empty expected:

```bash
printf "" | outmatch ""
```

Large output works fine:

```bash
python3 -c "print('x' * 1000)" | outmatch "$(python3 -c "print('x' * 1000)")"
```
