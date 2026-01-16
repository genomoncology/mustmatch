# Bash Execution

Tests for bash code execution.

## Simple command

```python
from mustmatch.services.runner import run_bash

result = run_bash('echo "hello"')
assert result.exit_code == 0
assert "hello" in result.stdout
```

## Capture stderr

```python
from mustmatch.services.runner import run_bash

result = run_bash('echo "error" >&2')
assert result.exit_code == 0
assert "error" in result.stderr
```

## Non-zero exit code

```python
from mustmatch.services.runner import run_bash

result = run_bash('exit 42')
assert result.exit_code == 42
```

## Multiline script

```python
from mustmatch.services.runner import run_bash

script = '''
x=1
y=2
echo $((x + y))
'''
result = run_bash(script)
assert result.exit_code == 0
assert "3" in result.stdout
```

## Duration tracking

```python
from mustmatch.services.runner import run_bash

result = run_bash('sleep 0.1')
assert result.duration >= 0.1
```

## Timeout handling

```python
from mustmatch.services.runner import run_bash

result = run_bash('sleep 10', timeout=0.1)
assert result.exit_code == -1
assert result.exception is not None
```
