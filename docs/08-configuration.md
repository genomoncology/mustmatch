# Configuration

mustmatch supports lightweight configuration through `pyproject.toml` and pytest options. Configuration should keep docs readable while avoiding hidden behavior. This file validates core public helpers used by plugin configuration paths.

## Tool Configuration

`[tool.mustmatch]` supports `auto_imports` for Python block namespaces. Keep imports explicit and minimal so readers can still understand examples quickly.

```toml
[tool.mustmatch]
auto_imports = ["math"]
```

## Repo Bootstrap

Installed-package pytest usage still relies on the `pytest11` entry point. This
checkout also bootstraps the plugin from source so contributor runs collect
Markdown tests even when a generated console script has gone stale.

Repo-local pytest config blocks the `mustmatch` entry-point alias and then
preloads `mustmatch.pytest_plugin` from `src`. That avoids double registration
when entry-point metadata is visible while keeping checkout-local runs
independent from editable-install metadata visibility.

```bash
uv run pytest --trace-config --co -q docs/01-overview.md 2>&1 | mustmatch like "mustmatch.pytest_plugin"
```

This fallback path should still work when the generated `pytest` console script
has a stale shebang. The check below rewrites the checkout-local script, runs
pytest through `uv`, and restores the original script on shell exit.

```bash
repo_root="$(cd .. && pwd)"
pytest_script="$repo_root/.venv/bin/pytest"
backup="$(mktemp)"
cp "$pytest_script" "$backup"
trap 'cp "$backup" "$pytest_script"; rm -f "$backup"' EXIT
{
  printf '#!/definitely/missing/python\n'
  tail -n +2 "$backup"
} > "$pytest_script"
cd "$repo_root/docs"
uv run pytest 01-overview.md -q | mustmatch like "1 passed"
```

Repo-owned automation should also avoid direct pytest and coverage console
scripts. These commands check the tracked automation and contributor docs for
the old forms that were replaced in this ticket.

```bash
repo_root="$(cd .. && pwd)"
if rg -n "uv run pytest|uv run coverage run|uv run coverage combine|uv run coverage report|uv run coverage html|uv run coverage xml" \
  "$repo_root/Makefile" \
  "$repo_root/.github/workflows/test.yml" \
  "$repo_root/README.md" \
  "$repo_root/docs/01-overview.md" \
  "$repo_root/CLAUDE.md"; then
  echo "found console-script invocation"
else
  echo "module-only automation"
fi | mustmatch "module-only automation"
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

## Pipe-Only Bash Execution

Bash blocks only execute when they pipe into `mustmatch`. This keeps executable
assertions explicit and prevents non-assertion shell snippets from running.

```bash
echo "run through mustmatch" | mustmatch like "run through mustmatch"
```

This sentinel block mentions `mustmatch` but has no pipe, so it should be
collected as markdown content only and not executed:

```bash
echo "mustmatch appears here without a pipe"
```
