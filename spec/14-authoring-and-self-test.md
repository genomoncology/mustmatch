# Authoring guide and runner self-test

These specs are documentation that runs. The same file teaches a feature and
proves it under `make spec`, so the examples can never drift from the behavior.
Three rules keep them honest:

1. **Show what a user types and the output they expect.** The example is the
   proof — prefer a real command and its real output over prose describing it.
2. **Stay on the happy path.** Demonstrate the documented behavior; prove error
   and edge cases (bad regex flags, parser corners, comparator failures) in
   `cargo test`, not in Markdown.
3. **A block runs only if it asserts.** A `bash` block executes only when it
   pipes into `| mustmatch`; everything else is documentation. That is why an
   install or destructive command can appear for reference without ever running
   (see `05-executable-markdown.md`).

## Runner self-test

Beyond the per-feature tutorials, mustmatch exercises its own runner by running
it over the generic fixtures in `tests/fixtures/` and asserting the result
summary. These are regression guards, not tutorials — they run from the `spec/`
directory, so the fixtures are one level up.

The canonical fixture covers one of each block class and must report them all as
passing:

```bash
mustmatch test -v ../tests/fixtures/rust-runner | mustmatch like "PASS Bash assertion blocks run
PASS Console examples execute visible commands
PASS Named runs reuse JSON fields
PASS Named runs honor dependencies
PASS Expected exits and stderr streams
PASS Contexts hide setup
passed"
```

Documentation-only fences must not surface as skipped cases in user-visible
output:

```bash
mustmatch test -v ../tests/fixtures/rust-runner | mustmatch not like "SKIP
skipped"
```

Configuration falls back to `[tool.mustmatch]` in `pyproject.toml` when no
`mustmatch.toml` is present:

```bash
mustmatch test -v ../tests/fixtures/rust-runner-pyproject | mustmatch like "PASS Pyproject contexts still work
passed"
```

A fixture run must complete with no failed blocks — this guards against a false
green where a setup-only block is reported but a later consuming command fails:

```bash
mustmatch test ../tests/fixtures/rust-runner/embedded-files.md 2>&1 | mustmatch not like "FAIL
failed"
```

Tracked Markdown describes the current CLI directly; a grep for old
release-archaeology terms must come back empty:

```bash
git -C .. grep -inE 'py''thon|py''test|pyo''3|remo''ved|cut''over|trans''itional|mig''rat' -- '*.md' spec/ | mustmatch ""
```
