# Configuration

mustmatch supports lightweight configuration through `pyproject.toml` and pytest options. Configuration should keep docs readable while avoiding hidden behavior. This file validates core public helpers used by plugin configuration paths.

## Tool Configuration

`[tool.mustmatch]` supports `auto_imports` for Python block namespaces. Keep imports explicit and minimal so readers can still understand examples quickly.

```toml
[tool.mustmatch]
auto_imports = ["math"]
```

## Public Core API

The Rust-backed public helpers are importable from `mustmatch._core`. These checks validate mode detection and table coercion behavior.

```python
from mustmatch._core import build_table_rows, detect_mode
headers, rows = build_table_rows(["value", "str:raw"], [["42", "42"]])
assert rows[0]["value"] == 42
assert rows[0]["raw"] == "42"
assert detect_mode('/^a$/') == "regex"
```
