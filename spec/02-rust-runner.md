# Rust Documentation Runner

`mustmatch-cli test` runs executable Markdown without going through pytest. During the transition the installed `mustmatch` command still owns the public name, so this contract invokes the Rust binary through Cargo and asks it to run a generic documentation fixture.

## Run a documentation fixture

A documentation directory can mix bash assertion blocks, console examples, named runs, expected exits, contexts, and unsupported Python blocks. The Rust runner reports the supported blocks as passing and makes unsupported Python blocks visible as skips.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner | mustmatch like "PASS Bash assertion blocks run
PASS Console examples execute visible commands
PASS Named runs reuse JSON fields
PASS Named runs honor dependencies
PASS Expected exits and stderr streams
PASS Contexts hide setup
SKIP Unsupported Python blocks are visible
passed
skipped"
```

## Run a pyproject fallback fixture

A repository without `mustmatch.toml` can still use the existing `[tool.mustmatch]` context configuration in `pyproject.toml`. The Rust runner keeps that compatibility while preferring `mustmatch.toml` when both files are present.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner-pyproject | mustmatch like "PASS Pyproject contexts still work
passed"
```

## Run lifecycle hooks from pyproject fallback

A repository that keeps configuration in `[tool.mustmatch]` gets the same lifecycle hook behavior as `mustmatch.toml`. The fixture uses pyproject-owned suite, file, and context setup so fallback parsing cannot silently lag the new lifecycle schema.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner-lifecycle-pyproject/setup-hooks.md | mustmatch like "PASS Pyproject suite setup runs
PASS Pyproject file setup runs
PASS Pyproject context setup runs
passed"
```

## Run bash table scenarios and outlines

The Rust documentation runner can use Markdown tables as bash scenario data. Row placeholders substitute into commands and expected output, and verbose output names each row so a reader can identify which scenario ran.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner/table-scenarios.md | mustmatch like "PASS Bash each_row substitutes table columns
[double-two]
[double-three]
PASS Scenario outlines substitute inputs and outputs
[alpha-case]
[beta-case]
PASS Table selection and coercion use the named case table
[row-1]
[row-2]
passed"
```

## Run embedded fixture files

The Rust documentation runner can materialize named file blocks into the working directory for a section. The command examples read ordinary relative paths, while the document shows the file content directly instead of hiding setup in heredocs.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner/embedded-files.md | mustmatch like "PASS Embedded JSON files become local inputs
PASS Section fixture files are shared by later commands
PASS New sections get fresh fixture directories
PASS Row fixtures render table values
[row-alpha]
[row-beta]
PASS Context fixture files land in context cwd
passed"
```

The fixture run must complete without failed blocks; this guards against a false green where setup-only fixture blocks are reported but later consuming commands fail.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner/embedded-files.md 2>&1 | mustmatch not like "FAIL
failed"
```

## Run lifecycle setup hooks

Lifecycle setup hooks prepare the runner scopes before user examples execute. The fixture reads one suite sentinel, one file sentinel, and one context sentinel from normal documented commands.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner-lifecycle/setup-hooks.md | mustmatch like "PASS Suite setup runs before document blocks
PASS File setup runs before document blocks
PASS Context setup remains visible
passed"
```

## Run context teardown after last use

A context teardown runs after the final block using that context, before later no-context blocks in the same document. The fixture writes a context body sentinel inside the context and then proves the sentinel is absent in the following block.

```bash
cargo run -q -p mustmatch-cli -- test -v ../tests/fixtures/rust-runner-lifecycle/context-teardown.md | mustmatch like "PASS Context body can use setup state
PASS Context teardown removes body sentinel
passed"
```

## Run suite and file teardowns after exit

Suite and file teardowns clean up after the runner exits. The fixture writes suite and file body sentinels during a successful document run; after the command returns, neither sentinel should remain in the fixture directory.

```bash
cargo run -q -p mustmatch-cli -- test ../tests/fixtures/rust-runner-lifecycle/after-run-teardown.md >/dev/null
find ../tests/fixtures/rust-runner-lifecycle -maxdepth 1 \( -name suite-body.txt -o -name file-body.txt \) -print | mustmatch not like "suite-body.txt
file-body.txt"
```
