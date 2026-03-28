# Code Review Log

## Critique

### Design Completeness Audit

| Design item | Matching implementation | Status |
| --- | --- | --- |
| Add `is_closing_fence` and tighten the parser close-fence decision | [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L98) and [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L179) | Addressed |
| Add Rust test `keeps_inner_fence_with_info_inside_bash_block` | [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L333) | Addressed |
| Add Rust test `accepts_longer_closing_fence_with_trailing_spaces` | [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L359) | Addressed |
| Extend `docs/03-executable-documents.md` with `Nested Fences In Bash Blocks` | [`docs/03-executable-documents.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/docs/03-executable-documents.md#L25) | Addressed after review fix |
| Leave `docs/10-verify-matrix.md` and `docs/11-lint.md` unchanged | `git diff main..HEAD -- docs/10-verify-matrix.md docs/11-lint.md` shows no changes | Addressed |
| Create external quality bar artifact with required sections and content | `/home/ian/workspace/planning/mustmatch/planning/quality-bar.md` | Addressed |

Initial gap found:

- The first implementation of [`docs/03-executable-documents.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/docs/03-executable-documents.md#L25) proved the inner ` ```python ` line but did not prove that the generated fixture also contained the matching closing fence. That left the executable proof weaker than the approved design intent. I fixed this by appending the closing fence at runtime and asserting both fence lines are present.

Documentation and contract checks:

- The external quality bar lists the required smoke tests, fragile areas, security boundaries, and spec-health counts.
- [`README.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/README.md#L43) and [`CLAUDE.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/CLAUDE.md#L7) now document the required editable-package rebuild step before Python-side verification.
- A stale version line remained in [`CLAUDE.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/CLAUDE.md#L54) even though the package version is `0.0.4` in [`pyproject.toml`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/pyproject.toml#L7). I corrected it.

### Test-Design Traceability

| Proof matrix item | Matching test / proof | Result |
| --- | --- | --- |
| Inner fenced openings do not close the outer bash block | [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L333) `keeps_inner_fence_with_info_inside_bash_block` | Present |
| Longer closing fences with trailing spaces still close correctly | [`parser.rs`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/crates/mustmatch-core/src/parser.rs#L359) `accepts_longer_closing_fence_with_trailing_spaces` | Present |
| Pytest collection sees the new regression proof | [`docs/03-executable-documents.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/docs/03-executable-documents.md#L25), verified with `uv run python -m pytest docs/03-executable-documents.md --collect-only -q` | Present |
| The collected nested-fence example executes successfully | [`docs/03-executable-documents.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/docs/03-executable-documents.md#L25), verified with `uv run python -m pytest docs/03-executable-documents.md -q` | Present |
| Existing workaround specs still pass | `uv run python -m pytest docs/10-verify-matrix.md docs/11-lint.md -q` | Present |
| Full repo checks remain green | `make check`, `make test` | Present |
| Quality bar exists with required content | `/home/ian/workspace/planning/mustmatch/planning/quality-bar.md` plus content review | Present as manual artifact |

Blocking test-coverage gaps found: none after the doc-proof tightening.

### Quality Checks

- Implementation quality: parser change is narrow, reuses `parse_fence_start`, and preserves longer same-marker closing fences without duplicating parser logic.
- Duplication review: `rg` confirmed there was no existing reusable helper for close-fence validation; the new helper is the only such logic in the repo.
- Security review: no new shell, path, or query injection surface was introduced. The parser remains pure data parsing.
- Performance review: `is_closing_fence` is still O(line length) and called only while scanning markdown lines. The added work is negligible at repo scale.

## Fix Plan

1. Strengthen the executable-doc regression proof so the generated fixture contains both the nested opening fence and its closing fence, with assertions for both lines.
2. Correct the stale version line in `CLAUDE.md` while touching the same contributor doc.

## Repair

Applied fixes:

- Updated [`docs/03-executable-documents.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/docs/03-executable-documents.md#L29) to append the inner closing fence to the generated file and assert that both ` ```python ` and ` ``` ` are present.
- Updated [`CLAUDE.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/CLAUDE.md#L54) so the documented version matches [`pyproject.toml`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/pyproject.toml#L7).

### Post-Fix Collateral Damage Scan

- Dead code: none introduced. The docs change only strengthens assertions; the doc remains collected and executed. The `CLAUDE.md` change is purely textual.
- Unused imports or variables: none introduced.
- Resource cleanup conflicts: none introduced. The bash doc still removes the temp directory once and has no duplicated cleanup path.
- Stale error messages: not applicable; no error text changed.
- Shadowed variables: none introduced.

## Verification

- `cargo test -p mustmatch-core --lib` -> `30 passed`
- `uv run python -m pytest docs/03-executable-documents.md --collect-only -q` -> `Nested Fences In Bash Blocks` collected
- `uv run python -m pytest docs/03-executable-documents.md -q` -> `3 passed`
- `uv run python -m pytest docs/10-verify-matrix.md docs/11-lint.md -q` -> `6 passed`
- `make check` -> pass
- `make test` -> `33 passed in 4.66s`

## Residual Concerns

- The executable-doc proof still cannot place a literal standalone ` ``` ` line directly inside the outer triple-backtick markdown block without hitting the parser's intentionally out-of-scope indentation behavior. The runtime-generated closing fence is the strongest proof available within this ticket's scope.
- No out-of-scope issue files were needed from this review.

## Defect Register

| # | Category | Lintable | Description |
|---|----------|----------|-------------|
| 1 | weak-assertion | no | The initial `docs/03` regression proof only proved the inner opening fence and did not verify that the generated fixture also contained the nested closing fence. |
| 2 | stale-doc | no | [`CLAUDE.md`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/CLAUDE.md#L54) reported `0.0.2` while [`pyproject.toml`](/home/ian/workspace/worktrees/003-fix-rust-parser-nested-fence-bug/pyproject.toml#L7) and the rebuilt package were `0.0.4`. |
