# Getting Started

Get mustmatch running in under a minute, then learn the patterns you'll use daily.

## Installation

```console
pip install mustmatch
```

Or with uv:
```console
uv add mustmatch
```

## Your First Assertion

Pipe command output to mustmatch with the expected value:

```bash
echo "hello world" | mustmatch "hello world"
```

No output means success (exit code 0). On mismatch, you get a diff and exit code 1.

## Choosing a Match Mode

### Exact match (default)

```bash
echo "hello world" | mustmatch "hello world"
```

### Contains (`like`)

Use `like` for substring matching:

```bash
echo "Usage: mustmatch [OPTIONS]" | mustmatch like "Usage:"
```

### Regex (auto-detected)

Wrap patterns in `/.../' for regex matching:

```bash
echo "completed in 42ms" | mustmatch "/completed in \d+ms/"
```

### JSON (auto-detected)

JSON is auto-detected from `{...}` or `[...]`:

```bash
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'
```

## Multi-line Output

Use literal newlines in your expected value:

```bash
printf "line 1\nline 2\nline 3" | mustmatch "line 1
line 2
line 3"
```

Or test for substring:

```bash
ls --help | mustmatch like "list"
```

## Testing Your Documentation

Run all bash code blocks in your docs as tests:

```console
$ mustmatch test docs/
✓ 42 passed, 42 total
```

Skip blocks with HTML comments:

````markdown
<!-- mustmatch: skip -->
```bash
# This block won't run
```
````

## Next Steps

- [CLI Reference](cli.md) - All options, exit codes, errors
- [Test Runner](mdtest.md) - `mustmatch test` documentation
