# Code Log

## Execution Order
1. Orientation, rebase, contract review, and red-state confirmation — done
2. Preconditions, prior-art search, and parity evidence before deletion — done
3. Rust binary/metadata/gate cutover — done
4. Remove Python/PyO3 runtime surfaces and stale tests/docs references — done
5. Run check-lane spec gate plus focused/lint/test proof and final diff audit — done

## Resume State
- Last completed batch: Run check-lane spec gate plus focused/lint/test proof and final diff audit
- Files edited so far: `.march/code-log.md`, `.march/validation-profiles.toml`, `Cargo.toml`, `Cargo.lock`, `crates/mustmatch-cli/Cargo.toml`, `crates/mustmatch-cli/src/main.rs`, `crates/mustmatch-cli/src/runner.rs`, `crates/mustmatch-cli/src/lint.rs`, `crates/mustmatch-cli/src/verify_matrix.rs`, `Makefile`, `pyproject.toml`, `uv.lock`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `.github/workflows/test.yml`, `bench/clibench-commands.txt`, `spec/02-rust-runner.md`, `spec/03-rust-quality-commands.md`, `tests/fixtures/*`, removed Python/PyO3/docs paths and Python parity tests
- Existing partial edits: preserve all cutover edits
- Tests passing: yes — `make lint`, `make test`, `make spec`, `cargo test --locked`, and `uv build` are green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Editing `repos/biomcp` or any other repo outside this mustmatch worktree
- Adding new shipped-contract assertions
- New runner features, comparator/parser rewrites, parallelism, or `--deselect`
- New validation/input-hardening/logging/abstractions not required by the landed contract or design
- Keeping Python CLI/runtime/pytest plugin compatibility in this repo after cutover

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist 0/22
- Read `AGENTS.md` and `CLAUDE.md`; shipped contract specs are `spec/*.md`
- Read skills: `mustmatch`, `rust-standards`, `python-standards`
- `git fetch origin main && git rebase origin/main` — branch already up to date, no conflicts
- Read `.march/design-final.md`, `.march/ticket.md`, `.march/contract-red-check.json`, and stale seed `.march/code-log.md`
- `spec-only` — unavailable (`command not found`)
- `make spec` — red as expected before edits: 17 passed, 8 failed, all failures are check-lane entries from `spec/04-rust-binary-cutover.md`
- Verified preconditions: `cargo`, `uv`, `bash`, and `python3` are available; local `spec/*.md` files exist; consumer specs are readable for a temporary parity copy; no verify-lane credentials are needed
- Read `.march/validation-profiles.toml`; focused profile maps to `make test`
- Searched transitional surfaces with `rg`: existing Rust dispatch/help lives in `crates/mustmatch-cli/src/{main.rs,runner.rs,lint.rs,verify_matrix.rs}`; cutover surfaces are `Cargo.toml`, `Cargo.lock`, `crates/mustmatch-cli/Cargo.toml`, `pyproject.toml`, `Makefile`, docs/README/CHANGELOG, and Python/PyO3 source paths
- Parity before deletion: `uv run python -m mustmatch test spec/01-cli-assertions.md spec/02-rust-runner.md spec/03-rust-quality-commands.md` and `cargo run -q -p mustmatch-cli -- test ...` both exited 0 with identical output (`17 passed`; diff empty)
- Parity before deletion for a copied real consumer spec: copied `/home/ian/workspace/repos/march/spec/04-doctor-bootstrap.md` to `.march/parity/march-consumer/`; under an isolated temp March env, Python and Rust quiet runs both exited 1 with identical empty output (diff empty), recording pass/fail parity without editing the consumer repo
- Renamed Cargo bin target to `mustmatch`; updated Rust help/version text in top-level, `test`, `lint`, and `verify-matrix`
- Changed `make lint`, `make test`, and `make spec` to Rust-only gates; retired the public `check` target
- Updated `.march/validation-profiles.toml` so profiles no longer reference retired `make check` and `spec-only` maps to `make spec`
- Switched maturin metadata to binary packaging: `manifest-path = "crates/mustmatch-cli/Cargo.toml"`, `bindings = "bin"`; removed Python entry points/runtime metadata
- Removed `src/mustmatch/`, `src/sitecustomize.py`, `crates/mustmatch-python/`, `tests/test_doc_runner.py`, and Python/Rust parity tests that imported the deleted Python CLI
- Removed legacy `docs/` tree rather than leaving stale pytest/Python runtime guidance; retained executable contract is `spec/*.md`
- Updated README, changelog, AGENTS/CLAUDE orientation, CI workflow, bench commands, specs, and Rust-runner fixtures to the public `mustmatch` binary
- `uv lock` — refreshed lock after removing Python dev/test dependencies
- `cargo test` — green: 25 CLI unit tests, 48 core unit tests, doc-tests empty
- `cargo metadata --no-deps --format-version 1 | rg 'mustmatch-python|pyo3'` — no output
- `uv build` — green; built binary-wheel artifacts successfully, then removed `dist/`
- `make lint && make test && make spec` — green; final `make spec` reports 25 passed
- `cargo test --locked` — green, proving the manually cleaned lockfile is consistent
- `cargo run -q -p mustmatch-cli --bin mustmatch -- --help` — documents public `mustmatch` usage and subcommands
- `make -n spec` — shows `cargo run -q -p mustmatch-cli --bin mustmatch -- test spec/`
- `git diff --check` — clean
- `git status --short --branch` — only intended tracked changes/deletions; no normal untracked build artifacts

Proof results:
- Check-lane contract: `make spec` green (25 passed), including all 8 entries from `.march/contract-red-check.json` in `spec/04-rust-binary-cutover.md`.
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green.
- Lint: final `make lint` green.
- Packaging: `uv build` green with maturin bin bindings.
- Verify lane: `.march/contract-red-check.json` has no `lane: verify` entries; no `make verify` or credentials required.

Over-edit audit:
- Cargo/package/Makefile/pyproject/lock changes are load-bearing for the landed check-lane assertions and design decisions: public bin target, cargo-only gates, binary PyPI packaging, and no PyO3 workspace graph.
- Rust source edits are limited to user-facing command/help/version text named by design; dispatch, parser, comparator, runner semantics, lint, and verify-matrix behavior were not rewritten.
- Python/PyO3 source and Python-only tests were deleted because design explicitly requires no Python CLI/runtime, pytest plugin, PyO3 binding crate, or `import mustmatch` path in this repo.
- `docs/` deletion removes stale Python/pytest executable documentation; README/CHANGELOG/AGENTS/CLAUDE now point at `spec/*.md` and the Rust binary reality.
- Existing specs were updated only as a mechanical consequence of the design-named public binary cutover (`--bin mustmatch` and expected help names); no new shipped-contract assertions were authored.
- Fixture changes are mechanical consequences of the renamed binary now placed on PATH as `mustmatch`.
- No adjacent fixes were taken.

Diff-size audit:
- The large deletion count is expected and design-named: Python runtime, PyO3 crate, Python tests, and legacy docs are removed surfaces, not rewritten runtime.
- Non-deletion runtime diff is small: four help/version string edits and one Cargo bin-target rename.
- Metadata/gate/docs edits are limited to references that would otherwise advertise or execute the removed Python surfaces.

## Deviations from Design
- None
