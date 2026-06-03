Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read AGENTS.md/CLAUDE.md and located the repo contract surface: `spec/*.md`, especially `spec/02-rust-runner.md` for the Rust runner.
- Preflight confirmed all ticket files are staged in the main-relative diff and there are no untracked ticket files.
- Rebased onto `origin/main` at start and before sign-off; branch was up to date.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant watching entry: mustmatch's possible divergence from the workspace `AGENTS.md` + `spec/*.md` standard.
- Probe result: this worktree has `AGENTS.md` naming `spec/*.md` / `make spec` as the behavioral contract, but `.march/validation-profiles.toml` still maps `spec-only` to `make test` and `full-blocking` to `make check && make test`. Filed `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md`.
- Docs probe: README still called `docs/` the executable specification. Fixed the touched README wording to say executable documentation, preserving `spec/*.md` as contract truth.
- Planning lint: `/home/ian/workspace/scripts/lint-planning.sh mustmatch` passed.

## Exercise Results — ran, inputs, observations

- `cargo run -q -p mustmatch-cli -- test --help` showed the expected `test` usage/options; no new CLI flags were added.
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner/table-scenarios.md` passed 8 row-expanded cases with labels `[double-two]`, `[double-three]`, `[alpha-case]`, `[beta-case]`, `[row-1]`, and `[row-2]`.
- Temporary adversarial fixtures verified diagnostics for missing row columns, unknown tables, conflicting `each_row`/`table`, mismatched run/expect outline tables, and row context cwd isolation.
- `mustmatch-cli test /tmp/mustmatch-no-such-file-007` exited 0 with `No markdown files found`; filed as a UX issue because an explicit missing path can hide typos.

## Edge Cases Tested — specific cases, results

- Missing row column: non-zero; diagnostic included row label and `unknown row column "missing"`.
- Missing named table: non-zero; diagnostic included `unknown table "Missing Rows"` before command execution.
- Conflicting `each_row="Rows" table="Other Rows"`: non-zero; clear conflict diagnostic.
- Scenario outline with different run/expect tables: non-zero; diagnostic named the table mismatch.
- Named context with `cwd = "{tmp}"` across two rows: passed; each row got an isolated cwd.
- Explicit missing path: exited 0; filed issue.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/01-cli-assertions.md` and `spec/02-rust-runner.md`.
- `make spec` passed: 6 passed.
- `uv run mustmatch verify-matrix .march/design-final.md --repo-root .` found the proof-matrix references.
- `uv run mustmatch lint spec/02-rust-runner.md` had 0 findings for the changed spec. `spec/01-cli-assertions.md` still has a pre-existing short-like finding outside this ticket's changed surface.
- Gap found: the new table-scenarios contract can be satisfied by failed runner output because the pipeline does not use pipefail and the assertion checks unordered substrings. A temporary intentionally failing outline fixture still made the outer `mustmatch like` exit 0. Filed `~/workspace/planning/mustmatch/issues/007-rust-runner-pipeline-failure-masked-by-contract.md` for design to rewrite behaviorally.
- Counts before/after: no shipped-contract assertions were added, removed, tightened, or relaxed during verify.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator verification is not pending.

## Regression Results — existing features verified

- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner` passed existing Rust-runner fixture behavior plus the new table fixture: 20 passed, 1 skipped.
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-pyproject` passed: 2 passed.
- Basic installed CLI assertions still worked for text contains, JSON subset, and `not like` checks.

## Test Suite — full-blocking result

- Ran the full-blocking profile exactly once as `make check && make test`.
- Result: green. Lint passed; Python docs/README/tests passed 63 tests; cargo tests passed 9 CLI tests, 47 core tests, 2 Python-binding tests, and doc-tests.

## Documentation — parity audit of docs/help/examples

- Audited README, `docs/04-fixtures-and-tables.md`, `docs/12-named-runs.md`, and `mustmatch-cli test --help`.
- Fixed README wording from executable specification to executable documentation for `docs/`.
- Fixed `docs/04-fixtures-and-tables.md` scenario-outline example so the expected column matches the shown `printf` output.
- Help text needed no change because the feature uses existing directives, not a new CLI flag.

## Issues Found and Fixed — fixes + proof

- Fixed README/docs wording and the `docs/04` scenario-outline example mismatch.
- Proof: `make check && make test` green; `make spec` green; manual table fixture run green.

## Issues Filed — list with paths

1. `~/workspace/planning/mustmatch/issues/007-rust-runner-pipeline-failure-masked-by-contract.md`
2. `~/workspace/planning/mustmatch/issues/007-missing-test-path-exits-zero.md`
3. `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md`

## Planning Updates — concrete issues filed or FAQ watching proposal

Filed the three concrete issues above. No FAQ edit was made; the validation-profile issue is the actionable ratchet for the relevant watching entry.

## UX Quality — CLI/UI assessment

- New row labels are readable in verbose output and identify failing rows.
- Error diagnostics for bad row/table directives are clear enough for a user to repair the Markdown.
- Existing missing-path behavior is weak UX and was filed as a follow-up.

Issues filed: 3
