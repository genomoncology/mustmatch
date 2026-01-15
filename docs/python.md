# Python Testing

mustmatch can test Python code blocks in markdown documentation, with optional state sharing between blocks.

## Overview

Python code blocks (` ```python ` or ` ```py `) are executed using Python's built-in `exec()`. This allows testing Python examples in your documentation to ensure they work correctly.

## Basic Usage

### CLI

<!-- mustmatch: skip -->
```bash
# Test only Python blocks
mustmatch test --lang python docs/

# Test both bash and Python blocks
mustmatch test --lang all docs/
```

### pytest

<!-- mustmatch: skip -->
```bash
# Test Python blocks
pytest docs/ --mustmatch-lang python

# Test all blocks (default)
pytest docs/ --mustmatch-lang all
```

## Memory Mode

By default, each Python block runs independently with its own fresh namespace. This means variables defined in one block are not available in subsequent blocks.

**Memory mode** allows blocks to share state, which is useful when your documentation builds concepts progressively:

### Without Memory Mode (default)

Each block runs independently:

````markdown
```python
x = 42
```

```python
# This fails! x is not defined in this block's namespace
print(x)
```
````

### With Memory Mode

Blocks share state within a file:

````markdown
```python
x = 42
```

```python
# This works! x persists from the previous block
print(x)  # Output: 42
```
````

Run with memory mode:

<!-- mustmatch: skip -->
```bash
# CLI
mustmatch test --lang python --memory docs/

# pytest
pytest docs/ --mustmatch-lang python --mustmatch-memory
```

## Memory Mode Use Cases

Memory mode is ideal for:

1. **Tutorials** where examples build on previous code
2. **API documentation** that demonstrates object lifecycle
3. **Step-by-step guides** where state accumulates

### Example: Class Tutorial

````markdown
# Calculator Tutorial

First, define a class:

```python
class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, n):
        self.result += n
        return self

calc = Calculator()
```

Then use it:

```python
calc.add(5).add(3)
assert calc.result == 8
```
````

Without `--memory`, the second block would fail because `calc` doesn't exist.

## Programmatic API

Use the `check_md_file` function to test markdown files programmatically:

<!-- mustmatch: skip -->
```python
from mustmatch import check_md_file

# Test Python blocks with memory mode
result = check_md_file(
    "docs/tutorial.md",
    lang="python",
    memory=True
)
assert result  # True if all blocks pass
```

## Error Handling

When a Python block fails, mustmatch shows:

1. **File and line number** where the block starts
2. **The code** that was executed
3. **Any output** produced before the error
4. **The full traceback**

Example error output:

```
  ✗ Block (line 15): Calculate result

    Code:
      result = undefined_variable + 1

    Error:
      NameError: name 'undefined_variable' is not defined
        File "docs/example.md:15", line 1, in <module>
          result = undefined_variable + 1

    docs/example.md:15-15
```

## Assertions in Python Blocks

Use standard Python assertions in your blocks:

<!-- mustmatch: skip -->
```python
# Simple assertions
x = 1 + 1
assert x == 2

# With messages
result = calculate()
assert result > 0, f"Expected positive result, got {result}"
```

## Output Capture

Output printed by Python blocks is captured but not shown unless there's an error. This keeps test output clean while still providing debugging information when needed.

```python
# This output is captured
print("Setting up...")
x = 42
print(f"x = {x}")
# Test passes silently
```

## Skip Directives

Use HTML comments to skip Python blocks:

````markdown
<!-- mustmatch: skip -->
```python
# This block won't be executed
import hypothetical_module
```
````

## Timeout

Set a timeout for slow Python blocks:

````markdown
<!-- mustmatch: timeout=60 -->
```python
# Allow up to 60 seconds
import time
time.sleep(5)  # Simulating slow operation
```
````

## Best Practices

### 1. Keep Blocks Independent When Possible

While memory mode is useful, independent blocks are easier to maintain:

<!-- mustmatch: skip -->
```python
# Good: Self-contained example
from mylib import process
result = process("data")
assert result["status"] == "ok"
```

### 2. Use Memory Mode for Progressive Examples

Memory mode shines for tutorials:

<!-- mustmatch: skip -->
```python
# Block 1: Setup
data = load_data()
```

<!-- mustmatch: skip -->
```python
# Block 2: Transform (needs data from Block 1)
processed = transform(data)
assert len(processed) > 0
```

### 3. Include Assertions

Always include assertions to verify the code works:

<!-- mustmatch: skip -->
```python
# Instead of just showing how to use the API...
result = my_function()

# ...assert on the expected behavior
result = my_function()
assert result is not None
assert "success" in result
```

### 4. Handle Imports Explicitly

Each block (without memory mode) has its own namespace, so imports must be repeated:

```python
# Block 1
import json
data = json.dumps({"key": "value"})
```

```python
# Block 2 (without memory mode)
import json  # Must import again!
parsed = json.loads('{"key": "value"}')
```

With memory mode, imports persist between blocks.

## Limitations

1. **No async support** - `async def` functions and `await` are not supported in blocks
2. **No input()** - Interactive input is not supported
3. **Memory per file** - Memory mode shares state within a single file, not across files
4. **Sequential execution** - Blocks run in document order (parallel execution disabled for Python)
