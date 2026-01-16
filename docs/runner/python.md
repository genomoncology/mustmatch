# Python Execution

Tests for Python code execution.

## Simple expression

```python
from mustmatch.services.runner import run_python

result = run_python('print("hello")')
assert result.exit_code == 0
assert "hello" in result.stdout
```

## Capture stdout

```python
from mustmatch.services.runner import run_python

code = '''
for i in range(3):
    print(i)
'''
result = run_python(code)
assert result.exit_code == 0
assert "0" in result.stdout
assert "1" in result.stdout
assert "2" in result.stdout
```

## Assertion error

```python
from mustmatch.services.runner import run_python

result = run_python('assert False, "test failure"')
assert result.exit_code == 1
assert "test failure" in result.stderr or result.exception is not None
```

## Runtime error

```python
from mustmatch.services.runner import run_python

result = run_python('raise ValueError("oops")')
assert result.exit_code == 1
assert "ValueError" in result.stderr
```

## Shared namespace

```python
from mustmatch.services.runner import run_python

namespace = {"__builtins__": __builtins__}

# First execution defines variable
run_python('x = 42', globals_dict=namespace)

# Second execution can access it
result = run_python('print(x)', globals_dict=namespace)
assert "42" in result.stdout
```

## Namespace with table injection

```python
from mustmatch.services.runner import create_python_namespace, run_python

table_data = [
    {"name": "Alice", "age": "30"},
    {"name": "Bob", "age": "25"},
]
namespace = create_python_namespace(table=table_data)

code = '''
for row in table:
    print(f"{row['name']} is {row['age']}")
'''
result = run_python(code, globals_dict=namespace)
assert result.exit_code == 0
assert "Alice is 30" in result.stdout
assert "Bob is 25" in result.stdout
```

## Duration tracking

```python
import time
from mustmatch.services.runner import run_python

result = run_python('import time; time.sleep(0.1)')
assert result.duration >= 0.1
```
