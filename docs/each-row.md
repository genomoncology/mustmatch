# Row Directives

These directives reduce repeated boilerplate in table-driven specs. They let documentation focus on behavior while mustmatch handles iteration, setup, and common assertions.

## each_row Auto Assertions

`each_row` runs the block once per table row. When no explicit `assert` appears and `result` is defined, mustmatch compares matching columns automatically.

| input | expected |
|-------|----------|
| 2     | 4        |
| 3     | 6        |

```python each_row
from types import SimpleNamespace
result = SimpleNamespace(input=row.input, expected=row.input * 2)
```

## each_row With Explicit Assertions

If explicit asserts exist in the block, automatic result-column assertions are skipped.

| input | expected |
|-------|----------|
| 5     | 15       |
| 7     | 21       |

```python each_row
assert row.input * 3 == row.expected
```

## setup

`setup` blocks run before later executable blocks in the same section context.

```python setup
multiplier = 5
```

| value | product |
|-------|---------|
| 1     | 5       |
| 4     | 20      |

```python each_row
from types import SimpleNamespace
result = SimpleNamespace(value=row.value, product=row.value * multiplier)
```

## expect_error

Use `expect_error` to declare expected failure behavior inline.

```python expect_error="file not found"
raise RuntimeError("file not found in fixture directory")
```

## perf

Use `perf` with a literal threshold for small smoke checks.

```python perf=1.0
total = sum(range(20000))
assert total > 0
```

Use `perf` with `each_row` for table-driven limits.

| max_seconds | label  |
|-------------|--------|
| 1.0         | smoke  |

```python each_row perf=max_seconds
assert row.label == "smoke"
result = {"label": row.label, "max_seconds": row.max_seconds}
```
