# Code Review Log — 026 un-foolable self-test contracts

## Critique Summary

Read `AGENTS.md` and `CLAUDE.md`; the shipped BDD/spec layer is `spec/*.md`, run by `make spec`. Read `.march/ticket.md`, `.march/design-draft.md`, `.march/design-final.md`, `.march/contract-red-check.json`, `.march/code-log.md`, and the full diff against `main`.

Local gates run during review:

- `make spec` — green (`82 passed, 2 skipped`) before repair.
- `make spec` — green (`82 passed, 2 skipped`) after repair.
- `make test` — green.
- `make lint` — green.
- `git diff --check` — clean.

## Design Completeness Audit

Every design-final implementation item has a corresponding landed change:

- Full canonical runner fixture failure-absence assertion landed in `spec/14-authoring-and-self-test.md::Runner self-test`.
- Local quoted-hash/comment-boundary fixture landed in `spec/14-authoring-and-self-test.md::Quoted hash assertion detection`.
- Public-doc archaeology grep now excludes `.march/**` in `spec/14-authoring-and-self-test.md`.
- Release-smoke self-containment check was rewritten as executable-fence-aware scans in `spec/15-release-smoke.md`.
- No Rust code, Makefile target, README/help text, release workflow, or `tests/smoke/smoke.md` change landed, matching the design scope.

## Spec Traceability

### Forward

All four proof-matrix entries have landed assertions at their named locations:

1. `spec/14-authoring-and-self-test.md::Runner self-test` full-fixture absence block: `mustmatch test -v ../tests/fixtures/rust-runner 2>&1 | mustmatch not like "FAIL\nfailed"`.
2. `spec/14-authoring-and-self-test.md::Quoted hash assertion detection`: embedded `quoted-hash.md` fixture plus verbose `PASS`/`SKIP` assertion.
3. `spec/15-release-smoke.md::Smoke document is self-contained` embedded-fixture scan: tracks the quadruple fixture fence and nested bash fence before emitting structural sentinels.
4. `spec/15-release-smoke.md::Smoke document is self-contained` top-level executable scan: now emits distinct sentinels for the installed stdin assertion and nested smoke test command.

### Reverse

Scoped shipped-spec diff with `git diff main..HEAD -- 'spec/*'` and rechecked the working-tree repair with `git diff main -- 'spec/*'` before commit.

- New/modified `spec/14` failure-absence and quoted-hash assertions trace directly to proof-matrix rows.
- Modified `spec/14` archaeology grep exclusion is design-final scope item 4: a mechanical/public-doc scoping repair, not a new behavior assertion.
- Replaced `spec/15` smoke scan traces to the two proof-matrix smoke rows.
- No invented assertion, silently relaxed assertion, or silently removed assertion remains.

## Edit Discipline Audit

Minimal shipped-spec implementation size was the four design-named spec assertions plus the `.march/**` public-doc grep exclusion. Actual shipped-spec diff is limited to `spec/14-authoring-and-self-test.md` and `spec/15-release-smoke.md`; no runtime code changed.

The review repair changed only the defective top-level smoke scan output from raw command lines to semantic sentinels. Removing those four edited lines restores the false negative, so the change is within minimal-fix discipline. No over-edit defects remain.

## Defect Register

| # | Category | Lintable | Description |
|---|----------|----------|-------------|
| 1 | weak-assertion | no | `spec/15` top-level smoke scan printed raw command lines; a replacement `printf` line mentioning `mustmatch test nested-smoke.md | mustmatch` could satisfy both expected substrings after the executable nested smoke command was removed. Fixed by emitting distinct structural sentinels for the stdin assertion and nested smoke test command. |

## Repair Log

- Reproduced the weak assertion with a temp copy of `tests/smoke/smoke.md`: replaced the executable nested `mustmatch test nested-smoke.md | mustmatch ...` block with a `printf` line that merely mentioned that text; the pre-repair assertion still exited `0`.
- Edited `spec/15-release-smoke.md` so the top-level scan prints `top-level stdin assertion` and `top-level nested smoke test command` only from their respective matched executable lines.
- Re-ran the adversarial temp-copy probe; the repaired assertion now exits nonzero when the nested smoke command is removed.
- Post-fix collateral scan: no dead code, unused variables/imports, resource cleanup issues, stale messages, or shadowed variables were introduced. The awk state variables remain used and scoped to their scans.

## Residual Concerns / Issues

No out-of-scope issue file was opened. Residual non-blockers noted only for future maintainers: the smoke structure checks intentionally key off Markdown fence/command shape, so a future smoke-document rewrite should update the structural sentinels while preserving the same behavior.
