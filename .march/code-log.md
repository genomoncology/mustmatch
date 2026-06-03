# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Inspect existing Rust runner/named-run/table code paths and verify local preconditions — done
3. Implement minimal row planning/substitution, table selection, row labels, and row-sensitive run/expect behavior — done
4. Update named docs/help/examples required by design and run focused/spec gates — done
5. Diff audit, cleanup, and final proof recording — done

## Resume State
- Last completed batch: Diff audit, cleanup, and final proof recording
- Files edited so far: `.march/code-log.md`, `crates/mustmatch-cli/src/runner.rs`, `crates/mustmatch-cli/src/named_runs.rs`, `docs/04-fixtures-and-tables.md`, `docs/12-named-runs.md`, `README.md`
- Existing partial edits: preserve runtime/docs changes
- Tests passing: yes — final `cargo fmt && make spec && make test && make lint` is green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped-contract assertions in `spec/*.md`
- Porting or changing Python `each_row`
- Adding new CLI flags or parser syntax
- Live-service or credential-backed verify behavior; `.march/contract-red-check.json` has no verify-lane entries
- Defensive validation or abstractions not required by landed assertions/design

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist 0/22
- Read `AGENTS.md` and `CLAUDE.md`; located shipped specs under `spec/*.md`
- `git fetch origin main && git rebase origin/main` — branch already up to date, no conflicts
- Read `.march/design-final.md`, `.march/contract-red-check.json`, `.march/ticket.md`, and prior `.march/code-log.md`
- `make spec` — red as expected: `Run bash table scenarios and outlines` fails
- `uv run mustmatch test spec/02-rust-runner.md -v` — focused verbose red matches contract-red details: bare row placeholders are treated as invalid named-run substitutions
- Read mustmatch and rust-standards skills for spec/runtime boundaries and Rust quality rules
- Searched existing code with `rg` for `each_row`, named-run templates, table helpers, `MarkdownRunner`, docs, and tests; existing extension points are `runner.rs`, `named_runs.rs`, and core `build_table_rows`/`get_table_for_block`
- Read `crates/mustmatch-cli/src/{runner,named_runs,context,process,expect,main}.rs`, `crates/mustmatch-core/src/{fixture,parser,lib}.rs`, and `Cargo.toml`
- Verified preconditions: table fixture/config files exist, helper-tool is executable, `cargo` and `uv` are available, and no verify-lane entries or external services are required
- Implemented row-aware `mustmatch-cli test` fan-out in `runner.rs`: `each_row` cases select tables, build core `TableRowData`, append row labels, and pass row context into bash/run/expect execution
- Implemented row-aware template substitution and row-sensitive named-run caching in `named_runs.rs`; bare `{{column}}` resolves against the current row and dotted `{{run.field}}` keeps the existing named-run lookup path
- `cargo fmt && cargo check -p mustmatch-cli` — green after resolving one borrow of `selected_stream`
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner/table-scenarios.md` — 8 passed with expected row labels
- `make spec` — green, 6 passed
- Updated `docs/04-fixtures-and-tables.md` from Python-first `each_row` to bash table scenarios, scenario outlines, table selection, coercion, and `str:` raw columns
- Updated `docs/12-named-runs.md` with the bare row-column vs dotted named-run namespace split
- Updated README `Executable Markdown` table example from Python `each_row` to bash `each_row`
- `make test` — green: pytest docs/README/tests 63 passed; cargo tests green (5 CLI, 47 core, 2 python)
- `make spec` — green after docs: 6 passed
- `make lint` — green: ruff, cargo fmt --check, and cargo clippy -- -D warnings passed
- Added a small explicit diagnostic for `expect=<id> each_row` without a matching row-aware run block, on the same scenario-outline code path
- Final `cargo fmt && make spec && make test && make lint` — green: specs 6 passed; focused `make test` pytest 63 passed plus cargo tests green; lint green
- `git status --short --branch` — only intended source/docs plus `.march/code-log.md` modified
- `git diff --check` — clean

Proof results:
- Check-lane contract: `make spec` green, including `spec/02-rust-runner.md::Run bash table scenarios and outlines`.
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green.
- Verify lane: no `lane: verify` entries in `.march/contract-red-check.json`.

Over-edit audit:
- `runner.rs` changes are load-bearing for design-named row fan-out, table lookup/precedence, row labels, run/expect lockstep, expected-output row substitution, and row-scoped default cwd.
- `named_runs.rs` changes are load-bearing for bare row-column substitution, preserving dotted named-run substitution, JSON scalar rendering, and row-sensitive result caching.
- Docs/README edits are the design-required public documentation updates for bash table scenarios and the row-vs-run namespace split.
- No off-path refactors, parser syntax changes, Python `each_row` changes, or new CLI flags were included.

Diff-size audit:
- Runtime diff is larger than the narrow happy-path fixture because row fan-out crosses case planning, bash block execution, named-run caching, output comparison, table lookup, and labels; those are all named by `.march/design-final.md`.
- Documentation changes are confined to the three files named by design.
- No adjacent fixes were needed.

## Deviations from Design
- None
