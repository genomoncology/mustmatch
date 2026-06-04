# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Execution plan, precondition checks, and prior-art search — done
3. Minimal docs/fixture/spec cleanup named by design — done
4. Minimal parser/runner and internal unit-test update — done
5. Gates, focused profile, hygiene grep, and diff audit — done

## Resume State
- Last completed batch: Gates, focused profile, hygiene grep, and diff audit
- Files edited so far: `.march/code-log.md`, `.march/verify-log.md`, `CHANGELOG.md`, `README.md`, the design-named deleted spec, `tests/fixtures/rust-runner/runner.md`, `tests/fixtures/rust-runner/table-scenarios.md`, `crates/mustmatch-core/src/parser.rs`, `crates/mustmatch-core/src/fixture.rs`, `crates/mustmatch-cli/src/runner.rs`
- Existing partial edits: preserve current minimal edits
- Tests passing: yes — `make lint`, `make test`, and `make spec` are green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding or relaxing shipped-contract assertions beyond deleting the design-named obsolete spec file
- Touching build tooling identifiers explicitly preserved by the design
- New features, flags, validation, logging, helper modules, or broad refactors
- Service or credential work; the contract file has no service-lane entries

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist read
- Read `AGENTS.md` and `CLAUDE.md`; shipped contract specs are `spec/*.md`
- `git fetch origin main && git rebase origin/main` — branch already up to date
- Read `.march/design-final.md`, `.march/contract-red-check.json`, `.march/ticket.md`, and seed `.march/code-log.md`
- Read mustmatch skill guidance for executable documentation discipline
- `spec-only` — unavailable on PATH; profile config maps it to `make spec`
- `make spec` — red as expected before edits: `spec/02-rust-runner.md::Run a documentation fixture` and `spec/02-rust-runner.md::Tracked Markdown describes current behavior` failed; remaining spec cases passed
- Preconditions checked: `cargo`, `uv`, `git`, `spec/02-rust-runner.md`, rust-runner fixture, README, and changelog are present; no service credentials are required
- Prior-art search found existing selection in `parse_markdown`, case inclusion in `MarkdownRunner::include_block`, explicit directive skip handling in `run_block`, and parser/unit tests on the same path; no new helper/module needed
- Edited current-state docs and fixtures: clean changelog capabilities entry, direct install wording, neutral documentation-only fixture fence, and the design-named spec file deletion
- Cleaned tracked stage notes so the tracked Markdown hygiene assertion evaluates the repo rather than stale March notes
- Updated parser selection to collect only supported runner block classes; updated runner inclusion to drop the language-named branch while leaving explicit skip directive and non-asserting bash behavior intact
- Updated internal unit fixtures on the changed parse path from an ordinary language fence to supported shell examples
- Hygiene grep with the landed term pattern over tracked Markdown/spec surfaces — no output after edits
- `make lint` — green
- `make test` — green
- `make spec` — green: 19 passed; both check-lane entries now pass
- Final focused profile (`make test`) — green
- Documentation fixture smoke: `cargo run -q -p mustmatch-cli --bin mustmatch -- test -v tests/fixtures/rust-runner` reports 27 passes and no skip lines
- Reviewed README/changelog and reran hygiene grep; docs/examples match current behavior
- `git diff --check` — clean
- `git status --short --branch` — only intended tracked edits/deletion
- Service lane: `.march/contract-red-check.json` has no entries requiring service credentials or operator-only exercise

Proof results:
- Check-lane contract: `make spec` green, including both entries from `.march/contract-red-check.json`
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green
- Lint: final `make lint` green
- Service lane: none in `.march/contract-red-check.json`

Over-edit audit:
- Parser and runner edits are exactly the named behavior change: ordinary non-runner fences stop entering the executed case list, while explicit skip and supported block handling remain intact
- Docs/fixture edits are limited to named current-state surfaces and the neutral documentation-only fixture example required by design
- Tracked stage-note cleanup is load-bearing for the landed tracked-Markdown hygiene assertion
- Unit fixture edits are mechanical consequences of the parser selection change
- No adjacent fixes were taken

Diff-size audit:
- Runtime code diff is five lines plus two internal fixture updates, matching the small behavior change
- Larger text deletion is the design-named obsolete spec and stale tracked notes needed for hygiene
- Docs and fixture prose edits are bounded to named surfaces

## Deviations from Design
- None
