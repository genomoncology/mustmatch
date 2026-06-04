# Contexts

A context bundles the working directory, environment variables, `PATH` entries,
and setup commands a documented command needs — so the example stays clean while
the plumbing lives in configuration. Contexts are defined in a `mustmatch.toml`
beside the spec (or in `[tool.mustmatch]` in `pyproject.toml`). This directory's
config defines a `demo` context:

```toml
[contexts.demo]
cwd = "{tmp}"                 # run in a fresh temp directory
required_env = ["DOC_VALUE"]  # fail fast if unset
path = ["{tmp}"]              # put the temp dir on PATH
setup = [
  "printf 'state=ready\n' > {tmp}/state.txt",
  "printf '#!/bin/sh\necho helper-ran\n' > {tmp}/greet",
  "chmod +x {tmp}/greet",
]

[contexts.demo.env]
DOC_VALUE = "example"
```

## A command running in a context

Tag a block with `context=demo`. It runs in the context's `cwd`, with the
context's environment and `PATH`, after its setup has prepared `state.txt` and a
`greet` helper — none of which clutters the example.

```bash run id=in-context context=demo
cat state.txt
greet
env | grep '^DOC_VALUE='
```

```text expect=in-context contains
state=ready
helper-ran
DOC_VALUE=example
```

## Tokens

Three tokens expand inside context values: `{tmp}` is a fresh temporary directory
created per context, `{root}` is the directory holding the config file, and
`{cwd}` is the document's directory. `${VAR}` expands an environment variable.

## Required environment and configuration location

`required_env` lists variables that must be present and non-empty; a missing one
fails the context before any command runs. Configuration is read from
`mustmatch.toml` when present, falling back to `[tool.mustmatch]` in
`pyproject.toml`.
