# Pyproject Lifecycle Fixture

This fixture shows that lifecycle hooks declared under `[tool.mustmatch]` behave like hooks from `mustmatch.toml`. The commands read suite, file, and context setup sentinels from normal documented examples.

## Pyproject suite setup runs

The suite setup hook from `pyproject.toml` runs before the first document block.

```bash
cat suite-setup.txt | mustmatch-cli like "suite=pyproject"
```

## Pyproject file setup runs

The file setup hook from `pyproject.toml` runs before blocks in this Markdown document.

```bash
cat file-setup.txt | mustmatch-cli like "file=pyproject"
```

## Pyproject context setup runs

The context setup hook from `pyproject.toml` still prepares context-local state.

```bash context=ephemeral
cat context-setup.txt | mustmatch-cli like "context=pyproject"
```
