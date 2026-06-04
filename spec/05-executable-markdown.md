# Executable Markdown

`mustmatch test PATH...` walks every `.md` file under the given paths and runs
the code blocks as tests. A document is both the documentation a human reads and
the contract `make spec` enforces — the examples are the proof.

## What runs, and what is just documentation

The runner is deliberately conservative about what it executes:

- A plain ```bash``` block runs **only if it contains a `| mustmatch` pipe**.
  A block with no assertion is treated as documentation and is **never run** —
  so an install command or a destructive example shown for reference is safe.
- A block tagged `skip` is shown but never run.
- A non-`bash` fence (`json`, `text`, …) with no directive is documentation and
  does not execute.

The fixture below embeds a small document with one of each, then runs it. The
`npm install` block has no assertion, so it is reported `SKIP` and never
executes; only the asserting block runs.

````markdown file=demo.md
# Demo

## Runs because it asserts

```bash
printf 'ok\n' | mustmatch like "ok"
```

## Documentation only

```bash
npm install left-pad
```

## Skipped explicitly

```bash skip
printf 'never\n' | mustmatch like "never"
```

## Reference data

```json
{"example": true}
```
````

```bash
mustmatch test -v demo.md | mustmatch like "PASS Runs because it asserts
SKIP Documentation only
SKIP Skipped explicitly
1 passed, 2 skipped"
```

## `sh` is an alias for `bash`

A fence tagged `sh` runs the same way as `bash`.

```sh
printf 'via sh\n' | mustmatch like "via sh"
```

## The run summary and exit code

`mustmatch test` prints a one-line summary of `passed` / `failed` / `skipped`
counts and exits non-zero only when something actually failed. The fixture above
reported `1 passed, 2 skipped` and exited `0`, because a skip is not a failure.

## Runner options

`mustmatch test` accepts `-v`/`--verbose` (show each block), `-q`/`--quiet`,
`-x`/`--fail-fast`, `--timeout SECONDS` (per-block), and `--lang all|bash`. The
help text lists them.

```bash
mustmatch test --help | mustmatch like "--fail-fast"
```
