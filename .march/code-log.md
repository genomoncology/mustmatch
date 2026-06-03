# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Inspect existing Python lint/verify-matrix implementation, Rust CLI routing/help patterns, fixtures, and local preconditions — done
3. Implement Rust CLI routing plus lint and verify-matrix modules with JSON/exit parity — done
4. Add focused Rust unit/parity coverage for helper behavior and error paths — done
5. Update design-named docs/help surfaces and run spec/focused/lint/test gates — done
6. Diff audit, cleanup, and final proof recording — done

## Resume State
- Last completed batch: Diff audit, cleanup, and final proof recording
- Files edited so far: `.march/code-log.md`, `Cargo.lock`, `README.md`, `crates/mustmatch-cli/Cargo.toml`, `crates/mustmatch-cli/src/main.rs`, `crates/mustmatch-cli/src/lint.rs`, `crates/mustmatch-cli/src/verify_matrix.rs`, `crates/mustmatch-cli/tests/quality_parity.rs`, `docs/10-verify-matrix.md`, `docs/11-lint.md`
- Existing partial edits: preserve runtime/docs/test changes
- Tests passing: yes — final `make spec && make test && make lint` is green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped-contract assertions in `spec/*.md`
- Retuning lint or verify-matrix behavior beyond the Python parity named by design
- Removing Python implementations or changing installed command names
- New lint rules, `--strict`, baselining, or new CLI/config surface
- Broad `mustmatch-core` parser redesign or parser refactors not required by this port
- Live-service or credential-backed verify behavior; `.march/contract-red-check.json` has no verify-lane entries

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist 0/22
- Read `AGENTS.md` and `CLAUDE.md`; located shipped specs under `spec/*.md`
- `git fetch origin main --quiet && git rebase origin/main` — branch already up to date, no conflicts
- Read `.march/design-final.md`, `.march/contract-red-check.json`, `.march/ticket.md`, and stale seed `.march/code-log.md`
- Read skills: `cli-design`, `mustmatch`, and `rust-standards`
- `spec-only` — unavailable in this shell (`command not found`)
- `make spec` — red as expected: five failures in `spec/03-rust-quality-commands.md` covering Rust lint/verify-matrix help and JSON behavior
- Verified preconditions: `tests/fixtures/rust-quality/*` exist, `bash`, `cargo`, and `uv` are available, `.march/validation-profiles.toml` exists, and no external service/credential lane is present
- Searched existing code for lint/verify-matrix/Python oracle constants, Rust dispatch/help patterns, serde_json usage, subprocess invocation, and path-resolution patterns
- Added `crates/mustmatch-cli/src/lint.rs` porting Python lint constants/behavior, `bash -n` shell syntax checks, JSON output, help, and exit codes
- Added `crates/mustmatch-cli/src/verify_matrix.rs` porting Python table code-span scanning, repo-path heuristic traps, lexical path resolution, JSON output, help, and exit codes
- Updated `crates/mustmatch-cli/src/main.rs` to route `lint` and `verify-matrix` before match parsing and list them in top-level help
- Added `regex` dependency to `crates/mustmatch-cli/Cargo.toml`
- `cargo fmt && cargo check -p mustmatch-cli` — green
- `make spec` — green, 13 passed; all five `spec/03-rust-quality-commands.md` check-lane entries pass
- Verify lane: no `lane: verify` entries and no `make verify` target; deterministic verify-matrix runtime is covered by check-lane spec
- `cargo test -p mustmatch-cli` — green, 17 passed including new lint shell-fence/rule coverage and verify-matrix heuristic/table-ref/normalization coverage
- `cargo clippy -p mustmatch-cli -- -D warnings` — green
- Added `crates/mustmatch-cli/tests/quality_parity.rs` comparing Rust JSON status/count/rules/reference statuses with Python CLI on shared rust-quality fixtures
- `cargo fmt && cargo test -p mustmatch-cli` — green, 17 unit tests and 2 parity tests passed
- Updated design-named docs/README prose for Rust `lint` and `verify-matrix` availability without changing executable assertions
- `git diff -- spec tests/fixtures/rust-quality` — no shipped spec assertions or rust-quality fixtures changed
- Final `make spec && make test && make lint` — green: specs 13 passed; focused `make test` pytest 63 passed plus cargo tests (17 CLI unit, 2 CLI parity, 48 core, 2 Python); lint green
- `git diff --check` — clean
- `git status --short --branch` — only intended runtime/dependency/docs plus `.march/code-log.md`; `.march/` remains unstaged

Proof results:
- Check-lane contract: `make spec` green, including all five `spec/03-rust-quality-commands.md` entries from `.march/contract-red-check.json`.
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green.
- Verify lane: no `lane: verify` entries in `.march/contract-red-check.json` and no `make verify` target.

Over-edit audit:
- `main.rs` changes are load-bearing dispatch/help changes named by design; without them subcommands fall through to matcher parsing and help contracts fail.
- `lint.rs` is load-bearing for the Rust lint runtime named by design: Python-parity regexes, directive-bearing shell fence collection, `bash -n`, JSON fields, help, and exit semantics.
- `verify_matrix.rs` is load-bearing for the Rust verify-matrix runtime named by design: table code-span scanning, exact repo-path false-positive guard, in-repo/missing/invalid resolution, JSON fields, help, and exit semantics.
- `quality_parity.rs` is design-named internal parity coverage comparing Rust and Python over shared fixtures; it does not add shipped-contract assertions.
- `regex` dependency and `Cargo.lock` update are mechanical consequences of porting the Python regex heuristics faithfully.
- README/docs prose edits are confined to design-named documentation updates and do not change executable assertions.

Diff-size audit:
- Minimal implementation is a two-command Rust port plus parser-free static analysis, help, JSON output, path handling, shell syntax subprocess, and parity coverage; the new modules account for the large line count.
- No spec assertions, fixtures, Python implementation, off-path refactors, or speculative validation were changed.

## Deviations from Design
- None
