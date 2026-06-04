Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; the repo contract is `spec/*.md` via `make spec`, with `make smoke` as the installed-wheel release/package gate.
- Read `.march/ticket.md`, design draft/final, code and review logs, checkpoint state, `.march/contract-red-check.json`, and `planning/mustmatch/faq.md`.
- Rebasing checks showed `main`/`origin/main` remain ancestors of this branch.
- Preflight staged ticket work products; no untracked repo files remain.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant watching entry: whether mustmatch follows the workspace contract standard. This ticket keeps `AGENTS.md` naming `spec/*.md`, validation profiles map `spec-only` to `make spec`, and the release smoke input stays outside the normal source-tree contract as `tests/smoke/smoke.md`.
- No relevant answered FAQ entries were weakened.
- No security/safety boundary issue was found in repo planning memory; release smoke uses a temporary venv and no secrets.

## Exercise Results — ran, inputs, observations

- `make smoke`: green; built a wheel, installed it into a throwaway venv, and `mustmatch test tests/smoke/smoke.md` reported `2 passed`.
- `SMOKE_WHEEL=/tmp/does-not-exist-mustmatch.whl make smoke`: failed loudly with `SMOKE_WHEEL does not exist`.
- Explicit wheel override with a copied wheel in a path containing a space, while a fake earlier `mustmatch` was on `PATH`: green; the target still selected the throwaway venv binary first.
- Structural probes confirmed `tests/smoke/smoke.md` has `file=`, stdin `| mustmatch`, and nested `mustmatch test` lines, and no `cargo`, `target/`, or `../` references.
- Workflow probe confirmed publish-job ordering landmarks: checkout, wheel artifact download, `run: make smoke`, then PyPI publish.

## Edge Cases Tested — specific cases, results

- Missing prerequisite: absent `SMOKE_WHEEL` path exits nonzero before install.
- Path safety/quoting: explicit wheel path with a space installs and runs correctly.
- PATH fallback: a fake earlier `mustmatch` on `PATH` does not get used; installed venv binary wins.
- Self-contained smoke input: forbidden dev-tree dependency scan produced no output.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/15-release-smoke.md`, `tests/smoke/smoke.md`, `Makefile`, `.github/workflows/release.yml`, `AGENTS.md`, and `README.md` against the proof matrix.
- Proof locations exist for all three check-lane entries in `.march/contract-red-check.json`.
- `mustmatch lint spec/15-release-smoke.md`: `findings=0`.
- `make spec` spec-only result: green, `74 passed, 2 skipped`.
- Contract gap filed: `planning/mustmatch/issues/020-release-smoke-contract-command-lines.md` because the smoke-doc structural assertion scans prose as well as executable lines. Runtime behavior is correct, but design should rewrite the assertion to target executable smoke structure.
- Assertion-quality delta: no weak assertions relaxed in verify; one weak assertion escalated to design via the issue above; no syntactic red found.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator-pending list is empty.

## Regression Results — existing features verified

- CLI JSON-subset assertion through `./target/debug/mustmatch`: green.
- Missing expected value in stdin assertion exits with usage status `2` and `Error: expected value required`.
- Existing embedded-fixture spec `spec/09-embedded-files.md` in verbose mode: `6 passed`.
- CLI help still exposes assertion mode, `test`, `verify-matrix`, and `lint`.

## Test Suite — full-blocking result

- Full-blocking profile run exactly once as `make lint && make test && make spec`: green.
- `make lint`: green.
- `make test`: green; Rust unit/doc tests green.
- `make spec`: green, `74 passed, 2 skipped`.

## Documentation — parity audit of docs/help/examples

- `make help` lists `smoke` with the other targets.
- `AGENTS.md` documents `make smoke` and `tests/smoke/`.
- `README.md` Gates section documents `make smoke`.
- Verify found and fixed one docs parity miss: the README spec table omitted new `spec/15-release-smoke.md`; added the `Release smoke gate` row.
- Release workflow smoke-before-publish ordering is documented by the checked spec and visible in the workflow.

## Issues Found and Fixed — fixes + proof

- Fixed README spec table omission by adding `Release smoke gate | spec/15-release-smoke.md`.
- Proof after fix: `make spec` green and full-blocking green.

## Issues Filed — list with paths

- `/home/ian/workspace/planning/mustmatch/issues/020-release-smoke-contract-command-lines.md` — design-level contract rewrite so the smoke-doc assertion targets executable lines rather than prose.

## Planning Updates — concrete issues filed or FAQ watching proposal (or "none")

Filed the contract ratchet issue above. No FAQ edit proposed.

## UX Quality — CLI/UI assessment (if applicable)

- `make smoke` is discoverable in help, fails clearly when `SMOKE_WHEEL` is missing, and reports the installed-wheel smoke result concisely.
- The release workflow gates publish before credentials are used by the PyPI publish action.

Issues filed: 1
