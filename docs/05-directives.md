# Directives

Directives add behavior to code fences without extra framework code. They are declared in the fence info string and parsed alongside language tags. This file covers `setup`, `expect_error`, and `timeout`.

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
