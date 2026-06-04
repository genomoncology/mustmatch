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

## Expected failures (`xfail`)

A block marked `xfail` still runs, but its result is inverted for reporting: an
expected **failure** is reported as `XFAIL` and keeps the suite green, while an
unexpected **pass** is reported as `XPASS`. Use it to document behavior that is
known-broken or not-yet-implemented without turning `make spec` red. Add a reason
with `xfail="..."`, and `strict` to make an `XPASS` a real failure — so a
fixed-but-still-marked example gets flagged for cleanup.

The fixture below has one block that fails as expected and one that has started
passing again. The run reports one `XFAIL` (with its reason) and one `XPASS`, and
still exits `0`.

````markdown file=xfail-demo.md
# Demo

## Known gap

```bash xfail="ticket-123: not yet implemented"
printf 'actual\n' | mustmatch like "desired output"
```

## Already fixed

```bash xfail
printf 'works\n' | mustmatch like "works"
```
````

```bash
mustmatch test -v xfail-demo.md | mustmatch like "XFAIL Known gap
ticket-123: not yet implemented
XPASS Already fixed
1 xfailed, 1 xpassed"
mustmatch test xfail-demo.md >/dev/null 2>&1 && code=0 || code=$?
printf 'exit=%s\n' "$code" | mustmatch like "exit=0"
```

Under `strict`, an `XPASS` is a real failure, so the run exits non-zero and the
stale marker gets noticed.

````markdown file=xfail-strict.md
# Strict

## Should be unmarked now

```bash xfail strict
printf 'works\n' | mustmatch like "works"
```
````

```bash
mustmatch test xfail-strict.md >/dev/null 2>&1 && code=0 || code=$?
printf 'exit=%s\n' "$code" | mustmatch like "exit=1"
```
