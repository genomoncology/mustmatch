Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; repo behavioral contracts are `spec/*.md`, run by `make spec`.
- Read `.march/ticket.md`, design draft/final, code log, code-review log, checkpoint state, `.march/contract-red-check.json`, validation profiles, and `planning/mustmatch/faq.md`.
- Rebases onto `origin/main` at start and before sign-off were clean/up to date; final rebase used autostash and verify fixes were re-staged.
- Preflight found no untracked files; ticket work products are staged/tracked in the diff against `main`.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant FAQ watching entry: mustmatch's possible divergence from the workspace `AGENTS.md` + `spec/*.md` standard.
- Probe result: this worktree has `AGENTS.md`; the lifecycle contract is in `spec/02-rust-runner.md`; `make spec` is green with 17 passed.
- Existing planning issue `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md` already covers the validation-profile drift where March `spec-only`/`full-blocking` profiles omit `make spec`; no duplicate filed.
- Security/safety probes covered malformed config, missing context, invalid timeout, missing/empty input directory, setup-failure cleanup, and generated sentinel cleanup.

## Exercise Results — ran, inputs, observations

- `cargo run -q -p mustmatch-cli -- test --help` showed `PATHS`, `--verbose`, `--quiet`, `--fail-fast`, `--timeout`, `--lang`, and help.
- Lifecycle fixtures passed with real runner invocations:
  - `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-lifecycle/setup-hooks.md` → 3 passed.
  - `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-lifecycle-pyproject/setup-hooks.md` → 3 passed.
  - `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-lifecycle/context-teardown.md` → 2 passed.
  - `cargo run -q -p mustmatch-cli -- test tests/fixtures/rust-runner-lifecycle/after-run-teardown.md` followed by sentinel `find` → no suite/file/context body sentinels remained.
- Verify found and fixed one bounded runtime defect: setup failure after partial setup did not run teardown because teardown was only registered after setup success.

## Edge Cases Tested — specific cases, results

- Partial suite setup failure: setup wrote `suite-state.txt` then exited 9; command exited 1 and teardown removed the sentinel after the fix.
- Missing context: block with `context=missing` exited 1 with `No mustmatch context named "missing" in config`.
- Malformed `mustmatch.toml`: exited 1 with a TOML parse diagnostic naming the config path and parse location.
- Empty directory: printed `No markdown files found` and exited successfully, preserving existing runner behavior.
- Invalid `--timeout nope`: exited 2 with `Error: --timeout must be an integer`.
- Focused unit proofs added/ran for suite, file, and context setup-failure cleanup: `cargo test -p mustmatch-cli setup_failure -- --nocapture` → 3 passed; teardown-focused regression run → 6 passed.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/01-cli-assertions.md`, `spec/02-rust-runner.md`, and `spec/03-rust-quality-commands.md`.
- Grepped all four `.march/contract-red-check.json` proof locations; every named `spec/02-rust-runner.md::...` section exists.
- Ran `make spec`: green, 17 passed. This confirms every `lane: check` entry in `.march/contract-red-check.json` is green.
- `uv run mustmatch lint spec/02-rust-runner.md --json` passed with 0 findings; `spec/03` also passed. `spec/01` has a pre-existing short `like "world"` lint finding outside this ticket's changed surface.
- Lifecycle assertions target user-visible behavior: PASS labels from real fixture runs plus sentinel absence after runner exit. They would fail if suite/file setup, pyproject fallback, context teardown, or after-run teardown were broken.
- Counts before/after in verify: no shipped-contract assertions were added, removed, or changed by verify. The runtime cleanup fix is covered by Rust unit tests because setup-failure rollback is an internal/error-path behavior per design.
- No design-level contract gaps blocking approval were found.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator verification is not pending.

## Regression Results — existing features verified

- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner` → 27 passed, 1 skipped.
- Existing pyproject fallback and Rust runner fixtures remained covered by `make spec`.
- `uv run python -m pytest docs/16-lifecycle-hooks.md docs/08-configuration.md docs/13-standalone-doc-runner.md README.md -q` → 13 passed.

## Test Suite — full-blocking result

- Ran the configured `full-blocking` profile exactly once: `make check && make test`.
- Result: green. Lint passed; pytest passed 63 tests; Rust tests passed 25 `mustmatch-cli` unit tests, 2 quality parity tests, 48 core tests, and 2 Python binding tests.
- Separately ran the contract gate `make spec`: green, 17 passed.

## Documentation — parity audit of docs/help/examples

- Audited `README.md`, `docs/16-lifecycle-hooks.md`, `docs/08-configuration.md`, `docs/13-standalone-doc-runner.md`, and `docs/index.md` against shipped lifecycle behavior.
- Docs correctly describe suite/file/context hook scopes, `mustmatch.toml` and `[tool.mustmatch]` configuration, tokens/env/PATH, opaque shell-command boundary, and failure semantics.
- Targeted docs/README executable run passed (13 passed). No docs/help mismatch found.

## Issues Found and Fixed — fixes + proof

- Fixed: suite/file/context setup failures now run their configured teardown if a setup command fails after creating partial state.
- Implementation proof: added Rust unit regressions for suite setup failure cleanup, file setup failure cleanup, and context setup failure cleanup.
- Command proof: `cargo test -p mustmatch-cli setup_failure -- --nocapture` → 3 passed; full-blocking and `make spec` remained green.

## Issues Filed — list with paths

None.

## Planning Updates — concrete issues filed or FAQ watching proposal

No new planning issue or FAQ entry needed. The only new defect was fixed in-ticket, and existing issue 007 already covers the validation-profile/spec divergence noted during the FAQ watch.

## UX Quality — CLI/UI assessment

- CLI help is discoverable and script-friendly for the runner options touched here.
- Lifecycle failure diagnostics identify the failing scope/phase without echoing expanded hook commands.
- Missing context, malformed config, and invalid option errors are actionable.

Issues filed: 0
