# mustmatch

`mustmatch` provides executable documentation tools for command-line projects. It asserts CLI output in shell pipelines, runs Markdown examples as documentation tests, and supports documentation-first named runs where commands and expected output are separate readable blocks. The Rust core handles parsing, normalization, and comparison while Python keeps runtime orchestration.

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

Markdown documents can be run directly with `mustmatch test` or collected by pytest. Prefer documentation-first named runs: show the command a user would type, then show the expected output separately.

````markdown
```bash run id=version-json
mytool --json version
```

```json expect=version-json contains
{
  "name": "mytool"
}
```
````

Later commands can reuse JSON fields from earlier runs without visible `jq`, Python one-liners, or temporary files:

````markdown
```bash run id=detail uses=version-json
mytool get {{version-json.name}}
```
````

Tables can also drive per-row Python checks with `each_row` when Python is the clearest way to express fixture logic.

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

Run docs directly:

```bash
uv sync --extra dev --reinstall-package mustmatch
uv run mustmatch test docs/ -v
```

Or collect them through pytest when a project already uses pytest:

```bash
uv run python -m pytest docs/ -v
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
12. `docs/12-named-runs.md`
13. `docs/13-standalone-doc-runner.md`

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
