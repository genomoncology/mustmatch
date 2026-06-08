Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; mustmatch's shipped behavioral contract is `spec/*.md`, run by `make spec`.
- Read the required March artifacts: `.march/ticket.md`, `.march/design-draft.md`, `.march/design-final.md`, `.march/code-log.md`, `.march/code-review-log.md`, `.march/checkpoint.json`, `.march/contract-red-check.json`, prior `.march/verify-log.md`, and supporting March notes/profiles.
- Read `planning/mustmatch/faq.md`; there are no active `watching` entries.
- Rebased at start; fetched before sign-off and confirmed `origin/main` is still an ancestor of `HEAD`, so no final rebase was needed.
- Preflight found no untracked files. Ticket diff is limited to March artifacts plus `spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- No relevant `watching` entries are active for mustmatch.
- Relevant answered entry: mustmatch uses `AGENTS.md` plus `spec/*.md` as its executable contract. This ticket preserves that by changing shipped specs only, with no runtime/README/help behavior changes.
- Security/safety boundaries touched here are local-only: embedded fixture paths remain relative, smoke scans inspect tracked Markdown, and no credentials/network/destructive operations are introduced.

## Exercise Results — ran, inputs, observations

- `make spec`: green, `82 passed, 2 skipped`; this covered every `lane: check` entry in `.march/contract-red-check.json`.
- Injected an intentional failing Markdown file into a temp copy of `tests/fixtures/rust-runner`:
  - Positive masked pipeline probe exited `0`, reproducing the original false-negative shape.
  - New absence assertion shape exited `1` and reported forbidden `FAIL` and `failed`, proving the mask is closed.
- Temp quoted-hash fixture with single-quoted hash, double-quoted hash, and leading real shell comment: source binary reported the two quoted cases as `PASS` and the real comment as `SKIP`.
- Smoke structural probes over temp copies of `tests/smoke/smoke.md`:
  - Current document satisfied both embedded-fixture and top-level executable scans.
  - Removing the nested bash assertion and leaving prose outside a bash fence made the embedded-fixture check fail.
  - Replacing the top-level nested smoke command with a different asserted line that merely mentioned `mustmatch test nested-smoke.md | mustmatch` made the top-level check fail.
- `make smoke`: green; built and installed the wheel in an isolated venv and ran `tests/smoke/smoke.md` through the installed `mustmatch` entry point (`2 passed`).
- `./target/debug/mustmatch lint spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`: both `findings=0`.
- `./target/debug/mustmatch verify-matrix .march/design-final.md --repo-root .`: initially exposed a non-shipped artifact reference to embedded `nested-smoke.md`; after bounded wording repair it passed.

## Exploratory Verification — change-aware probes tried; high-signal probes; noisy/not-worth-repeating probes; recommended improved tests (`spec`, `test`, `lint`, `gate`, `verify-group`, docs/help, FAQ watching, experiment/harness); agent/tool-cost friction if applicable

- High-signal probes were chosen from the diff: masked runner pipelines, quoted-`#` shell-comment detection, executable-fence-aware smoke structure, and the installed-wheel smoke path.
- The temp failing fixture was the strongest probe because it proved both the old positive pipeline false-negative and the new absence assertion's failure behavior on the same input.
- The top-level smoke replacement probe was high-signal because it recreated the code-review concern: prose/mentions inside an executable bash block must not satisfy the nested-smoke command sentinel.
- Noisy/not worth repeating: replacing the nested smoke assertion with arbitrary invalid text *inside an existing bash fence* still looks like executable structure to the structural scan; this is not the prose-only false negative targeted by this ticket, and `make smoke` catches invalid executable bash content directly.
- Recommended durable improved tests: already landed as shipped specs in this ticket. No additional spec/test/lint/gate/verify-group/FAQ/experiment issue is needed.
- Agent/tool-cost friction: the Makefile remains the cheapest discovery path. Direct source-tree probes need `PATH="$PWD/target/debug:$PATH"` so nested `mustmatch` calls use the just-built binary; this is existing repo behavior and is encoded in `make spec`.

## Edge Cases Tested — specific cases, results

- Empty/zero-style protected output: full canonical fixture absence check remains green on the real fixture and red on injected failure output.
- Malformed/intentional failure: temp failing fixture produced `FAIL`/`failed` and the absence assertion failed.
- Boundary values: quoted `#` in single and double quotes both ran; a leading real shell comment with `| mustmatch` skipped.
- Stale/prose smoke state: prose-only embedded fixture and prose-like top-level command replacements failed the structural checks.
- Release integration: installed-wheel smoke passed through `make smoke`.

## Spec Audit — specs reviewed, gaps found, counts before/after, spec-only result

- Reviewed changed shipped specs: `spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`, plus `tests/smoke/smoke.md` and the Makefile smoke/spec targets they document.
- Proof locations exist in repo:
  - `spec/14-authoring-and-self-test.md::Runner self-test`
  - `spec/14-authoring-and-self-test.md::Quoted hash assertion detection`
  - `spec/15-release-smoke.md::Smoke document is self-contained`
- `spec-only` result: green, `82 passed, 2 skipped`.
- Full-blocking later repeated `make spec` with the same green `82 passed, 2 skipped` result.
- No coverage gap blocks approval. The ticket's introduced behavior is contract hardening in the changed spec files, and the adversarial probes show the named false negatives fail.
- Verify authored no new shipped-spec assertions. `git diff main..HEAD -- spec/*` is still the design/code-review-authored spec diff only.

## Verify Group — `lane: verify` entries exercised (each: assertion, red_command, observed_status); operator-pending list explicit if credentials unavailable

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator-pending list is empty.

## Regression Results — existing features verified

- `make smoke`: green installed-wheel release smoke (`2 passed`).
- `mustmatch --help`, `mustmatch test --help`, and `make help`: output remains accurate for commands/options/targets; no help text change was required.
- Public-doc archaeology grep with `.march/**` excluded returned no matches.
- `mustmatch lint` for both changed specs returned `findings=0`.
- `mustmatch verify-matrix .march/design-final.md --repo-root .` passed after the bounded artifact wording repair.

## Test Suite — full-blocking result

- Full-blocking profile was run exactly once as `make lint && make test && make spec`: green.
- `make lint`: green (`cargo fmt --check` + `cargo clippy -- -D warnings`).
- `make test`: green (31 CLI unit tests, 5 runner error-path integration tests, 48 core tests, doc-tests green).
- `make spec`: green (`82 passed, 2 skipped`).

## Documentation — parity audit of docs/help/examples

- `README.md` remains accurate: it points to `spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`, and documents `make smoke` as the installed-wheel smoke gate.
- `mustmatch --help`, `mustmatch test --help`, and `make help` remain in parity with the shipped commands/targets.
- `tests/smoke/smoke.md` remains unchanged and is structurally aligned with `spec/15-release-smoke.md`.
- Fixed one non-shipped March artifact wording issue in `.march/design-final.md`: bare backticked embedded `nested-smoke.md` made `verify-matrix` look for a nonexistent repo file. It now references `tests/smoke/smoke.md`, and `verify-matrix` passes.

## Issues Found and Fixed — fixes + proof

- Fixed `.march/design-final.md` wording so embedded fixture references resolve through `tests/smoke/smoke.md` instead of a nonexistent top-level `nested-smoke.md`.
  - Proof: `./target/debug/mustmatch verify-matrix .march/design-final.md --repo-root .` now reports both references OK.
- No bounded runtime defects or shipped-doc mismatches were found.

## Issues Filed — list with paths

None.

## Planning Updates — concrete issues filed or FAQ watching proposal (or "none")

None. No recurring unautomated constraint remained after verification.

## UX Quality — CLI/UI assessment (if applicable)

- The changed interface is agent/user-facing executable documentation. The spec prose remains understandable and the assertions target structural behavior rather than exact counts.
- CLI/help output remains concise and discoverable.
- No performance regression was observed; added checks are local fixture runs and small scans, and full-blocking passed normally.

Issues filed: 0
