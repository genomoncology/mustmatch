# Rust Binary Cutover

The shipped command is the Rust `mustmatch` binary. The repo no longer routes the
public CLI, spec gate, or package metadata through the transitional Python layer.

## Public binary uses the mustmatch name

The Rust binary owns the public command name and documents the subcommands users
invoke from terminals and automation.

```bash
cargo run -q -p mustmatch-cli --bin mustmatch -- --help | mustmatch like "Usage:
    command | mustmatch
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
passed"
```

## Spec gate invokes the Rust runner

`make spec` dogfoods the Rust runner directly. A dry run of the gate shows the
Cargo-built public binary running the repository specs.

```bash
make -n -C .. spec | mustmatch like "cargo run
--bin mustmatch
test spec/"
```

## Spec gate avoids the Python runner

The spec gate no longer shells through Python package or pytest runner plumbing.

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

## PyPI packaging points at the Rust binary

The PyPI build metadata keeps the existing install path while building the Rust
command-line binary instead of a Python extension module.

```bash
awk '/manifest-path|bindings/ { print }' ../pyproject.toml | mustmatch like "manifest-path = \"crates/mustmatch-cli/Cargo.toml\"
bindings = \"bin\""
```

## PyPI packaging has no Python runtime entry points

The wheel metadata does not expose the deleted Python CLI or pytest plugin as
runtime entry points.

```bash
awk '/mustmatch[.]cli|mustmatch[.]pytest_plugin|module-name|python-source|crates[/]mustmatch-python/ { print }' ../pyproject.toml | mustmatch not like "mustmatch.cli
mustmatch.pytest_plugin
module-name
python-source
crates/mustmatch-python"
```

## Runtime Python package paths are absent

The runtime Python CLI, document runner, pytest plugin, and PyO3 crate are gone
from the checkout after the cutover.

```bash
find .. -path ../.git -prune -o \( -path ../src/mustmatch -o -path ../crates/mustmatch-python \) -print | mustmatch not like "src/mustmatch
crates/mustmatch-python"
```
