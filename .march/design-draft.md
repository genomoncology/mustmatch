# Design Draft — 026 un-foolable self-test contracts

## Investigation Summary

`make spec` is the BDD/spec gate for this repo: the Makefile builds `crates/mustmatch-cli` and runs the built `mustmatch test spec/ README.md`. The observable contract therefore lives in `spec/*.md`, with `spec/14-authoring-and-self-test.md` covering runner self-tests and `spec/15-release-smoke.md` covering the installed-wheel smoke document.

The masked-pass path is a spec-contract weakness rather than a runtime defect for this ticket. `crates/mustmatch-cli/src/process.rs::run_bash` executes bash blocks as `set -e` without `set -o pipefail`, and the ticket explicitly rejects changing that global behavior. A self-test pipeline like `mustmatch test failing.md | mustmatch like "failed"` can exit green because the pipeline status comes from the right-hand `mustmatch`; a manual temp-fixture probe reproduced this. `crates/mustmatch-cli/src/runner.rs` prints failed block lines as `FAIL ...` and the summary as `N failed`, so a full-fixture `2>&1 | mustmatch not like "FAIL\nfailed"` catches the masked failure without changing runner semantics.

The quoted-hash path is in `runner.rs::bash_block_has_mustmatch_pipe` and `code_before_shell_comment`. The parser tracks single quotes, double quotes, and escapes before deciding whether `#` starts a shell comment. A manual probe using the current built binary showed that `printf 'literal # before pipe\n' | mustmatch like ...` runs and passes, while a block containing only `# printf ... | mustmatch ...` is skipped. This is already shipped behavior whose proof is absent/weak.

The smoke false negative is in `spec/15-release-smoke.md::Smoke document is self-contained`: it currently scans all of `tests/smoke/smoke.md` with `awk '/file=|mustmatch test|\| mustmatch/'`. Because the scan is not restricted to executable code-fence structure, explanatory prose can satisfy the `mustmatch test` requirement after deleting the actual nested smoke command. A manual probe that removed only `mustmatch test nested-smoke.md | mustmatch ...` from a temp copy made the proposed code-fence-aware assertion fail while prose remained.

Prior art confirms the file homes: `4e60019` introduced `spec/14` and `tests/fixtures/rust-runner`; `3d85789`/`c70e984` introduced `spec/15`, `tests/smoke/smoke.md`, `make smoke`, and release smoke workflow ordering. `5e08a1c` hardened runner error paths in cargo tests but did not add shipped spec coverage for these self-test false-negative cases.

## Architecture Decisions

### Minimal Slice

Change only the shipped executable specs needed to close the three false-negative gaps:

1. In `spec/14-authoring-and-self-test.md::Runner self-test`, add a companion absence assertion for the full canonical `../tests/fixtures/rust-runner` run: `mustmatch test -v ... 2>&1 | mustmatch not like "FAIL\nfailed"`.
2. In `spec/14-authoring-and-self-test.md::Quoted hash assertion detection`, add an embedded local Markdown fixture proving the quoted-`#`/real-comment boundary, then assert the current runner reports PASS for the quoted hash block and SKIP for the true shell-comment block.
3. In `spec/15-release-smoke.md::Smoke document is self-contained`, replace the broad whole-file scan with executable-structure checks that only emit anchors from the embedded fixture fence and top-level bash fences.

Deferred: no `run_bash` pipefail change, no new directive/CLI/config, no `tests/smoke/smoke.md` change unless the current executable structure cannot satisfy the stronger assertion (investigation showed it can), and no cargo-test expansion for parser internals in this ticket.

### Files and data paths

- `spec/14-authoring-and-self-test.md` changes are read by `mustmatch test spec/` under `make spec`. The new full-fixture absence assertion exercises `MarkdownRunner::run` over `tests/fixtures/rust-runner`, merges stdout/stderr from the nested runner, and checks the user-visible failure markers emitted by `runner.rs`.
- The local quoted-hash fixture in `spec/14::Quoted hash assertion detection` uses a `markdown file=quoted-hash.md` block. The section-scoped fixture file is materialized by the existing embedded-file machinery before the bash assertion in that section runs `mustmatch test -v quoted-hash.md`.
- `spec/15-release-smoke.md` continues to inspect `../tests/smoke/smoke.md`, but its awk filters become code-fence-aware: one assertion proves the embedded fixture fence contains a nested executable assertion pipe; the other proves top-level executable bash fences contain both the stdin assertion and the nested `mustmatch test nested-smoke.md` command.
- Docs/help/examples changing in the same ticket: the two spec files are themselves executable documentation. README/help text and `tests/smoke/smoke.md` stay unchanged because no shipped CLI behavior or smoke document content changes.
- Final green gate after code/spec hardening: `make lint && make test && make spec`. The design-step observation gate for these `lane: check` improved green ratchets is `spec-only` (`make spec`).

No new runtime interface is introduced. The design extends existing spec idioms already present in the repo: `mustmatch test ... | mustmatch like`, `not like` absence checks, embedded `file=` fixtures, and awk-based structural source inspections.

## Quality Analysis

