# CLI Match Tests

Tests for the main mustmatch CLI match functionality.

## Exact match success

```bash
echo "hello" | mustmatch "hello"
```

## Exact match failure exits with code 1

```python
import subprocess
result = subprocess.run(
    ['bash', '-c', 'echo "hello" | mustmatch "world"'],
    capture_output=True
)
assert result.returncode == 1
```

## Contains match with like

```bash
echo "hello world" | mustmatch like "hello"
```

## Contains match with like failure

```python
import subprocess
result = subprocess.run(
    ['bash', '-c', 'echo "hello world" | mustmatch like "foo"'],
    capture_output=True
)
assert result.returncode == 1
```

## Negation with not

```bash
echo "success" | mustmatch not like "error"
```

## Negation failure

```python
import subprocess
result = subprocess.run(
    ['bash', '-c', 'echo "error occurred" | mustmatch not like "error"'],
    capture_output=True
)
assert result.returncode == 1
```

## Case insensitive with -i

```bash
echo "HELLO" | mustmatch -i "hello"
```

## JSON auto-detection

```bash
echo '{"a": 1, "b": 2}' | mustmatch '{"b": 2, "a": 1}'
```

## JSON subset with like

```bash
echo '{"a": 1, "b": 2, "c": 3}' | mustmatch like '{"a": 1}'
```

## Regex auto-detection

```bash
echo "version 1.2.3" | mustmatch "/version \d+\.\d+\.\d+/"
```

## Quiet mode suppresses output

```python
import subprocess
result = subprocess.run(
    ['bash', '-c', 'echo "hello" | mustmatch -q "world"'],
    capture_output=True,
    text=True
)
assert result.returncode == 1
assert result.stderr == ""
```

## Version flag

```bash
mustmatch --version | mustmatch like "mustmatch"
```

## Missing expected value exits with code 2

```python
import subprocess
result = subprocess.run(
    ['bash', '-c', 'echo "hello" | mustmatch'],
    capture_output=True
)
assert result.returncode == 2
```
