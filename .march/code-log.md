# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and red-state confirmation — done
2. Inspect existing Rust CLI/core/parser patterns and local fixtures/config preconditions — done
3. Implement minimal `mustmatch-cli test` runner modules/dispatch for landed fixture behavior — done
4. Wire Rust gates/docs named by design and run focused/spec gates — done
5. Diff audit, cleanup, and final proof recording — done

## Resume State
- Last completed batch: Diff audit, cleanup, and final proof recording
- Files edited so far: `.march/code-log.md`, `Cargo.lock`, `crates/mustmatch-cli/Cargo.toml`, `crates/mustmatch-cli/src/main.rs`, `crates/mustmatch-cli/src/process.rs`, `crates/mustmatch-cli/src/context.rs`, `crates/mustmatch-cli/src/expect.rs`, `crates/mustmatch-cli/src/named_runs.rs`, `crates/mustmatch-cli/src/runner.rs`, `Makefile`, `README.md`, `docs/13-standalone-doc-runner.md`, `spec/02-rust-runner.md`
- Existing partial edits: preserve committed runtime/spec changes; `.march/code-log.md` remains unstaged artifact
- Tests passing: yes — final `make spec && make test && make lint` is green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped-contract assertions in `spec/*.md`
- Python block execution beyond visible unsupported skips
- Table scenarios, embedded files, lifecycle hooks, lint/verify-matrix, Python deletion, or binary rename
- New abstractions beyond the runner modules named by design
- Input validation or defensive behavior not required by landed assertions

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist 0/22
- Read `AGENTS.md` and `CLAUDE.md`; located shipped specs under `spec/*.md`
- `git fetch origin main && git rebase origin/main` — branch already up to date
- Read `.march/design-final.md`, `.march/contract-red-check.json`, `.march/ticket.md`, and previous `.march/code-log.md`
- `make spec` — red as expected: 3 passed, 2 failed
- `uv run mustmatch test spec/ -v` — both `spec/02-rust-runner.md` check assertions fail with `Error: too many arguments`
- Rewrote `.march/code-log.md` for current 03-code execution state
- Read CLI/mustmatch/rust skills relevant to this implementation
- Inspected `crates/mustmatch-cli/src/main.rs`, core parser/comparator exports, Python `doc_runner.py` parity, `Makefile`, `spec/02-rust-runner.md`, and Rust runner fixtures/configs
- Verified local-only preconditions: fixture files exist, helper-tool is executable, and `cargo`/`uv` are available
- Added Rust runner modules named by design: subprocess execution, context config, named runs/substitution, expectation comparison, and markdown dispatch
- Extended `mustmatch-cli` dispatch so first token `test` runs the documentation runner while `-- test` remains an assertion expected value path
- Added `serde_json`, `tempfile`, and `toml` dependencies for JSON substitution, `{tmp}` contexts, and config loading
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner` — 12 passed, 1 skipped
- `cargo run -q -p mustmatch-cli -- test -v tests/fixtures/rust-runner-pyproject` — 2 passed
- Updated `Makefile` to include `cargo fmt --check`/`cargo clippy -- -D warnings` in `make lint` and `cargo test` in `make test`
- Updated README and `docs/13-standalone-doc-runner.md` prose for `mustmatch-cli test`, Rust gates, and `mustmatch.toml` precedence
- `make spec` initially still failed because spec execution cwd is `spec/`, making `tests/fixtures/...` resolve to a nonexistent path
- Mechanical landed-assertion fix: changed fixture paths in `spec/02-rust-runner.md` to `../tests/fixtures/...`; expected output/behavior unchanged
- `make spec` — 5 passed
- `make test` initially failed because pytest collected Rust-runner fixture markdown under `tests/fixtures/`; updated `Makefile` pytest invocation with `--ignore=tests/fixtures` so fixture input data is not treated as Python-runner docs
- `make test` — Python docs/README/tests 67 passed; `cargo test` 54 passed across Rust crates/doc-tests
- `make lint` initially failed on a clippy `collapsible_if`; simplified the named-run index condition
- `cargo fmt && make lint` — ruff, cargo fmt, and clippy all green
- `printf 'test\n' | cargo run -q -p mustmatch-cli -- -- test` — confirmed `test` remains assertable via `--`
- `git commit -m "code: fix mechanical bug in landed assertion (spec/02-rust-runner.md)"` — committed fixture path-only assertion fix
- `git commit -m "code: implement rust documentation runner"` — committed Rust runner/runtime/docs/gate changes
- Final `make spec && make test && make lint` — all green: specs 5 passed; Python tests 67 passed; Rust cargo test green; ruff/fmt/clippy green
- `git status --short --branch` — only `.march/code-log.md` modified/unstaged as required runtime artifact

Proof results:
- Check-lane contract: `make spec` green, including both `spec/02-rust-runner.md` entries.
- Focused profile: `.march/validation-profiles.toml` maps focused to `make test`; final `make test` green.
- Full local lint gate: `make lint` green.
- Verify lane: no verify entries in `.march/contract-red-check.json`.

Over-edit audit:
- Runtime modules are the design-named surfaces required for subprocess execution, context config, named runs/substitution, expectation comparison, and markdown dispatch.
- Added dependencies are load-bearing: `toml` for config precedence/fallback, `tempfile` for `{tmp}` context lifetime, `serde_json` for `{{run.field}}` substitution.
- Makefile pytest `--ignore=tests/fixtures` is load-bearing because Rust-runner fixture markdown is input data for the Rust contract, not Python-runner docs.
- README/docs prose and CLI help changes are limited to changed shipped behavior and gate wiring.
- No adjacent fixes were needed.

Diff-size audit:
- The implementation is larger than the direct fixture happy path because design explicitly required addressable runner modules and gate/docs wiring.
- Most apparent size is `Cargo.lock` transitive dependency resolution plus the new module files; no off-path refactors or reformat-only source rewrites were included.

## Deviations from Design
- None
