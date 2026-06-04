# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Execution plan, precondition checks, and prior-art search — done
3. Implement smoke document, Makefile target/help, release workflow gate, and docs surfaces — done
4. Run smoke/spec/focused gates and fix minimal failures — done
5. Hygiene, over-edit audit, final code-log proof — done

## Resume State
- Last completed batch: Hygiene, over-edit audit, final code-log proof
- Files edited so far: `.march/code-log.md`, `tests/smoke/smoke.md`, `Makefile`, `.github/workflows/release.yml`, `AGENTS.md`, `README.md`
- Existing partial edits: preserve current implementation edits; all non-`.march` implementation files are staged so the landed `git ls-files` assertion reflects tracked state
- Tests passing: yes — `make lint`, `make test` (focused), `make spec`, default `make smoke`, and `SMOKE_WHEEL=... make smoke` are green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, or deleting shipped-contract assertions
- Changing Rust CLI runtime behavior; design calls for release/package infrastructure only
- Running the full `spec/` suite from an installed wheel
- Adding credentials, secrets, service integrations, or a broader release matrix
- Refactoring unrelated Makefile or workflow structure beyond the smoke gate path

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist read
- Read `AGENTS.md` and `CLAUDE.md`; behavioral specs are `spec/*.md`
- Read `.march/ticket.md`, `.march/design-final.md`, `.march/contract-red-check.json`, and stale seed `.march/code-log.md`
- `git fetch origin main && git rebase origin/main` — branch already up to date
- `spec-only` — unavailable on PATH; `.march/validation-profiles.toml` maps `spec-only` to `make spec`
- `make spec` — red as expected for all three check-lane entries in `spec/15-release-smoke.md`
- Preconditions checked: `cargo`, `uv`, `make`, `pyproject.toml`, `Makefile`, `.github/workflows/release.yml`, and `tests/` exist; no service credentials are required
- Prior-art search found existing `uv build`/publish targets, release artifact upload/download steps, and embedded fixture syntax; no new Rust helper/module is needed
- Implemented `tests/smoke/smoke.md`, `make smoke`, release workflow smoke-before-publish wiring, and AGENTS/README docs
- First `make spec` after edits was red only because the new smoke document needed to be staged for the landed `git ls-files` assertion; staged `tests/smoke/smoke.md` and `make spec` then passed
- First `make smoke` found the embedded fixture was in a different section than the nested `mustmatch test`; rewrote the smoke document so fixture and smoke commands share one section
- `make spec && make smoke` — green (`make spec`: 74 passed, 2 skipped; `make smoke`: installed wheel in throwaway venv and smoke document reported 2 passed)
- Verify lane: `.march/contract-red-check.json` has no `lane: verify` entries, so no credentials/operator-only checks are outstanding
- `make test` — focused profile green (`.march/validation-profiles.toml` maps focused to `make test`)
- `make lint` — green
- `SMOKE_WHEEL="$(find target/wheels -maxdepth 1 -type f -name '*.whl' | sort | head -n 1)" make smoke` — explicit wheel override green, no rebuild path exercised
- `git status --short --branch` — intended code/doc edits staged; `.march/code-log.md` modified but not staged
- Reviewed `git diff`/`git diff --cached` for intended changes only
- Structural smoke checks: smoke document contains `file=`, stdin `| mustmatch`, and `mustmatch test`; it has no `cargo`, `target/`, or parent-directory references; `make help` lists `smoke`
- Final `make spec && git diff --check` — green/clean
- `git diff --cached --check && git diff --check` — clean
- Final staged diff: `.github/workflows/release.yml`, `AGENTS.md`, `Makefile`, `README.md`, and `tests/smoke/smoke.md`; `.march/code-log.md` remains unstaged runtime artifact

Proof results:
- Check-lane contract: `make spec` green, including all three entries from `.march/contract-red-check.json`
- Focused profile: `make test` green
- Release smoke: default `make smoke` green and explicit `SMOKE_WHEEL=... make smoke` green
- Lint: `make lint` green
- Verify lane: no entries in `.march/contract-red-check.json`

Over-edit audit:
- `tests/smoke/smoke.md` is the design-named self-contained installed-binary smoke input and contains only the required embedded fixture, stdin assertion, and nested `mustmatch test`
- `Makefile` edits are limited to `.PHONY`, `smoke`, and help; the PATH check is load-bearing to prevent fallback to a non-installed binary
- Release workflow edits are limited to checkout/setup, artifact selection, and smoke-before-publish ordering required by design
- AGENTS/README edits only document the new release/package gate
- No Rust runtime, spec contract, or unrelated release logic was changed

Diff-size audit:
- Runtime code diff is zero Rust lines; this ticket is release infrastructure only
- Makefile target is longer than the smoke command itself because the design requires isolated install, optional `SMOKE_WHEEL`, missing-file validation, PATH precedence, and cleanup
- Workflow additions are bounded to the required publish-job ordering and host-compatible wheel selection
- No adjacent fixes were taken

## Deviations from Design
- None
