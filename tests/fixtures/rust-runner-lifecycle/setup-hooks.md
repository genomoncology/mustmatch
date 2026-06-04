# Lifecycle Setup Fixture

This fixture shows that runner scopes can prepare ordinary files before documented commands run. The commands read suite, file, and context setup sentinels without embedding setup plumbing in the Markdown.

## Suite setup runs before document blocks

The suite setup hook runs before the first document block, so a normal command can read suite state from the fixture root.

```bash
cat suite-setup.txt | mustmatch like "suite=ready"
```

## File setup runs before document blocks

The file setup hook runs before blocks in this Markdown document, alongside the surrounding suite setup.

```bash
cat file-setup.txt | mustmatch like "file=ready"
```

## Context setup remains visible

Context setup still prepares context-local state before a context-backed command runs.

```bash context=ephemeral
cat context-setup.txt | mustmatch like "context=ready"
```
