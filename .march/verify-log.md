Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; this repo's user-visible contract is `spec/*.md` via `make spec`.
- Read `.march/ticket.md`, design draft/final, code log, code-review log, checkpoint state, `.march/contract-red-check.json`, and `planning/mustmatch/faq.md`.
- Rebased at start and again before sign-off; branch remained up to date with `origin/main`.
- Preflight status found no untracked worktree files. The branch diff against `main` is limited to `.march/code-log.md`, `crates/mustmatch-cli/src/verify_matrix.rs`, and `spec/13-verify-matrix.md`.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- No active `watching` entries were present in `planning/mustmatch/faq.md`.
- Relevant answered memory says mustmatch's contract lives in `AGENTS.md` and `spec/*.md`; this ticket keeps that shape and documents the new author-facing `expected-missing` behavior in `spec/13-verify-matrix.md`.
- Security/safety boundary probed: unescaped absolute/outside-root paths still report `invalid` and exit nonzero.

## Exercise Results — ran, inputs, observations

- Current source binary probe with `cargo run -q -p mustmatch-cli -- verify-matrix` on a temporary design containing `README.md` plus `expected-missing docs/none.md`: exited 0, JSON reported one checked reference, and omitted `docs/none.md`.
- Same-cell binding probe: `expected-missing docs/escaped.md then docs/real.md` exited 1 and reported unmarked `docs/real.md` as `missing`.
- Previous-cell probe: marker text in one cell did not escape a path in the next cell; command exited 1 and reported the path as `missing`.
- Accidental suffix probe: `notexpected-missing docs/accidental.md` did not escape the path; command exited 1 and reported it as `missing`.
- Non-table regression probe: prose backticks remained ignored and produced `references_checked: 0`.
- Help and missing-prereq probes: `verify-matrix --help` remains concise; missing `--repo-root` target exits 2 with `Error: repo root not found`.

## Exploratory Verification — change-aware probes tried; high-signal probes; noisy/not-worth-repeating probes; recommended improved tests (`spec`, `test`, `lint`, `gate`, `verify-group`, docs/help, FAQ watching, experiment/harness); agent/tool-cost friction if applicable

- High-signal probes were the same-cell, previous-cell, suffix, and outside-root cases because the ticket's main risk is turning a local escape into a false-negative suppressor.
- Regression probes covered adjacent collector behavior: non-table backticks, unescaped missing refs, invalid outside-root refs, and help/error paths.
- Noisy probe: running `mustmatch test spec/13-verify-matrix.md -v` directly used the older installed `mustmatch` on `PATH`, not the source under test, and failed the new section. `make spec` is the authoritative source-tree contract gate and passed.
- Recommended improved test: filed a `spec` issue for the pre-existing `short-like-pattern` lint finding in `spec/13-verify-matrix.md::Resolving references`.
- Agent/tool-cost friction: no new CLI discovery friction; the marker is documented in the spec section where proof-matrix authors look.

## Edge Cases Tested — specific cases, results

- Empty/no table input: no references checked, pass.
- Missing prerequisite: nonexistent repo root exits 2 before verification.
- Malformed/wrong context marker: `notexpected-missing` is not accepted as an escape.
- Boundary binding: repeated code spans in the same cell only skip the immediately marked span.
- Security boundary: absolute path outside repo root remains `invalid` and fails.
- Error recovery: all failing probes were independent temp files; rerunning after fixing the design input succeeds cleanly.

## Spec Audit — specs reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/13-verify-matrix.md`, especially `Resolving references` and `Escaping expected-value paths`.
- Proof matrix locations from `.march/contract-red-check.json` exist and both entries are `lane: check`.
- New behavior has shipped contract coverage for JSON output and human output in `spec/13-verify-matrix.md::Escaping expected-value paths`.
- `make spec` (spec-only) result: green, `80 passed, 2 skipped`.
- Assertion-quality delta: 0 assertions relaxed in verify; 1 weak/pre-existing assertion escalated to design issue; no new shipped-spec assertions authored here.

## Verify Group — `lane: verify` entries exercised (each: assertion, red_command, observed_status); operator-pending list explicit if credentials unavailable

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator-pending list is empty.

## Regression Results — existing features verified

- `cargo test -q -p mustmatch-cli verify_matrix -- --nocapture`: green, 7 tests passed.
- `make spec`: green for the full shipped spec suite, including existing missing-reference behavior.
- Existing true positives preserved by real CLI probes: unescaped missing references exit 1, outside-root references exit 1 with `invalid`, and non-table backticks are ignored.

## Test Suite — full-blocking result

- Full-blocking profile run exactly once as `make lint && make test && make spec`: green.
- `make lint`: green (`cargo fmt --check` + `cargo clippy -- -D warnings`).
- `make test`: green (31 CLI tests, 48 core tests, doc-tests green).
- `make spec`: green (`80 passed, 2 skipped`).

## Documentation — parity audit of docs/help/examples

- `spec/13-verify-matrix.md` documents the `expected-missing` marker and its JSON/human-output semantics.
- `README.md` already points users to `spec/13-verify-matrix.md` for proof-matrix behavior; no separate README behavior prose needed.
- `verify-matrix --help` remains accurate for command syntax; marker semantics are detailed authoring behavior, not a CLI option.
- No stale architecture docs or examples were found for this behavior.

## Issues Found and Fixed — fixes + proof

- No bounded runtime or docs defects were found that required repair in verify.
- Proof: targeted probes, `cargo test -p mustmatch-cli verify_matrix`, `make spec`, and full-blocking all passed.

## Issues Filed — list with paths

- `/home/ian/workspace/planning/mustmatch/issues/024-verify-matrix-exit-code-short-like.md` — design rewrite for pre-existing short `mustmatch like "exit=1"` assertion in `spec/13-verify-matrix.md::Resolving references`.

## Planning Updates — concrete issues filed or FAQ watching proposal (or "none")

Filed the spec issue above. No FAQ `watching` entry proposed.

## UX Quality — CLI/UI assessment (if applicable)

- Human output for escaped expected paths lists only real checked references and omits the expected-missing fixture path, which matches the authoring mental model.
- Error output for missing repo roots remains clear.
- The source-tree workflow is efficient through `make spec`; direct `mustmatch test` can be noisy when the installed binary is stale, but that is not new to this ticket.

Issues filed: 1
