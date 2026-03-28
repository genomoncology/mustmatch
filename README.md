# mustmatch

`mustmatch` provides two tightly coupled capabilities for executable documentation workflows. It asserts CLI output in shell pipelines, and it executes Markdown `bash`/`python` fences as pytest tests. The Rust core handles parsing, normalization, and comparison while Python keeps runtime orchestration.

## Install

Use a normal Python virtual environment and install with pip. This snippet is documentation-only and intentionally skipped during executable doc runs.

```bash skip
pip install mustmatch
```

## CLI Assertions

Pipe command output into `mustmatch` and compare against one expected value.

```bash
echo "hello" | mustmatch "hello"
echo "hello world" | mustmatch like "world"
echo "v1.2.3" | mustmatch "/^v[0-9]+[.][0-9]+[.][0-9]+$/"
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

## Executable Markdown

Markdown documents become test files under pytest collection. Tables can drive per-row Python checks with `each_row`.

````markdown
# Math Behavior

## Double Values

| input | output |
|-------|--------|
| 2     | 4      |

```python each_row
doubled = row.input * 2
result = {"input": row.input, "output": doubled}
row_label = f"row-{row_index}"
```
````

Run docs as tests:

```bash
python -m pytest docs/ -v
```

## Quality Checks

Use `mustmatch verify-matrix` to confirm proof-matrix references stay inside the repo, and `mustmatch lint` to lint markdown specs without executing their fences.

- `mustmatch verify-matrix .march/design-final.md --repo-root .`
- `mustmatch lint docs/02-cli-assertions.md`

## Documentation Map

The executable specification is in `docs/`:

1. `docs/01-overview.md`
2. `docs/02-cli-assertions.md`
3. `docs/03-executable-documents.md`
4. `docs/04-fixtures-and-tables.md`
5. `docs/05-directives.md`
6. `docs/06-comparison-modes.md`
7. `docs/07-normalization.md`
8. `docs/08-configuration.md`
9. `docs/09-examples.md`
10. `docs/10-verify-matrix.md`
11. `docs/11-lint.md`

## CLI Bench Plan

Benchmark commands are tracked in `bench/clibench-commands.txt` so Python and Rust paths can be compared with the same tag set.

```bash
# Python baseline
CLIBENCH_PROJECT=mustmatch-cli uv run --script /home/ian/workspace/.codex/skills/clibench/clibench.py batch bench/clibench-commands.txt

# Compare prefixes
CLIBENCH_PROJECT=mustmatch-cli uv run --script /home/ian/workspace/.codex/skills/clibench/clibench.py compare python rust
```

## License

MIT
