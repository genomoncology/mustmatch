Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; this repo's mustmatch contract is `spec/*.md`, run by `make spec`, while runner error paths are cargo tests.
- Read `.march/ticket.md`, `.march/design-draft.md`, `.march/design-final.md`, `.march/code-log.md`, `.march/code-review-log.md`, `.march/checkpoint.json`, `.march/contract-red-check.json`, and `planning/mustmatch/faq.md`.
- Rebased at start and before sign-off; branch remained up to date with `origin/main`.
- Preflight found no untracked files. Staged ticket work products up front, then staged the bounded README/docs repair found during verification.
- Diff vs `main` is limited to `.march/code-log.md`, `README.md`, `crates/mustmatch-cli/src/context.rs`, `crates/mustmatch-cli/src/runner.rs`, and `crates/mustmatch-cli/tests/runner_error_paths.rs`; no `spec/*.md` files changed.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- `planning/mustmatch/faq.md` has no active `watching` entries.
- Relevant answered memory says mustmatch's contract lives in `AGENTS.md` and `spec/*.md`; this ticket preserves that split by proving the new runner error paths in cargo tests rather than shipped specs.
- Safety boundaries probed: missing path diagnostics, quiet mode, mixed valid+missing operands, invalid `--lang`, cyclic `uses=`, and setup failure redaction. The synthetic secret was not leaked.

## Exercise Results — ran, inputs, observations

- `cargo test -q -p mustmatch-cli --test runner_error_paths -- --nocapture`: green, 5 passed. This covered all five check-lane assertions from `.march/contract-red-check.json`.
- Missing explicit path probe with source CLI: exited `1`, stdout empty, stderr `Path not found: .../missing.md`.
- Existing empty directory probe: exited `0`, stderr `No markdown files found`, preserving the intended no-op.
- Mixed valid markdown plus missing operand: exited `1` before running the valid file, so a typo cannot be hidden by another good operand.
- Quiet missing path: exited `1` with zero stdout/stderr bytes.
- Bare-filename `mustmatch.toml` context probe: from the fixture directory, `mustmatch test doc.md` exited `0`, printed `1 passed`, and wrote the `{root}` sentinel in the config directory.
- Bare-filename `pyproject.toml` context probe: same shape, exited `0` and wrote the `{root}` sentinel in the config directory.
- Invalid `--lang nope`: exited `2`, reported `Error: --lang must be all or bash`, and did not print a no-tests/no-markdown success.
- Cyclic named-run fixture: exited nonzero with clear `cyclic run dependency` diagnostics rather than recursing.
- Setup failure redaction fixture: exited nonzero with `context "leaky" setup command failed`; the synthetic secret value was absent.

## Exploratory Verification — change-aware probes tried; high-signal probes; noisy/not-worth-repeating probes; recommended improved tests (`spec`, `test`, `lint`, `gate`, `verify-group`, docs/help, FAQ watching, experiment/harness); agent/tool-cost friction if applicable

- High-signal probes were missing/empty/mixed/quiet path operands and bare-filename context configs because those directly target the changed path handling and catch the original silent-green and empty-`{root}` failures.
- Adjacent regression probes covered pyproject fallback contexts, invalid language parsing, named-run cycle detection, setup secret redaction, and existing rust-runner fixtures.
- Noisy probes:
  - Running `cargo run -q -p mustmatch-cli --` from inside a temporary fixture directory failed because Cargo could not find `Cargo.toml`; using the built source binary path is the right user-like probe for arbitrary cwd fixtures.
  - Running `./target/debug/mustmatch test spec/` without prepending `target/debug` to `PATH` made nested spec commands resolve the older installed `mustmatch`; `make spec` / `PATH="$PWD/target/debug:$PATH" ./target/debug/mustmatch ...` is the authoritative source-tree shape.
  - `./target/debug/mustmatch lint spec/` does not accept a directory; not relevant to this runner-path ticket and not repeated.
- Improved tests already landed in this ticket as cargo integration tests (`test`). No additional spec/lint/gate/verify-group follow-up is needed.
- Agent/tool-cost friction: the source-tree command shape is efficient through `make spec`; direct ad hoc runs need `PATH` discipline so nested `mustmatch` calls use the built binary, but that is existing repo behavior and documented in the Makefile.

## Edge Cases Tested — specific cases, results

