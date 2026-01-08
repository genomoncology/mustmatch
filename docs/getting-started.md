# Getting Started

## Installation

Add doctest-expect as a dev dependency:

```bash
uv add --group dev doctest-expect
```

Or install from source:

```bash
uv pip install -e path/to/doctest-expect
```

## First Example

Verify a command produces expected output:

```bash
echo "hello world" | expect "hello world"
```

If the output matches, the command exits with code 0. If it doesn't match, it exits with code 1 and prints a diff.

## Integration with mktestdocs

Use `expect` in your documentation examples:

````markdown
## Check Version

```bash
mycommand --version | expect --contains "1.0"
```

## Process Data

```bash
echo '{"input": "data"}' | mycommand process | expect --jsonl '{"output": "result"}'
```
````

When mktestdocs runs these bash blocks, the `expect` assertions verify the output.

## Next Steps

See [CLI Reference](cli/reference.md) for all available options.
