# CLI Exec Tests

Tests for the mustmatch exec subcommand.

## Exit code check success

```bash
mustmatch exec --exit-code 0 -- echo hello
```

## Exit code check failure

```python
import subprocess
result = subprocess.run(
    ['mustmatch', 'exec', '--exit-code', '0', '--', 'false'],
    capture_output=True
)
assert result.returncode == 1, f"Expected 1, got {result.returncode}"
```

## Stdout exact match

```bash
mustmatch exec --stdout "hello" -- echo hello
```

## Stdout contains with like

```bash
mustmatch exec --stdout-like "hello" -- echo "hello world"
```

## Stdout not contains

```bash
mustmatch exec --stdout-not-like "error" -- echo "success"
```

## Missing assertion exits with code 2

```python
import subprocess
result = subprocess.run(
    ['mustmatch', 'exec', '--', 'echo', 'hello'],
    capture_output=True
)
assert result.returncode == 2, f"Expected 2, got {result.returncode}"
```

## Missing command exits with error

```python
import subprocess
result = subprocess.run(
    ['mustmatch', 'exec', '--exit-code', '0'],
    capture_output=True
)
# Typer returns 1 for missing required arguments
assert result.returncode != 0, f"Expected non-zero, got {result.returncode}"
```
