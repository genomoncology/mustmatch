# Investigation Notes — 026 un-foolable self-test contracts

## Code Path Trace

- `make spec` builds `crates/mustmatch-cli` and runs `PATH="$PWD/target/debug:$PATH" ./target/debug/mustmatch test spec/ README.md` per `Makefile:12-16`; the shipped BDD contract is `spec/*.md` plus README.
- Bash spec blocks flow through `MarkdownRunner::run_block` in `crates/mustmatch-cli/src/runner.rs`: `include_block` includes all `bash` fences, `run_block` skips a bash block only when `bash_block_has_mustmatch_pipe` returns false, and `run_bash_block` executes with `run_bash` then treats nonzero `exit_code` as `FAIL ... bash block exited ...`.
- `crates/mustmatch-cli/src/process.rs::run_bash` shells scripts as `bash -c "set -e\n{script}"`; it intentionally does not set `set -o pipefail`. Therefore `mustmatch test failing.md | mustmatch like "failed"` exits from the right-hand assertion and can mask the nonzero left-hand runner if the failure output contains the asserted text.
- The runner prints block failures as `FAIL ...` on stderr and the aggregate summary as `N failed` on stdout in `runner.rs::print_summary`. A spec-level absence assertion must merge streams (`2>&1`) and assert `not like "FAIL\nfailed"` so either a failed block line or failed summary makes the outer bash block fail.
- The current canonical self-test in `spec/14-authoring-and-self-test.md::Runner self-test` positively asserts PASS lines for `../tests/fixtures/rust-runner`; it does not yet pair that same full fixture run with an absence-of-failure assertion. The existing absence check targets only `embedded-files.md`, so failures in `runner.md` or `table-scenarios.md` could still be hidden by the positive summary assertion.
- Bash pipe detection is in `runner.rs::bash_block_has_mustmatch_pipe`, which strips only true shell comments via `code_before_shell_comment`. The parser tracks single/double quotes and escapes; a `#` inside quotes remains code, while a whitespace-delimited unquoted `#` begins a comment. A temp probe showed `printf 'literal # before pipe\n' | mustmatch like ...` runs as PASS, while a block containing only `# printf ... | mustmatch ...` is reported SKIP.
- `spec/15-release-smoke.md::Smoke document is self-contained` currently scans every line of `tests/smoke/smoke.md` with `awk '/file=|mustmatch test|\| mustmatch/{print}'`. Because this scan is whole-file and unanchored, prose mentioning `mustmatch test` can satisfy the check even if the executable nested command line is removed.
- `tests/smoke/smoke.md` has the executable shape the smoke contract should prove: a quadruple-fenced `markdown file=nested-smoke.md` embedded fixture, a nested bash assertion inside that fixture, a top-level stdin assertion bash fence, and a top-level `mustmatch test nested-smoke.md | mustmatch like "1 passed"` bash fence.

## Constraints

- AGENTS.md and CLAUDE.md both say mustmatch's observable contract is `spec/*.md`, run via `make spec`; internals and error paths use cargo tests. This ticket is self-test/spec-contract hardening, so the proof belongs in `spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`.
- The ticket explicitly rejects runner-wide `set -o pipefail`; changing `run_bash` would alter every consumer bash block and is out of scope. The masked-pipeline fix must be a spec-level absence assertion.
- Assertions must be semantic or structural, not trivia. The planned assertions avoid exact pass counts for the canonical fixture and smoke structure; the only count-like text left in smoke is the smoke document's own executable `mustmatch like "1 passed"` command, which is the installed smoke's user-visible assertion.
- Existing `spec/14` states documentation-only fences in the canonical `rust-runner` fixture must not surface as skipped cases. Adding a real-comment-only bash block to `tests/fixtures/rust-runner` would break that contract; the quoted-hash boundary fixture should therefore be local to `spec/14` (embedded `file=`) or isolated outside the canonical directory.
- No external services or credentials are involved. All planned checks are `lane: check` and run through `spec-only` / `make spec`.
- The smoke gate must not route package smoke through source-tree `make spec`; `Makefile::smoke` installs a wheel into an isolated venv and runs `mustmatch test tests/smoke/smoke.md`. The spec/15 rewrite only proves the smoke document's executable structure.
- Public repo constraints apply: no domain content, absolute local paths, or planning references in committed specs.

## Prior Art

- `4e60019 docs-as-spec: rebuild spec/ as executable tutorials; fix bare-filename cwd` introduced `spec/14-authoring-and-self-test.md` and the generic `tests/fixtures/rust-runner` self-test fixture. That file is the established home for runner self-tests.
- `3d85789 design: land failing contract for 020-release-smoke-test-verify-the-installed-wheel-before-tagging` introduced `spec/15-release-smoke.md`; `c70e984 Release smoke test: verify the installed wheel before tagging` added `tests/smoke/smoke.md`, `make smoke`, and release workflow smoke ordering.
- `5e08a1c Rust runner error-path hardening...` touched runner error-path internals and cargo integration tests only; it did not add shipped spec coverage for this ticket's self-test/smoke false-negative cases.
- Existing `spec/05-executable-markdown.md` already documents SKIP behavior for documentation-only or explicitly skipped blocks, so a small local fixture that visibly reports SKIP for a real shell-comment-only bash block is consistent with the public runner behavior.
- The `mustmatch` skill reinforces the same split: executable Markdown specs prove observable CLI/documentation behavior, while internals/error paths are language-native tests. Here the observable behavior is the self-test contract's ability to catch regressions.