- **Reuse** — Reuses existing spec files, embedded fixture support, `mustmatch test -v`, and `not like`; no new helper files/functions are needed.
- **Duplication** — Searched `spec/14`, `spec/15`, `tests/fixtures`, `tests/smoke`, and runner tests; no existing full-canonical-fixture failure-absence assertion, quoted-hash boundary fixture, or executable-fence-aware smoke structure proof exists.
- **Simplicity** — Smallest change is three spec assertions/fixtures; no runtime semantics change and no extra packaging path.
- **Separation of concerns** — Spec files prove user-visible self-test/smoke contracts; runner internals remain in Rust code/tests and are not edited here.
- **Performance** — Hot path is `make spec`; the added checks run local markdown fixtures and two small awk scans over one tiny smoke file. No external calls, subprocess loops over large trees, or full-repo scans beyond existing grep remain.
- **Data fidelity** — Downstream consumer is the release smoke gate: `tests/smoke/smoke.md` must retain embedded fixture, stdin assertion, and nested installed-binary `mustmatch test` command. The structural checks verify those fields/lines rather than silently accepting prose mentions.
- **Security** — Inputs are tracked repo Markdown only. Embedded fixture path is relative and handled by existing path-safety validation; awk scans do not execute smoke file contents.
- **Scope discipline** — Removed pipefail/runtime changes, cargo parser tests, smoke fixture rewrites, and CLI/help edits from scope because the ticket asks for self-test contract hardening and current runtime behavior already satisfies the intended assertions.

## Acceptance Criteria

- The full canonical runner fixture self-test fails if any nested runner output contains `FAIL` or `failed`, so an inner failed runner result cannot be masked by a positive right-hand pipeline assertion.
- The release smoke self-containment proof fails if the executable nested `mustmatch test nested-smoke.md | mustmatch ...` line is removed while prose remains.
- A shipped self-test fixture proves a bash command with a quoted `#` before `| mustmatch` runs and matches, while a true shell-comment line containing `| mustmatch` remains skipped.
- `spec-only` is green after the authored improved-green assertions; final build gate remains `make lint && make test && make spec`.

## Proof Matrix

| location | behavior assertion | class | lane | expected observation | docs/help/examples + final green gate |
|---|---|---|---|---|---|
| `spec/14-authoring-and-self-test.md::Runner self-test — canonical fixture absence assertion` | Full canonical runner self-test reports no `FAIL` lines and no `failed` summary, catching a nested runner failure that a positive pipeline could mask. | structural | check | green improved test | Spec text changes in `spec/14`; no help/README change. Gate: `spec-only` now, `make lint && make test && make spec` final. |
| `spec/14-authoring-and-self-test.md::Quoted hash assertion detection` | A quoted `#` before `| mustmatch` is treated as code and runs as PASS, while a true shell-comment assertion line is skipped. | semantic | check | green improved test | Spec text/embedded fixture changes in `spec/14`; no help/README change. Gate: `spec-only` now, `make lint && make test && make spec` final. |
| `spec/15-release-smoke.md::Smoke document is self-contained — embedded fixture structure` | The smoke document contains an executable embedded `nested-smoke.md` fixture with a nested bash assertion pipe, not just prose mentioning `file=` or `| mustmatch`. | structural | check | green improved test | Spec text changes in `spec/15`; `tests/smoke/smoke.md` unchanged because current structure is correct. Gate: `spec-only` now, `make lint && make test && make spec` final. |
| `spec/15-release-smoke.md::Smoke document is self-contained — top-level executable smoke commands` | Top-level executable bash fences include both the installed stdin assertion and the nested `mustmatch test nested-smoke.md` command, so prose alone cannot satisfy the nested-run requirement. | structural | check | green improved test | Spec text changes in `spec/15`; `tests/smoke/smoke.md` unchanged. Gate: `spec-only` now, `make lint && make test && make spec` final. |

## Improved Green Test Eligibility

All proof entries qualify as improved green tests:

1. The ticket explicitly asks to strengthen self-test/smoke contracts that can currently pass while the protected behavior is broken.
2. Investigation traced the current code paths (`run_bash`, `run_block`, `bash_block_has_mustmatch_pipe`, `code_before_shell_comment`) and current spec gaps (`spec/14` positive-only full fixture assertion, `spec/15` whole-file smoke scan, no quoted-hash fixture).
3. Manual probes showed the runtime/smoke document already satisfy the intended behaviors: full fixtures currently have no failures, quoted-hash runs while real comments skip, and the smoke document has the executable nested command.
4. The new assertions catch realistic regressions: failed nested fixture output, deletion of the executable smoke command while prose remains, and regressing the quote-aware comment parser.
5. Making these assertions red would require introducing false fixture failures, deleting correct smoke commands, or changing runtime semantics out of ticket scope. Therefore the right observation is `green ratchet`, not fabricated red.

## Design Landmine Check

- **Happy path, not degraded failure path:** The specs show self-tests and smoke document structure working. The only negative assertion checks absence of failure output from a normal full fixture run; it does not degrade credentials, unset env, or simulate a service failure.
- **Real services, not simulated:** No external service is touched. The smoke structure check inspects tracked local Markdown; the smoke gate itself remains the existing real installed-wheel `make smoke` path outside `spec-only`.
- **Trivia rejected:** No exact pass counts are pinned for the canonical fixture or smoke structure. Assertions name user-visible regression targets: nested failures, missing executable smoke line, and quote/comment pipe detection.
