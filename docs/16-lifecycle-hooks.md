# Lifecycle Hooks

The Rust documentation runner can run opaque shell hooks at suite, file, and context boundaries. Hooks belong in configuration so Markdown examples stay focused on product behavior instead of setup and cleanup plumbing.

## Hook Scopes

Lifecycle scopes nest from broad to narrow:

```text
suite setup
  file setup
    context setup
      documented command
    context teardown
  file teardown
suite teardown
```

A suite starts once for each discovered config root in one `mustmatch-cli test` invocation. File hooks run around each Markdown document. Context teardown runs after the final command that uses that context scope, including row-scoped context instances.

## Configuring Hooks

`mustmatch.toml` uses top-level `suite`, `file`, and `contexts` tables. Existing `pyproject.toml` configuration keeps the same shape under `[tool.mustmatch]`.

````toml
path = ["{root}/target/debug"]

[suite]
setup = ["scripts/spec-up.sh"]
teardown = ["scripts/spec-down.sh"]

[file]
setup = ["scripts/spec-reset-file.sh"]
teardown = ["scripts/spec-clean-file.sh"]

[contexts.demo]
cwd = "{tmp}"
setup = ["mytool seed demo"]
teardown = ["mytool clear demo"]
````

Hooks are plain shell commands run through the same process helper as documented bash blocks: `bash -c` with `set -e`, configured cwd, explicit environment, PATH additions, token expansion, captured stdout/stderr, and a timeout. mustmatch does not interpret Docker, databases, ports, health checks, credentials, or retries; hook commands own that behavior.

## Tokens And Environment

Hook commands can use the same path tokens as contexts:

- `{root}` — config root
- `{cwd}` — default document cwd for the current scope
- `{tmp}` — temporary directory owned by the hook scope

Top-level `path`, `env`, and `env_file`/`env_files` settings apply before scope-specific settings. Context hooks keep the context's cwd and environment for setup, documented commands, and teardown.

## Failure Semantics

A setup failure stops new work and returns a non-zero status. Teardowns for scopes that already started still run on normal failure paths and fail-fast paths. If teardown fails after all documented commands passed, the run fails; if a documented command already failed, that earlier failure remains the primary result.