## Hard Parts & Risks

- The masked-pass fix must catch failed blocks in any file under `../tests/fixtures/rust-runner`, not only the embedded-files fixture. Risk: a positive PASS assertion can still mask failure because the shell pipeline's exit comes from the right-hand assertion. Mitigation: add a companion `2>&1 | mustmatch not like "FAIL\nfailed"` for the full fixture directory.
- The smoke structural check must distinguish executable lines from explanatory prose without over-pinning counts or prose. Risk: another broad grep/awk over the whole file remains gameable. Mitigation: use anchored awk state over code-fence boundaries and assert only emitted structural sentinel/command lines from inside the embedded fixture fence and top-level executable bash fences.
- The quoted-`#` proof must cover both sides of the boundary. Risk: placing the real-comment case in the canonical fixture would add a SKIP and break the existing no-SKIP canonical self-test. Mitigation: embed a local fixture in `spec/14` whose expected output deliberately includes PASS for quoted hash and SKIP for real comment.
- Need avoid `set -o pipefail` or other runtime semantics changes; this design step should touch specs only unless the structural smoke assertion needs `tests/smoke/smoke.md` (current smoke document already has the required structure).
- Because these are improved green tests, a red result after authoring would indicate either a syntactic assertion bug or an already-present runtime/spec mismatch; do not fabricate failure.

## Scope: Required vs Deferred

Required:

- Add a full-canonical-fixture absence assertion in `spec/14-authoring-and-self-test.md` so failed runner output (`FAIL` or `failed`) fails the outer self-test even without pipefail.
- Add a quoted-hash/comment-boundary self-test fixture in `spec/14-authoring-and-self-test.md` proving quoted `#` before `| mustmatch` runs and true shell-comment `| mustmatch` remains skipped.
- Rewrite the `spec/15-release-smoke.md` self-containment assertion so it targets executable smoke structure: embedded `file=nested-smoke.md` fixture, nested executable assertion, top-level stdin assertion, and top-level nested `mustmatch test` command.
- Record all three as `lane: check` improved green ratchets if `spec-only` remains green.

Deferred/out of scope:

- Adding `set -o pipefail` to `run_bash` or changing global bash execution semantics.
- Changing `tests/smoke/smoke.md` unless investigation finds the structural assertion cannot prove the current executable shape (it can).
- Adding new CLI commands, directives, config, or runtime interfaces.
- Adding cargo tests for `code_before_shell_comment`; the ticket asks for self-test/spec coverage of shipped runner behavior, and the existing code path already satisfies the intended behavior.

## Test Coverage

- Current cargo tests in `crates/mustmatch-cli/tests/runner_error_paths.rs` cover missing explicit paths, bare-filename context root, invalid `--lang`, cyclic `uses=`, and setup secret redaction. They do not cover the quoted-hash comment parser boundary or smoke self-containment structure.
- Unit-level `runner.rs` tests exercise xfail, fixture scoping, each_row, lifecycle, and contexts, but no direct unit assertion for `bash_block_has_mustmatch_pipe` appears in the searched code.
- Manual probe of a temp failing fixture showed the weak positive pipeline exits `0` when it asserts `like "failed"`, while the proposed `not like "FAIL\nfailed"` absence assertion exits `1` for the same failing fixture.
- Manual probe of a temp quoted-hash fixture with the built source binary showed `PASS Quoted hash before pipe` and `SKIP Real shell comments stay documentation`, proving the current runtime already satisfies the boundary.
- Manual smoke structural probe over `tests/smoke/smoke.md` emitted the expected executable structure; removing only the executable `mustmatch test nested-smoke.md | mustmatch ...` line while leaving prose made the proposed assertion fail.

## Spec Coverage

- `spec/14-authoring-and-self-test.md` already proves canonical fixture PASS lines, no SKIP/skipped in the canonical fixture, pyproject context fallback, embedded-file no-failure output, and absence of old release-archaeology terms.
- Gap: no absence-of-failure assertion covers the full canonical `../tests/fixtures/rust-runner` directory, so a failure in `runner.md` or `table-scenarios.md` can be masked by the positive PASS pipeline.
- Gap: no shipped spec fixture proves the quoted-`#` before assertion pipe parser boundary, nor the intended skip for true shell-comment assertion lines.
- `spec/15-release-smoke.md` already proves the smoke file is tracked, no source-tree paths appear, Makefile smoke target is discoverable, and release workflow runs smoke before PyPI publish.
- Gap: the smoke self-containment check is whole-file/prose-gameable for `file=`, `| mustmatch`, and especially `mustmatch test`; it needs executable-fence-aware structural assertions.
- Planned proof entries are all `lane: check`, `class: structural`, and expected `green ratchet` because the runtime/smoke document already has the intended behavior and this ticket explicitly strengthens missing/weak proof.