- Empty/zero input equivalent: existing empty directory remains exit-0 no-op with `No markdown files found`.
- Missing prerequisite: nonexistent explicit operand exits nonzero and names the path.
- Malformed/wrong option: unsupported `--lang` exits as usage error before discovery.
- Boundary/mixed operands: any missing explicit operand fails even if another operand is valid markdown.
- Quiet recovery: `-q` suppresses diagnostics but preserves nonzero exit, so scripts can retry/fix the path cleanly.
- Bare-filename root boundary: both `mustmatch.toml` and `pyproject.toml` configs resolve `{root}` to the invocation/config directory for `mustmatch test doc.md`.
- Safety/security: setup-failure diagnostics omit expanded synthetic secret values.

## Spec Audit — specs reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/05-executable-markdown.md`, `spec/contexts/10-contexts.md`, `spec/07-named-runs.md`, `spec/lifecycle/11-lifecycle-hooks.md`, `spec/14-authoring-and-self-test.md`, and `README.md` for the changed runner/context surfaces.
- Proof-matrix locations in `.march/contract-red-check.json` all resolve to `crates/mustmatch-cli/tests/runner_error_paths.rs`.
- `git diff --name-only main -- spec` is empty; verify authored no new shipped spec assertions.
- No missing shipped-contract coverage blocks approval: `.march/ticket.md` and design-final intentionally route these runner error-path/runtime safety behaviors to cargo tests, not `spec/*.md`.
- Spec-only command `make spec`: green, `80 passed, 2 skipped` before full-blocking; full-blocking repeated the same spec result after the README repair.
- Assertion-quality delta: 0 shipped spec assertions relaxed, 0 weak assertions escalated, 0 syntactic-red spec references found. The only relaxation was README prose/example text, changing stale exact `67 passed` to durable `passed` wording.

## Verify Group — `lane: verify` entries exercised (each: assertion, red_command, observed_status); operator-pending list explicit if credentials unavailable

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator-pending list is empty.

## Regression Results — existing features verified

- `PATH="$PWD/target/debug:$PATH" ./target/debug/mustmatch test -v tests/fixtures/rust-runner`: green, `27 passed` covering assertion blocks, console examples, named runs, expected exits/stderr, contexts, tables, and embedded files.
- `PATH="$PWD/target/debug:$PATH" ./target/debug/mustmatch test -v tests/fixtures/rust-runner-pyproject`: green, `2 passed` covering pyproject context fallback.
- `make spec`: green for the full shipped spec suite and README.
- Existing empty-directory no-op remains unchanged.

## Test Suite — full-blocking result

- Full-blocking profile run exactly once as `make lint && make test && make spec`: green.
- `make lint`: green (`cargo fmt --check` + `cargo clippy -- -D warnings`).
- `make test`: green (31 CLI unit tests, 5 `runner_error_paths` integration tests, 48 core tests, doc-tests green).
- `make spec`: green (`80 passed, 2 skipped`).

## Documentation — parity audit of docs/help/examples

- `mustmatch test --help` remains accurate for options and `PATHS...` syntax.
- Main `mustmatch --help` remains accurate for the `test`, `verify-matrix`, and `lint` command list.
- No public docs claimed missing explicit paths were an exit-0 no-op; no docs/help update was required for the new missing-path diagnostic.
- `spec/contexts/10-contexts.md` already documents `{root}` as the directory holding the config file; the implementation now matches that for bare-filename invocations.
- Fixed one stale README console example count: `67 passed` became durable `passed` wording so the example no longer drifts when the spec count changes.

## Issues Found and Fixed — fixes + proof

- Fixed README stale count in a non-executable console example: replaced exact `67 passed` with durable `passed` wording.
  - Proof: full-blocking `make lint && make test && make spec` stayed green after the README repair.
- No bounded runtime defects were found beyond the code-step fixes already present.

## Issues Filed — list with paths

None.

## Planning Updates — concrete issues filed or FAQ watching proposal (or "none")

None. No recurring unautomated constraint remained after the bounded README fix, and the ticket's runtime behaviors are now covered by cargo tests.

## UX Quality — CLI/UI assessment (if applicable)

- Missing explicit path output is concise, names the path, and exits nonzero.
- Empty-directory no-op remains quiet except for the existing `No markdown files found` diagnostic.
- `-q` preserves script-friendly nonzero status while suppressing user-facing output.
- Context `{root}` now matches the author mental model for both `mustmatch.toml` and pyproject configs invoked via bare filenames.
- No excessive tool-call/token friction in the CLI behavior itself; source-tree verification remains cheapest through Makefile gates.

Issues filed: 0
