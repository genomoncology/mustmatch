# mustmatch

`mustmatch` does two things:

1. CLI assertion tool for command output
2. Pytest plugin for executable Markdown documentation

## Install

```bash
pip install mustmatch
```

## Side 1: CLI Assertions

Use `mustmatch` in pipelines to verify output.

```bash
echo "hello" | mustmatch "hello"
echo "hello world" | mustmatch like "world"
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

## Side 2: Executable Markdown

Write documentation in Markdown and run it as pytest.

````markdown
# Math Behavior

## Double Values

| input | output |
|-------|--------|
| 2     | 4      |

```python each_row
from types import SimpleNamespace
result = SimpleNamespace(input=row.input, output=row.input * 2)
```
````

Run docs as tests:

```bash
pytest docs/ -v
```

## CLI Reference

```text
Usage:
    command | mustmatch [not] [like] EXPECTED

Options:
    -i, --ignore-case    Case-insensitive
    -q, --quiet          Suppress mismatch output
    --version            Show version
    -h, --help           Show help
```

## Documentation

- `docs/index.md` - learning path
- `docs/quick-start.md` - CLI quick start
- `docs/comparison-modes.md` - matching modes
- `docs/writing-test-documents.md` - executable Markdown walkthrough
- `docs/fixture.md` - `md` fixture and table APIs
- `docs/each-row.md` - `each_row`, `setup`, `expect_error`, `perf`
- `docs/conventions.md` - writing conventions

## License

MIT
