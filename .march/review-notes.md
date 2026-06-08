# Design Review Notes — 026 un-foolable self-test contracts

## Phase 1 findings

### F1 — syntactic/pre-existing interaction: spec-only is red from the archaeology grep

- **Type:** syntactic-red / recorded-status mismatch
- **Evidence:** Independent `spec-only` equivalent (`make spec`, per `.march/validation-profiles.toml`) failed in `spec/14-authoring-and-self-test.md::Runner self-test` line 73. The existing archaeology grep scans tracked Markdown with `-- '*.md' spec/` and now matches committed `.march/design-draft.md` / `.march/investigation-notes.md` text (`removed`, `migrat...`, etc.).
- **Why it blocks:** `.march/contract-red-check.json` records all check-lane entries as `green, ratchet`, but the current authored tree is not green. This is not a behavioral red for any intended ticket assertion; it is a spec hygiene/pathscope problem exposed by adding tracked March artifacts.
- **Fix:** Narrow that existing grep to public Markdown/spec documentation by excluding `.march/**`, then rerun `make spec` and keep the four authored entries as green ratchets only if the suite is green.

### F2 — smoke embedded-fixture assertion is still prose-gameable inside the fixture

- **Type:** trivia/silent-green risk (prose-gameable structural assertion)
- **Evidence:** The new first `awk` in `spec/15-release-smoke.md` prints `nested assertion pipe` for any `| mustmatch` line while `in_fixture=1`, not only while inside the nested executable `bash` fence. If the executable nested assertion is deleted and prose inside the embedded `nested-smoke.md` fixture mentions `| mustmatch`, the assertion can still pass.
- **Why it blocks:** The proof-matrix row promises an executable embedded fixture with a nested bash assertion pipe, not a whole-fixture text scan. This is the same class of false negative the ticket is meant to eliminate.
- **Fix:** Track the nested triple-backtick bash fence inside the quadruple-fenced fixture (`in_nested_bash`) and only print the assertion sentinel for non-comment lines containing `| mustmatch` while both `in_fixture` and `in_nested_bash` are true.

## Audits completed

### Forward traceability

Every proof-matrix row has a landed assertion in the diff:

1. `spec/14-authoring-and-self-test.md::Runner self-test — canonical fixture absence assertion` → new full-fixture `mustmatch test -v ../tests/fixtures/rust-runner 2>&1 | mustmatch not like "FAIL\nfailed"` block.
2. `spec/14-authoring-and-self-test.md::Quoted hash assertion detection` → new embedded `quoted-hash.md` fixture plus verbose runner assertion requiring `PASS Quoted hash before pipe` and `SKIP Real shell comments stay documentation`.
3. `spec/15-release-smoke.md::Smoke document is self-contained — embedded fixture structure` → new embedded-fixture structural `awk` block; needs F2 repair before final.
4. `spec/15-release-smoke.md::Smoke document is self-contained — top-level executable smoke commands` → new top-level bash-fence structural `awk` block requiring the installed stdin assertion and executable `mustmatch test nested-smoke.md` line.

### Shape compliance

Changed files are `.march/*` artifacts and `spec/14-authoring-and-self-test.md` / `spec/15-release-smoke.md`. No behavior assertions were added to Rust unit tests, source code, README, or other non-spec files. No shape violations to move.

### Design landmines

- No check-lane assertion requires credentials, unsets environment, or degrades a service.
- No assertion mocks an external service; all checks are local deterministic CLI/spec behavior.
- All entries are correctly `lane: check`; no verify-lane rows are present.
- F2 is a local prose-gameability landmine, not an external-service grouping issue.

### Independent assertion classification and 5-question rubric

- **Runner full-fixture failure absence:** structural. Catches visible nested runner `FAIL` / `failed` output that a positive right-hand pipeline assertion can mask. Looser than exact counts and survives copy edits to pass labels.
- **Quoted hash assertion detection:** semantic. If quoted `#` lines are skipped, `PASS Quoted hash before pipe` disappears; if real comments are executed, `SKIP Real shell comments stay documentation` disappears. Not exact-count based.
- **Smoke embedded fixture structure:** intended structural, but currently defective per F2 because the pipe sentinel is not restricted to executable nested bash.
- **Smoke top-level executable commands:** structural. Requires executable top-level bash fences to contain both installed stdin assertion and the nested `mustmatch test nested-smoke.md` command; not satisfied by prose outside code fences.

### Spot-checked investigation

- `Makefile` `spec` target builds `mustmatch-cli` and runs `mustmatch test spec/ README.md` with `target/debug` first on `PATH`.
- `crates/mustmatch-cli/src/process.rs::run_bash` executes `bash -c "set -e\n{script}"` without `set -o pipefail`, matching the masked-pipeline analysis.
- `crates/mustmatch-cli/src/runner.rs` prints verbose `PASS`/`SKIP` labels and summary `failed` parts, and `bash_block_has_mustmatch_pipe` uses `code_before_shell_comment` that tracks single/double quotes before treating `#` as a shell comment.
- `tests/smoke/smoke.md` currently has the intended embedded `nested-smoke.md` fixture, nested assertion pipe, installed stdin assertion, and top-level `mustmatch test nested-smoke.md` command.

### Security and quality rubric

No new untrusted input or credentials are introduced. The design reuses existing spec runner behavior and fixture materialization, keeps runtime code untouched, and avoids exact pass counts. The required repairs are small spec-scope changes: exclude `.march/**` from a public-doc grep and make the smoke structure assertion truly executable-fence-aware.

## Phase 2 fix plan

- **F1 fix:** Edit the archaeology grep in `spec/14-authoring-and-self-test.md` to exclude `.march/**`; update the final design to call this out as a review repair to keep source/spec documentation checks from scanning March artifacts.
- **F2 fix:** Edit the first smoke-structure `awk` in `spec/15-release-smoke.md` to track the nested bash fence and only accept `| mustmatch` from executable nested bash code.
- **contract-red-check fix:** Rerun `make spec` after F1/F2 and update `.march/contract-red-check.json` so every check entry remains `green, ratchet` only after the repaired tree is actually green.
- **design-final fix:** Rewrite `.march/design-final.md` with explicit architecture decisions, acceptance criteria, proof matrix with canonical `green ratchet` evidence, and `## Code-Step Feasibility` (`feasible: yes`).
