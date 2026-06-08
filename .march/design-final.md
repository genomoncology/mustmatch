# Design Final — 026 un-foolable self-test contracts

## Goal

Harden mustmatch's own shipped self-test and release-smoke contracts so they fail when the protected executable behavior disappears. This ticket is contract hardening only: it changes executable specs, not runner semantics, CLI directives, packaging behavior, or Rust internals.

## Architecture Decisions

### 1. Close the masked pipeline at the spec layer

`run_bash` intentionally executes bash blocks as `set -e` without global `pipefail`. Changing that would alter every consumer's bash-block semantics, so this ticket does not touch `crates/mustmatch-cli/src/process.rs`.

The self-test instead adds a companion absence assertion for the full canonical `../tests/fixtures/rust-runner` run:

- run the nested fixture with verbose output;
- merge stdout/stderr for the nested runner result;
- assert the output contains neither user-visible `FAIL` lines nor a `failed` summary.

That makes a failed inner runner result visible to the outer assertion even when a separate positive pipeline could otherwise pass from the right-hand `mustmatch` process.

### 2. Prove the quoted-hash/comment boundary with a local fixture

The shipped behavior is the runner's public Markdown execution boundary: a bash block with `| mustmatch` in real code runs, while a true shell-comment-only block remains documentation. The spec adds a section-local embedded `quoted-hash.md` fixture so the canonical `tests/fixtures/rust-runner` directory does not gain intentional `SKIP` output.

The fixture proves both sides together:

- `printf 'literal # before pipe\n' | mustmatch ...` reports `PASS`;
- `# printf ... | mustmatch ...` reports `SKIP`.

If either side regresses, the visible verbose labels change and the spec fails.

### 3. Make the smoke self-containment check executable-fence-aware

`spec/15-release-smoke.md` now inspects `tests/smoke/smoke.md` by Markdown fence state instead of scanning arbitrary lines. The contract proves two executable structures:

1. Inside the quadruple-fenced `markdown file=nested-smoke.md` fixture, a nested triple-backtick `bash` fence contains a non-comment assertion pipe to `mustmatch`. Prose inside the embedded fixture cannot satisfy this check.
2. Outside the embedded fixture, top-level executable bash fences contain both the installed stdin assertion and the executable `mustmatch test nested-smoke.md | mustmatch ...` command.

The package smoke document itself remains unchanged because it already has the required executable shape. The package smoke gate still runs through `make smoke`; `spec/15` only verifies the tracked smoke document cannot become prose-only.

### 4. Keep public-doc hygiene checks scoped to public docs

The existing archaeology grep in `spec/14` is retained, but review narrowed it to exclude `.march/**`. March design artifacts are not public CLI/spec documentation, and scanning them made `spec-only` red for workflow prose instead of shipped documentation drift.

## Implementation Scope

Change only:

- `spec/14-authoring-and-self-test.md`
  - add the full canonical fixture failure-absence assertion;
  - add the local quoted-hash/comment-boundary fixture and verbose assertion;
  - exclude `.march/**` from the existing public-documentation archaeology grep.
- `spec/15-release-smoke.md`
  - replace the prose-gameable whole-file smoke scan with two executable-fence-aware structural scans.
- `.march/contract-red-check.json`
  - record the repaired check-lane observations as green ratchets from `spec-only`.

Do not change Rust code, `tests/smoke/smoke.md`, Makefile targets, README/help text, or release workflow ordering.

## Acceptance Criteria

- A failure anywhere in the canonical `tests/fixtures/rust-runner` nested run produces visible `FAIL` or `failed` output that makes the outer self-test fail.
- A quoted `#` before `| mustmatch` is treated as executable command data and reports `PASS`; a true shell-comment line containing `| mustmatch` remains documentation and reports `SKIP`.
- The release smoke self-containment check fails if the nested executable assertion pipe inside the embedded fixture is removed, even if prose inside that fixture mentions `| mustmatch`.
- The release smoke self-containment check fails if the top-level executable `mustmatch test nested-smoke.md | mustmatch ...` command is removed, even if explanatory prose still mentions `mustmatch test`.
- `spec-only` (`make spec`) is green after the contract repairs; final code-step gate remains `make lint && make test && make spec`.

## Proof Matrix

| landed spec entry | behavior assertion | class | lane | red command | expected kind | expected observation | observed status |
|---|---|---|---|---|---|---|---|
| `spec/14-authoring-and-self-test.md::Runner self-test` full-fixture absence block | The canonical runner self-test output contains no `FAIL` line and no `failed` summary, so a nested fixture failure cannot be hidden by a positive right-hand pipeline assertion. | structural | check | `spec-only` | already-implemented | green ratchet | `green, ratchet` after review `make spec` |
| `spec/14-authoring-and-self-test.md::Quoted hash assertion detection` | A quoted `#` before `| mustmatch` runs as code and reports `PASS`, while a true shell-comment assertion line reports `SKIP`. | semantic | check | `spec-only` | already-implemented | green ratchet | `green, ratchet` after review `make spec` |
| `spec/15-release-smoke.md::Smoke document is self-contained` embedded-fixture scan | The embedded `nested-smoke.md` fixture contains a nested executable bash fence with a non-comment `| mustmatch` assertion pipe; prose inside the fixture cannot satisfy it. | structural | check | `spec-only` | already-implemented | green ratchet | `green, ratchet` after review `make spec` |
| `spec/15-release-smoke.md::Smoke document is self-contained` top-level executable scan | Top-level executable bash fences include both the installed stdin assertion and the executable nested `mustmatch test nested-smoke.md` command. | structural | check | `spec-only` | already-implemented | green ratchet | `green, ratchet` after review `make spec` |

There are no verify-lane rows and no expected-red behavior rows. These are improved green tests because the current runtime and smoke document already satisfy the strengthened contracts; the ticket closes proof gaps and false-negative risks.

## Quality Notes

- **Reuse:** Uses existing `mustmatch test -v`, embedded `file=` fixtures, `mustmatch not like`, and local `awk` source-structure checks already present in the spec style.
- **Simplicity:** No new helper scripts, directives, fixtures outside the spec section, or runtime abstractions.
- **Separation of concerns:** Public CLI/spec behavior stays in `spec/*.md`; parser internals and error paths remain Rust unit-test territory.
- **Performance:** Added checks run local Markdown fixtures and two small scans over one smoke file.
- **Security:** No credentials, network, or untrusted input. Embedded fixture paths are relative and validated by existing runner path-safety checks.
- **Spec quality:** Assertions avoid exact pass counts and exact advisory prose. They target named false negatives: masked nested failures, quoted-hash skip regression, real-comment execution regression, and prose-only smoke contracts.

## Code-Step Feasibility

- `feasible:` yes
- `reason:` The implementation is limited to already-authored spec contract edits and recorded check evidence. No runtime refactor, external service, or packaging change is required.
- `risk factors:` The smoke structure checks are intentionally tied to Markdown fence shape; future smoke-document rewrites may need to update the structural anchors while preserving the same behavior. The existing archaeology grep must continue to exclude workflow artifacts that are not public docs.
- `recommended action:` proceed to code
