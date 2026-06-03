# Rust Documentation Runner

`mustmatch-cli test` runs executable Markdown without going through pytest. During the transition the installed `mustmatch` command still owns the public name, so this contract invokes the Rust binary through Cargo and asks it to run a generic documentation fixture.

## Run a documentation fixture

A documentation directory can mix bash assertion blocks, console examples, named runs, contexts, and unsupported Python blocks. The Rust runner reports the supported blocks as passing and makes unsupported Python blocks visible as skips.

```bash
cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner | mustmatch like "PASS Bash assertion blocks run
PASS Console examples execute visible commands
PASS Named runs reuse JSON fields
PASS Contexts hide setup
SKIP Unsupported Python blocks are visible
passed
skipped"
```
