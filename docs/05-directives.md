# Directives

Directives add behavior to code fences without extra framework code. They are declared in the fence info string and parsed alongside language tags. This file covers `setup`, `expect_error`, `timeout`, table selection, and embedded `file=` fixture blocks.

## Setup

A `setup` block runs before later Python blocks in the same context. This supports shared helpers while keeping test code readable.

```python setup
base = 10
def scale(value):
    return base * value
```

```python
result = scale(3)
assert result == 30
assert base == 10
```

## Expected Errors

`expect_error` inverts success criteria for Python blocks. The block passes when execution fails and stderr includes the expected text.

```python expect_error="division by zero"
value = 1 / 0
value
```

## Timeout

`timeout=N` applies per block. Fast blocks still pass under timeout enforcement.

```python timeout=1
total = sum(range(1000))
assert total > 0
assert isinstance(total, int)
```

## Table Selection

Use `table=<name>` when multiple prior tables are in scope and you want a specific one.
Table names use the same normalization as `md.tables[...]` lookups.

### Shared Inputs

| text | expected |
|------|----------|
| BRAF mutation | BRAF |

### Alternate Inputs

| text | expected |
|------|----------|
| KRAS mutation | KRAS |

```python table=shared_inputs
assert len(scenarios) == 1
assert scenarios[0].text == "BRAF mutation"
assert scenarios[0].expected == "BRAF"
```

## Embedded File Fixtures

In the Rust documentation runner, `file=<relative/path>` on a fenced block writes that block's content into the consuming block's working directory. The file block is setup only: it is not executed, asserted, or reported as a PASS line.

````markdown
```json file=config.json
{"status":"active"}
```

```bash
cat config.json | mustmatch like '"status":"active"'
```
````

Paths must be relative and stay under the fixture cwd. Absolute paths, Windows drive or UNC prefixes, and `..` traversal are rejected. A `file=` block cannot also carry `run`, `mustmatch-run`, `expect`, `for`, `output`, or `mustmatch-output`.

File fixtures share the current H2 section's working directory. Row-scoped file blocks can use `each_row=<table>` and render bare `{{column}}` placeholders from the current row; context-backed blocks materialize files after the context cwd is resolved. See `docs/15-embedded-files.md` for the before/after pattern and row examples.
