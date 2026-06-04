# Lifecycle hooks

Setup and teardown commands can run outside the document, at three scopes:

- **suite** — once, before the first file and after the last (across the whole
  `mustmatch test` run);
- **file** — around each document;
- **context** — when a context is first used and after its last use.

Teardown is guaranteed: it runs when the runner exits and even when setup or a
block fails. This directory's `mustmatch.toml` writes a sentinel at each scope.

```toml
[suite]
setup = ["printf 'suite=ready\n' > {root}/suite-setup.txt"]
teardown = ["rm -f {root}/suite-setup.txt"]

[file]
setup = ["printf 'file=ready\n' > {root}/file-setup.txt"]
teardown = ["rm -f {root}/file-setup.txt"]

[contexts.cleanup]
cwd = "."
setup = ["printf 'context=ready\n' > {root}/context-setup.txt"]
teardown = ["rm -f {root}/context-setup.txt {root}/context-body.txt"]
```

## Suite and file setup run first

The suite and file setup sentinels are already in place before the first block.

```bash
cat suite-setup.txt | mustmatch like "suite=ready"
cat file-setup.txt  | mustmatch like "file=ready"
```

## Context teardown after last use

The `cleanup` context's setup wrote `context-setup.txt`; this block also leaves a
`context-body.txt`. Because this is the context's last use, its teardown runs
before the next block.

```bash context=cleanup
printf 'body\n' > context-body.txt
cat context-setup.txt | mustmatch like "context=ready"
```

The following block uses no context, so it runs after the teardown — and the
body file is gone.

```bash
ls context-body.txt 2>/dev/null | mustmatch not like "context-body.txt"
```

## Teardown always runs

Suite and file teardown run after the run completes, removing their sentinels;
the teardown-on-failure guarantee (setup or a block failing still triggers
teardown) is covered by the runner's unit tests.
