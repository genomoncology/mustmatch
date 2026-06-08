# mustmatch

`mustmatch` is a single Rust CLI for **assertion pipelines** and **executable
Markdown specs**. Pipe a command's output in and assert it matches an expected
text / JSON / regex contract, or run documentation-first Markdown with
`mustmatch test` so your examples are also your tests. It ships static quality
commands (`lint`, `verify-matrix`) too.

This README is itself a spec: the assertion examples below run under `make spec`.

## Install

```bash skip
uv tool install mustmatch
```

(The install line above is documentation — `mustmatch test` only runs a `bash`
block when it pipes into `| mustmatch`, so commands shown for reference are never
executed.)

## Assertion pipelines

Compare stdin against one expected value — exactly, as a substring with `like`,
as a regex in `/slashes/`, or as a JSON subset.

```bash
printf 'hello world\n'                  | mustmatch like "world"
printf 'v1.2.3\n'                       | mustmatch "/^v[0-9]+[.][0-9]+[.][0-9]+$/"
printf '{"status":"ok","count":42}\n'   | mustmatch like '{"status":"ok"}'
printf 'all systems go\n'               | mustmatch not like "error"
```

## Executable Markdown

`mustmatch test PATH...` runs the code blocks in your Markdown as tests. A
document is the documentation a reader sees and the contract `make spec`
enforces — at once.

```console
$ mustmatch test spec/
...
passed
```

The full, runnable guide lives in [`spec/`](spec/), one feature per file:

| Topic | File |
|-------|------|
| CLI assertions | `spec/01-cli-assertions.md` |
| Comparison modes | `spec/02-comparison-modes.md` |
| Ellipsis (`...`) | `spec/03-ellipsis.md` |
| Normalization | `spec/04-normalization.md` |
| Executable Markdown & the safety model | `spec/05-executable-markdown.md` |
| Console examples & streams | `spec/06-console-and-streams.md` |
| Named runs | `spec/07-named-runs.md` |
| Tables & scenario outlines | `spec/08-tables-and-outlines.md` |
| Embedded fixture files | `spec/09-embedded-files.md` |
| Contexts | `spec/contexts/10-contexts.md` |
| Lifecycle hooks | `spec/lifecycle/11-lifecycle-hooks.md` |
| Linting specs | `spec/12-lint.md` |
| Verifying a proof matrix | `spec/13-verify-matrix.md` |
| Authoring guide & runner self-test | `spec/14-authoring-and-self-test.md` |
| Release smoke gate | `spec/15-release-smoke.md` |

## Quality commands

```bash
mustmatch lint spec/14-authoring-and-self-test.md | mustmatch like "findings=0"
```

`mustmatch verify-matrix DESIGN --repo-root ROOT` confirms a design document's
backticked file references resolve inside the repo.

## Gates

```bash skip
make lint
make test
make spec
make smoke
```

`make spec` builds the binary and runs both the runner and every inline
assertion against the build under test, so CI always exercises the current
source. `make smoke` builds or selects a wheel, installs it into an isolated
environment, and runs the package smoke document through the installed
`mustmatch` entry point before release.

## License

MIT
