# Code Log

## Execution Order
1. Orientation, rebase, design/contract review, and baseline observation confirmation — done
2. Precondition checks and prior-art search in runner/context paths — done
3. Implement missing explicit-path validation and bare-filename context root normalization — done
4. Run targeted cargo tests, spec-only, and focused validation; fix minimal failures — done
5. Hygiene, over-edit audit, final code-log proof — done

## Resume State
- Last completed batch: Hygiene, over-edit audit, final code-log proof
- Files edited so far: `.march/code-log.md`, `crates/mustmatch-cli/src/runner.rs`, `crates/mustmatch-cli/src/context.rs`, `README.md`
- Existing partial edits: preserve current minimal path-validation/root-normalization edits
- Tests passing: `cargo test -q -p mustmatch-cli --test runner_error_paths -- --nocapture`, `make spec`, `make test` (focused), and `make lint` are green
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- Adding, relaxing, deleting, or changing shipped `spec/*.md` assertions
- Redesigning runner discovery, CLI parsing, named-run dependency handling, or hook diagnostics
- Changing happy-path runner output or existing empty-directory no-op behavior
- Adding docs/help/spec expansion unless an existing public note contradicts the final behavior
- Implementing speculative validation beyond missing explicit operands and bare-filename root normalization

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status` — initial checklist read
- Read `AGENTS.md` and `CLAUDE.md`; behavioral specs are `spec/*.md`
- Read mustmatch and rust-standards skill guidance
- `find spec -maxdepth 2 -type f -name '*.md'` — located spec files
- `git fetch origin main && git rebase origin/main` — branch already up to date
- Read `.march/ticket.md`, `.march/design-final.md`, `.march/contract-red-check.json`, and replaced stale seed `.march/code-log.md`
- `make spec` — green (80 passed, 2 skipped), matching the spec-only/baseline note
- Baseline cargo check-lane observations:
  - `cargo test -q -p mustmatch-cli --test runner_error_paths missing_explicit_path_fails_but_empty_directory_is_noop -- --nocapture` — red as recorded; missing explicit path currently prints `No markdown files found` and exits successfully
  - `cargo test -q -p mustmatch-cli --test runner_error_paths bare_filename_context_root_resolves_to_current_directory -- --nocapture` — red as recorded; bare filename context setup fails from bad cwd/root resolution
  - `cargo test -q -p mustmatch-cli --test runner_error_paths invalid_lang_exits_before_green_no_tests_summary -- --nocapture` — green ratchet
  - `cargo test -q -p mustmatch-cli --test runner_error_paths cyclic_uses_dependency_fails_with_clear_message -- --nocapture` — green ratchet
  - `cargo test -q -p mustmatch-cli --test runner_error_paths setup_failure_diagnostic_redacts_expanded_secret -- --nocapture` — green ratchet
- Preconditions checked: `crates/mustmatch-cli/src/runner.rs`, `crates/mustmatch-cli/src/context.rs`, `crates/mustmatch-cli/tests/runner_error_paths.rs`, `Makefile`, `Cargo.toml`, `.march/validation-profiles.toml`, `cargo`, `make`, and `mustmatch` are present; no external services, data files, or credentials are required for this ticket
- Prior-art search: `runner.rs` already has `doc_dir` treating bare filename parents as `.`; `collect_markdown_files`/`collect_one` currently ignore nonexistent paths; `context.rs` has the repeated `path.parent().unwrap_or(path)` pattern in `ContextRegistry::new` and `find_config`; no existing helper is shared between runner/context
- Edited `crates/mustmatch-cli/src/runner.rs`: `run` now rejects missing explicit operands before markdown collection and preserves existing empty-directory/no-markdown behavior after validation
- Edited `crates/mustmatch-cli/src/context.rs`: added local `effective_parent` mirroring `doc_dir` and used it for config-root derivation and non-directory config discovery starts
- `cargo test -q -p mustmatch-cli --test runner_error_paths -- --nocapture` — green (5 passed); both expected-red behavioral checks now pass and all three green ratchets remain green
- `make spec` — green (80 passed, 2 skipped)
- Verify lane: `.march/contract-red-check.json` has no `lane: verify` entries, so no credential-backed `make verify`/operator check is outstanding for this ticket
- Docs/scripts check: searched README, AGENTS/CLAUDE, docs/specs, Makefile, tests, and CLI sources for `mustmatch test`, missing/no-markdown path text, and `{root}` references; verify found one stale README console example count and relaxed it to durable `passed` wording. No help/scripts edits were needed.
- `git diff --name-only` — `.march/code-log.md`, `README.md`, `crates/mustmatch-cli/src/context.rs`, `crates/mustmatch-cli/src/runner.rs`, and `crates/mustmatch-cli/tests/runner_error_paths.rs` changed; no shipped specs changed
- `make test` — focused profile green (31 CLI unit tests, 5 runner_error_paths integration tests, 48 core tests, doc-tests green)
- `make lint` — green (`cargo fmt --check` + `cargo clippy -- -D warnings`)
- `git diff --check` — clean
- `git status --short --branch`, `git diff --cached --name-only`, `git ls-files --others --exclude-standard` — verify staged intended work products, including the bounded README docs parity fix; no untracked build artifacts

Proof results:
- Check lane: `cargo test -q -p mustmatch-cli --test runner_error_paths -- --nocapture` is green; the two red behavioral entries now pass and the three green ratchets still pass
- Spec-only: `make spec` is green (80 passed, 2 skipped)
- Focused profile: `make test` is green
- Lint: `make lint` is green
- Verify lane: no entries in `.march/contract-red-check.json`

Over-edit audit:
- `runner.rs` changes are limited to validating explicit operands before the existing collector and printing one missing-path diagnostic per missing operand when not quiet; removing any line would either restore the silent-green typo bug, break quiet behavior, or remove the design-named diagnostic/exit behavior
- `context.rs` changes are limited to the design-named bare-parent normalization in root derivation and config discovery; `effective_parent` is the same local shape as existing `doc_dir`
- No CLI parsing, discovery recursion, named-run cycle handling, setup diagnostic handling, or shipped specs were changed; the only docs change is the README's stale non-executable count relaxed to durable wording

Diff-size audit:
- Minimal fix is two small path-handling changes plus one helper per file; total runtime diff is under the expected 3x envelope for the named changes
- No adjacent fixes were taken

## Deviations from Design
- None
