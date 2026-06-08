# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Execution plan, precondition checks, and prior-art search — done
3. Implement cell-aware `expected-missing` collection in `verify_matrix.rs` plus named unit tests — done
4. Run spec-only/focused/lint/test gates and fix minimal failures — done
5. Hygiene, over-edit audit, final code-log proof — done

## Resume State
- Last completed batch: Hygiene, over-edit audit, final code-log proof
- Files edited so far: `.march/code-log.md`, `crates/mustmatch-cli/src/verify_matrix.rs`
- Existing partial edits: preserve current minimal collector/test edits; `.march/code-log.md` remains an unstaged runtime artifact
- Tests passing: yes — `cargo test -p mustmatch-cli verify_matrix`, `make spec`, `make test` (focused), and `make lint` are green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped-spec assertions
- Redesigning verify-matrix output, JSON shape, CLI parsing, or path resolution
- Changing non-table backtick scanning behavior
- Broad Markdown table parsing beyond the minimal cell-aware collector named by design
- Adding service integrations, credentials, or unrelated validation behavior

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist read
- Read `AGENTS.md` and `CLAUDE.md`; behavioral specs are `spec/*.md`
- Read mustmatch build-step skill guidance
- `find spec -maxdepth 2 -type f -name '*.md'` — located spec files
- `git fetch origin main && git rebase origin/main` — branch already up to date
- Read `.march/ticket.md`, `.march/design-final.md`, `.march/contract-red-check.json`, and replaced stale seed `.march/code-log.md`
- `make spec` — red as expected for the two check-lane behavioral entries in `spec/13-verify-matrix.md::Escaping expected-value paths` (six failed blocks because each entry has run/contains/not-contains assertions)
- Preconditions checked: `crates/mustmatch-cli/src/verify_matrix.rs`, `spec/13-verify-matrix.md`, `Makefile`, `cargo`, `make`, and `mustmatch` are present; no external services or credentials are required
- Prior-art search: `crates/mustmatch-cli/src/verify_matrix.rs` already has `TABLE_ROW_RE`, `CODE_RE`, `looks_like_repo_path`, `TableRef`, `collect_table_refs`, and resolver tests; `spec/13-verify-matrix.md` already contains the landed `expected-missing` authoring example
- Edited `crates/mustmatch-cli/src/verify_matrix.rs`: `collect_table_refs` now captures the table row body, splits cells with the existing minimal table model, and skips only a code span whose same-cell prefix ends with `expected-missing` after trimming whitespace
- Added unit coverage in `verify_matrix.rs` for marker binding, same-cell unmarked references after an escaped path, and unescaped missing-reference preservation
- `cargo test -p mustmatch-cli verify_matrix` — green (7 passed)
- `make spec` — green (80 passed, 2 skipped); expected-red check entries now pass and escaped paths are omitted from JSON/human output
- Verify lane: `.march/contract-red-check.json` has no `lane: verify` entries, so no `make verify`/credential-backed operator check is outstanding for this ticket
- Docs/scripts check: `rg` found the landed `expected-missing` contract only in `spec/13-verify-matrix.md`; no help text, README, scripts, or CLI output changes were needed beyond preserving the landed spec
- `git diff --name-only` — only `.march/code-log.md` and `crates/mustmatch-cli/src/verify_matrix.rs` changed; no shipped spec assertions were edited
- `make test` — focused profile green (`.march/validation-profiles.toml` maps focused to `make test`; 31 CLI tests, 48 core tests, doc-tests green)
- `make lint` — green (`cargo fmt --check` + `cargo clippy -- -D warnings`)
- `git diff --check` — clean
- Final `make spec` — green (80 passed, 2 skipped)
- `git status --short --branch`, `git diff --name-only`, `git diff --cached --name-only`, `git ls-files --others --exclude-standard` — only intended unstaged changes are `.march/code-log.md` and `crates/mustmatch-cli/src/verify_matrix.rs`; no staged files and no untracked build artifacts

Proof results:
- Check-lane contract: `make spec` green, including both entries from `.march/contract-red-check.json`
- Focused profile: `make test` green
- Lint: `make lint` green
- Verify lane: no entries in `.march/contract-red-check.json`

Over-edit audit:
- Collector changes are limited to the design-named path: table row body extraction, per-cell splitting, and a same-cell immediate-prefix `expected-missing` skip before reusing existing `looks_like_repo_path`/`TableRef` behavior
- Unit tests cover only design-named runtime edges: escaped path omission with real `README.md`, same-cell unmarked path preservation, and unescaped missing-reference preservation
- No CLI parsing, output shape, resolver, docs, scripts, or shipped-spec assertions were changed

Diff-size audit:
- Minimal runtime fix required changing the collector loop from row-wide scan to cell-aware scan; the implementation delta is confined to that loop
- Added unit-test lines are the design-requested internal proof for marker binding and true-positive preservation
- No adjacent fixes were taken

## Deviations from Design
- None
