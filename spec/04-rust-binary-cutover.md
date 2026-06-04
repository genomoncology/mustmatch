# Rust Binary Cutover

The shipped command is the Rust `mustmatch` binary. The repo no longer routes the
public CLI, spec gate, or package metadata through the transitional Python layer.

## Public binary uses the mustmatch name

The Rust binary owns the public command name and documents the subcommands users
invoke from terminals and automation.

```bash
cargo run -q -p mustmatch-cli --bin mustmatch -- --help | mustmatch like "mustmatch - Assert stdin output matches expected value or run Markdown docs.
Usage:
    command | mustmatch [not] [like]
    mustmatch test
    mustmatch verify-matrix
    mustmatch lint"
```

## Public binary runs Markdown specs

The public `mustmatch test` command can run the repo's own Markdown contract
without going through pytest or the transitional binary name.

```bash
cargo run -q -p mustmatch-cli --bin mustmatch -- test -v ../spec/01-cli-assertions.md | mustmatch like "PASS Exact match
PASS Substring match with `like`
PASS Regex match
3 passed"
```

## Spec gate avoids the Python runner

`make spec` dogfoods the Rust runner directly. A dry run of the gate should not
show Python package or pytest runner plumbing.

```bash
make -n -C .. spec | mustmatch not like "uv run
python
pytest"
```

## Cargo workspace has no Python binding crate

The shipped workspace metadata is Rust-only; the PyO3 binding crate is not part
of the release graph.

```bash
cargo metadata --no-deps --format-version 1 | mustmatch not like "mustmatch-python
pyo3"
```

## Runtime Python package paths are absent

The runtime Python CLI, document runner, pytest plugin, and PyO3 crate are gone
from the checkout after the cutover.

```bash
find .. -path ../.git -prune -o \( -path ../src/mustmatch -o -path ../crates/mustmatch-python \) -print | mustmatch not like "src/mustmatch
crates/mustmatch-python"
```
