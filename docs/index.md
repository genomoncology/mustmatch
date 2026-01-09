# outmatch

CLI output assertion tool for documentation testing.

## What It Does

Verify command output matches expectations:

```bash
echo "hello" | outmatch "hello"
```

## Quick Examples

```bash
echo "hello world" | outmatch "hello world"
```

```bash
echo "version 2.0" | outmatch --contains "2.0"
```

```bash
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'
```

## Documentation

See [Getting Started](getting-started.md) for installation and usage.
