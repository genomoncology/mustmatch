Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; repo contract surface is `spec/*.md`, run by `make spec`.
- Read `.march/ticket.md`, design/code/review artifacts, checkpoint state, `.march/contract-red-check.json`, validation profiles, and `planning/mustmatch/faq.md`.
- Rebases onto `origin/main` at start and before sign-off were clean/up to date.
- Preflight staged `.march/code-log.md`; no untracked ticket files were present.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant FAQ watching entry: mustmatch's possible divergence from the workspace `AGENTS.md` + `spec/*.md` standard.
- Probe result: this worktree has `AGENTS.md` and `spec/*.md`; this ticket's shipped contract lives in `spec/03-rust-quality-commands.md` and `make spec` is green.
- Existing planning issue `~/workspace/planning/mustmatch/issues/007-validation-profiles-omit-spec-contract.md` already covers the profile drift where `spec-only`/`full-blocking` omit `make spec`, so no duplicate was filed.
- Security/safety probes covered missing inputs, invalid values, absolute paths, parent traversal, env/shell/route false-positive traps, and symlink escapes.

## Exercise Results — ran, inputs, observations

- `cargo run -q -p mustmatch-cli -- --help` lists `lint` and `verify-matrix`.
- `cargo run -q -p mustmatch-cli -- lint --help` exposes `SPEC`, `--min-like-len`, and `--json`.
- `cargo run -q -p mustmatch-cli -- verify-matrix --help` exposes `DESIGN`, `--repo-root`, and `--json`.
- `lint-clean-directive.md --json` exited `0` with `status=pass`, `finding_count=0`.
- `lint-findings.md --json` exited `1` with `status=fail`, `finding_count=3`, and all three expected rule names.
- `verify-matrix-design.md --repo-root . --json` exited `1` with `README.md` ok, `docs/does-not-exist.md` missing, `references_checked=2`, `failure_count=1`.
- Python/Rust parity spot-check matched for lint and verify-matrix status/counts.

## Edge Cases Tested — specific cases, results

- Empty markdown lint input: pass, `finding_count=0`.
- `--min-like-len 0`: pass for a one-character `like` literal, as expected for a zero threshold.
- Non-integer `--min-like-len`: exit `2`, clear diagnostic.
- Missing lint spec and omitted spec: exit `2`, clear diagnostics.
- Missing `bash` prerequisite simulated with an empty `PATH` and direct binary invocation: exit `1`, `bash is required to lint shell code blocks`.
- Verify-matrix table with route, env var, and shell pipeline pseudo-paths: pass with `references_checked=0`.
- Verify-matrix parent traversal, absolute path, and missing in-repo path: exit `1`; statuses were `invalid`, `invalid`, and `missing`.
- Omitted design, missing `--repo-root`, missing design file, and nonexistent repo root: exit `2`, clear diagnostics.
- Symlink escape under repo root: exit `1`; escaped path reported `invalid`.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/01-cli-assertions.md`, `spec/02-rust-runner.md`, and `spec/03-rust-quality-commands.md`.
- Grepped all five proof-matrix section names; every named `spec/03-rust-quality-commands.md::...` location exists.
- Ran `make spec`: green, 13 passed. This is the repo contract gate used here for the check lane.
- Ran `uv run mustmatch lint spec/03-rust-quality-commands.md --json`: pass, 0 findings.
- Assertion-strength audit: no weak shipped-contract assertions relaxed or rewritten in verify. The exact counts in the new spec are design-authored and non-incidental: lint count proves the same finding set; verify-matrix reference count proves false-positive traps are ignored.
- Counts before/after in verify: no shipped-contract assertions added, removed, or changed by verify.
- Follow-up found: running `uv run mustmatch verify-matrix .march/design-final.md --repo-root .` flags the intentionally expected-missing fixture path `docs/does-not-exist.md`; filed a design issue rather than retuning behavior in this verify step.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator verification is not pending.

## Regression Results — existing features verified

- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner` passed: 27 passed, 1 skipped.
- Existing match assertion surfaces passed for text `like`, JSON subset `like`, and `not like`.
- Targeted docs parity passed: `uv run python -m pytest docs/10-verify-matrix.md docs/11-lint.md README.md -q` → 7 passed.

## Test Suite — full-blocking result

- Ran the configured full-blocking profile exactly once: `make check && make test`.
- Result: green. Lint passed; pytest passed 63 tests; cargo tests passed 18 CLI unit tests, 2 CLI parity tests, 48 core tests, and 2 Python-binding tests.
- Separately ran the contract gate `make spec`: green, 13 passed.

## Documentation — parity audit of docs/help/examples

- Audited README Quality Checks, `docs/10-verify-matrix.md`, `docs/11-lint.md`, and Rust/Python help surfaces.
- Rust binary help and installed Python help both expose the documented lint and verify-matrix options.
- Targeted README/docs pytest run passed.

## Issues Found and Fixed — fixes + proof

No bounded runtime or documentation fixes were needed in verify.

## Issues Filed — list with paths

- `~/workspace/planning/mustmatch/issues/010-verify-matrix-expected-missing-fixture-refs.md` — design follow-up for expected-missing fixture paths in proof-matrix assertion text being treated as unresolved repo references.

## Planning Updates — concrete issues filed or FAQ watching proposal

Filed the concrete design issue above. No FAQ update was needed; the existing watching entry and issue 007 already cover the broader spec/profile divergence.

## UX Quality — CLI/UI assessment

- Help text is discoverable and script-relevant.
- JSON output carries stable status/count/rule/reference fields.
- Error messages for missing files, missing required args, invalid thresholds, missing `bash`, path escapes, and bad repo roots are actionable.

Issues filed: 1
