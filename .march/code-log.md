# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Inspect existing parser/runner/context/named-run code paths and verify local preconditions — done
3. Implement minimal parser retention, fixture validation/materialization, section/row/context cwd lifetime, and substitution — done
4. Update design-named docs and run focused/spec gates — done
5. Diff audit, cleanup, and final proof recording — done

## Resume State
- Last completed batch: Diff audit, cleanup, and final proof recording
- Files edited so far: `.march/code-log.md`, `crates/mustmatch-core/src/parser.rs`, `crates/mustmatch-cli/src/runner.rs`, `crates/mustmatch-cli/src/context.rs`, `docs/05-directives.md`, `docs/15-embedded-files.md`, `docs/index.md`, `README.md`
- Existing partial edits: preserve runtime/docs changes
- Tests passing: yes — final `cargo fmt && make spec && make test && make lint` is green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped-contract assertions in `spec/*.md`
- New CLI flags or config surface
- Binary fixtures or reading files back as assertions
- Python runner behavior unless mechanically required by shared docs/tests
- Input validation or defensive behavior beyond `file=` path safety and directive conflicts named by design
- Live-service or credential-backed verify behavior; `.march/contract-red-check.json` has no verify-lane entries

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist 0/22
- Read `AGENTS.md` and `CLAUDE.md`; located shipped specs under `spec/*.md`
- `git fetch origin main && git rebase origin/main` — branch already up to date, no conflicts
- Read `.march/design-final.md`, `.march/contract-red-check.json`, `.march/ticket.md`, and prior `.march/code-log.md`
- `make spec` — red as expected: two failures in `spec/02-rust-runner.md` embedded fixture cases
- Read mustmatch and rust-standards skills for spec/runtime boundaries and Rust quality rules
- Searched existing code with `rg` for `file=`, `default_cwd_for`, `resolve_scoped`, `TempDir`, `each_row`, `substitute_with_row`, context lines, and section handling
- Read `crates/mustmatch-cli/src/{runner,context,named_runs}.rs`, `crates/mustmatch-core/src/parser.rs`, `spec/02-rust-runner.md`, and `tests/fixtures/rust-runner/embedded-files.md`
- Verified preconditions: fixture/config files exist, `demo` context has `cwd={tmp}`, helper-tool is executable, `cargo` and `uv` are available, and no verify-lane credentials/services are required
- Implemented parser retention for fenced blocks carrying `file=` so non-executable text languages remain available to the Rust runner
- Implemented runner-owned section tempdirs, row roots beneath section roots, `file=` path validation/conflict validation, and materialization of earlier same-section fixture files before consuming blocks run
- File content uses existing `NamedRuns::substitute_with_row`; row-scoped fixture blocks use existing table selection and row labels stay on consuming bash cases only
- Removed now-unused runner path storage and `ContextRegistry::resolve` wrapper as mechanical warning cleanup after switching all runner calls to `resolve_scoped`
- `cargo fmt && cargo check -p mustmatch-cli` — green
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner/embedded-files.md` — green, 7 passed with expected row labels
- `make spec` — green, 8 passed; both embedded fixture check-lane entries now pass
- Added unit diagnostics for `file=` unsafe paths (empty, parent traversal, absolute) and directive conflict with `expect=`; parser unit proves `json file=config.json` is retained with content/directive
- Updated design-named docs: `docs/15-embedded-files.md`, `docs/05-directives.md`, README documentation map/feature summary, and `docs/index.md`
- `cargo test -p mustmatch-core -p mustmatch-cli` — green: 48 core tests and 10 CLI tests passed
- `make spec` after docs — green, 8 passed
- `make test` (focused profile per `.march/validation-profiles.toml`) — green: pytest 63 passed plus cargo tests green
- `make lint` — green: ruff, cargo fmt --check, and cargo clippy -- -D warnings passed
- Final `cargo fmt && make spec && make test && make lint` — green: specs 8 passed; focused `make test` pytest 63 passed plus cargo tests green; lint green
- `git status --short --branch` — only intended source/docs plus `.march/code-log.md` modified; new `docs/15-embedded-files.md` is intentionally untracked pending commit/stage by March
- `git diff --check` — clean

Proof results:
- Check-lane contract: `make spec` green, including both `spec/02-rust-runner.md::Run embedded fixture files` entries from `.march/contract-red-check.json`.
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green.
- Verify lane: no `lane: verify` entries in `.march/contract-red-check.json`.

Over-edit audit:
- `parser.rs` change is load-bearing to retain non-executable `file=` blocks for runner materialization.
- `runner.rs` changes are load-bearing for design-named file block silence, path/conflict diagnostics, section-stable roots, row-root isolation, table-selected row fixture rendering, context-cwd materialization, and reuse of existing named-run substitution.
- `context.rs` removal of the unused `resolve` wrapper and runner path field removal are mechanical consequences of switching runner execution to `resolve_scoped`/section roots; they prevent lint warnings without changing public behavior.
- Docs/README edits are confined to the design-named documentation updates for `file=` behavior and the documentation map.
- No spec assertions, CLI flags, Python runner behavior, off-path refactors, or speculative validation were added.

Diff-size audit:
- Minimal runtime work crosses parser retention, runner classification, cwd lifetime, materialization, path safety, row selection, context composition, and diagnostics; the `runner.rs` diff is larger than the fixture happy path but each category is named by `.march/design-final.md`.
- Total diff remains within the expected scope for those coupled surfaces plus design-required docs.
- No adjacent fixes were needed.

## Deviations from Design
- None
