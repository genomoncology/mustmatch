# mustmatch

`mustmatch` is a single Rust CLI for assertion pipelines and executable Markdown specs. It compares stdin against expected text/JSON/regex contracts, runs documentation-first Markdown examples with `mustmatch test`, and provides static quality commands for spec linting and proof-matrix references.

## Install

Install the package to get the `mustmatch` command:

```bash skip
uv tool install mustmatch
```

For repo-local development, run the binary through Cargo:

```bash
cargo run -q -p mustmatch-cli --bin mustmatch -- --help
```

## CLI Assertions

Pipe command output into `mustmatch` and compare against one expected value.

```bash
echo "hello" | mustmatch "hello"
echo "hello world" | mustmatch like "world"
echo "v1.2.3" | mustmatch "/^v[0-9]+[.][0-9]+[.][0-9]+$/"
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

## Executable Markdown

Markdown documents run directly with the Rust binary:

```bash
mustmatch test spec/
```

Prefer documentation-first examples: show the command a user would type and the output they should expect.

````markdown
```console mustmatch
$ mytool version
mytool 1.2.3
```
````

Named runs are available when command and output need to be decoupled, especially for JSON subset checks.

````markdown
```bash run id=version-json
mytool --json version
```

```json expect=version-json contains
{
  "name": "mytool"
}
```
````

Tables can drive per-row bash scenarios with `each_row`, embedded `file=<relative/path>` blocks can materialize fixtures, and lifecycle hooks can keep suite, file, and context setup/teardown in configuration instead of Markdown.

## Quality Checks

Use `mustmatch verify-matrix` to confirm proof-matrix references stay inside the repo, and `mustmatch lint` to lint Markdown specs without executing their fences.

- `mustmatch verify-matrix .march/design-final.md --repo-root .`
- `mustmatch lint spec/01-cli-assertions.md`

The repo gates are Rust-only:

```bash
make lint
make test
make spec
```

## Behavioral Contract

The executable contract lives in `spec/*.md` and is run by `make spec` through the Rust binary. Unit tests live under the Rust crates and run with `cargo test` via `make test`.

## License

MIT
