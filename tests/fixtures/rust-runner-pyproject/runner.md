# Pyproject Fallback Fixture

This fixture has no `mustmatch.toml`. It keeps the existing `pyproject.toml` context shape covered while the Rust runner moves new projects toward language-neutral config.

## Pyproject contexts still work

A context from `[tool.mustmatch.contexts]` prepares the temporary working directory and environment for a named run.

```bash run id=pyproject-context context=fallback
cat fallback.txt
env | grep '^FALLBACK_VALUE='
```

```text expect=pyproject-context contains
fallback=ready
FALLBACK_VALUE=pyproject
```
