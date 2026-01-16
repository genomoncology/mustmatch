# Public API Tests

Tests for the mustmatch public API.

## check_md_file function

````python
from pathlib import Path
from mustmatch import check_md_file

# Create a temporary test file with bash
test_file = Path("/tmp/test_api.md")
content = "# Test\n\n```bash\necho hello\n```\n"
test_file.write_text(content)

# Test the file
result = check_md_file(test_file)
assert result == True

# Clean up
test_file.unlink()
````

## check_md_file with Python blocks

````python
from pathlib import Path
from mustmatch import check_md_file

# Create a test file with Python
test_file = Path("/tmp/test_python.md")
content = "# Test\n\n```python\nx = 1 + 1\nassert x == 2\n```\n"
test_file.write_text(content)

result = check_md_file(test_file, lang="python")
assert result == True

test_file.unlink()
````

## check_md_file with memory mode

````python
from pathlib import Path
from mustmatch import check_md_file

# Create a test file with shared state
test_file = Path("/tmp/test_memory.md")
content = "# Test\n\n```python\nx = 42\n```\n\n```python\nassert x == 42\n```\n"
test_file.write_text(content)

result = check_md_file(test_file, lang="python", memory=True)
assert result == True

test_file.unlink()
````

## check_md_file returns False on failure

````python
from pathlib import Path
from mustmatch import check_md_file

# Create a failing test file
test_file = Path("/tmp/test_fail.md")
content = "# Test\n\n```bash\nexit 1\n```\n"
test_file.write_text(content)

result = check_md_file(test_file, lang="bash")
assert result == False

test_file.unlink()
````

## check_md_file with no matching blocks

```python
from pathlib import Path
from mustmatch import check_md_file

# Create a file with no executable blocks
test_file = Path("/tmp/test_empty.md")
test_file.write_text("# Test\n\nJust some text, no code blocks.\n")

result = check_md_file(test_file)
assert result == True  # No blocks to fail

test_file.unlink()
```

## Module exports

```python
from mustmatch import (
    __version__,
    main,
    check_md_file,
    compare,
    normalize,
    parse_markdown,
    run_bash,
    run_python,
    CompareMode,
    CompareResult,
    NormalizeOptions,
    Block,
    Table,
    ParseResult,
    RunResult,
)

# Verify they're all accessible
assert __version__ is not None
assert callable(main)
assert callable(check_md_file)
assert callable(compare)
assert callable(normalize)
assert callable(parse_markdown)
assert callable(run_bash)
assert callable(run_python)
```
