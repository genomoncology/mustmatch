Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; repo contract surface is `spec/*.md`, with this ticket covered in `spec/02-rust-runner.md`.
- Read ticket/design/code/review artifacts, `.march/contract-red-check.json`, checkpoint state, and `planning/mustmatch/faq.md`.
- Rebases onto `origin/main` at start and before sign-off were clean/up to date.
- Preflight found no untracked ticket files; staged work products are updated before sign-off.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant watching entry: mustmatch's potential divergence from the workspace `AGENTS.md` + `spec/*.md` standard.
- Probe result: this worktree's AGENTS names `spec/*.md` / `make spec` as contract truth; the ticket uses that surface. `docs/index.md` still called `docs/` the executable specification, so verify fixed it to say executable documentation.
- `.march/validation-profiles.toml` still maps `spec-only`/`full-blocking` away from `make spec`; this is already filed as `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md`, so no duplicate issue was opened.
- Security/safety probe: malicious `file=` paths using `..` and absolute paths fail before file writes with clear diagnostics.
- Planning lint: `/home/ian/workspace/scripts/lint-planning.sh mustmatch` passed.

## Exercise Results — ran, inputs, observations

- `cargo run -q -p mustmatch-cli -- test --help` showed expected `test` options; no new CLI flags were added.
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner/embedded-files.md` passed all embedded-file behaviors: JSON fixture, section reuse, fresh H2 cwd, row fixtures, and context cwd.
- Verified file blocks are silent setup: verbose output only reports consuming bash blocks, not `file=` blocks.
- Adversarial temporary fixtures for parent traversal, absolute path, directive conflict, and missing row placeholder all failed with user-repairable diagnostics.
- Regression probe for a non-fixture markdown sidecar file passed, preserving document-directory cwd outside fixture-capable sections.

## Edge Cases Tested — specific cases, results

- `file=../escape.txt`: non-zero; diagnostic says path must be relative and stay under fixture cwd.
- `file=/tmp/escape.txt`: non-zero; same confinement diagnostic.
- `file=config.json expect=run-output`: non-zero; diagnostic says file blocks cannot also use `expect=`.
- Row-scoped file content with `{{missing}}`: non-zero; diagnostic includes `unknown row column "missing"` and row label.
- Context-backed fixture (`context=demo`, `cwd={tmp}`): passed; relative file path is materialized in the resolved context cwd.
- Section isolation: fixture contract's new H2 cannot see prior section's `state/status.txt`.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/02-rust-runner.md` and the new fixture `tests/fixtures/rust-runner/embedded-files.md` for the changed surface.
- `make spec` passed: 8 passed, including both check-lane entries from `.march/contract-red-check.json`.
- `uv run mustmatch verify-matrix .march/design-final.md --repo-root .` found the proof-matrix spec reference.
- `uv run mustmatch lint spec/02-rust-runner.md` reported 0 findings.
- Assertion-strength audit: positive landmarks cover distinct user-visible behaviors, row labels prove both row copies, and the separate `not like "FAIL\nfailed"` guard catches failed blocks. A direct guard probe failed as expected on output containing `failed`.
- Counts before/after: verify added no shipped-contract assertions and relaxed no shipped-contract assertions. No contract gap found for 008.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator verification is not pending.

## Regression Results — existing features verified

- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner` passed: 27 passed, 1 skipped.
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-pyproject` passed: 2 passed.
- Basic installed CLI assertions passed for text `like`, JSON subset `like`, and `not like`.

## Test Suite — full-blocking result

- Ran the configured full-blocking profile exactly once: `make check && make test`.
- Result: green. Lint passed; pytest passed 63 tests; cargo tests passed 11 CLI tests, 48 core tests, and 2 Python-binding tests.
- Separately ran the contract gate `make spec`: green, 8 passed.

## Documentation — parity audit of docs/help/examples

- Audited README, `docs/05-directives.md`, `docs/15-embedded-files.md`, `docs/index.md`, the fixture docs, and `mustmatch-cli test --help`.
- Fixed `docs/index.md` wording from executable specification to executable documentation to keep `spec/*.md` as contract truth.
- Help text needed no change because `file=` is a fence directive, not a CLI option.

## Issues Found and Fixed — fixes + proof

- Fixed `docs/index.md` contract-wording drift.
- Proof: `make check && make test` green; `make spec` green; docs/help audit passed.

## Issues Filed — list with paths

None.

## Planning Updates — concrete issues filed or FAQ watching proposal

No new planning issue was needed. The only recurring planning concern observed here is already tracked by `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md`.

## UX Quality — CLI/UI assessment

- Verbose output names the consuming behavior sections and row labels; `file=` setup blocks do not create misleading PASS lines.
- Error messages for unsafe paths, directive conflicts, and missing row placeholders are clear enough for a user to repair the Markdown.

Issues filed: 0
