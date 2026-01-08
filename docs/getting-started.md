# Getting Started

## Installation

Add outmatch as a dev dependency:

```bash
uv add --group dev outmatch
```

Or install from source:

```bash
uv pip install -e path/to/outmatch
```

## First Example

Verify a command produces expected output:

```bash
echo "hello world" | outmatch "hello world"
```

If the output matches, the command exits with code 0. If it doesn't match, it exits with code 1 and prints a diff.

## Integration with mktestdocs

Use `outmatch` in your documentation examples:

````markdown
## Check Version

```bash
mycommand --version | outmatch --contains "1.0"
```

## Process Data

```bash
echo '{"input": "data"}' | mycommand process | outmatch --jsonl '{"output": "result"}'
```
````

When mktestdocs runs these bash blocks, the `outmatch` assertions verify the output.

## Next Steps

See [CLI Reference](cli/reference.md) for all available options.
