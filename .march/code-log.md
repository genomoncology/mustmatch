# Code Log

## Execution Order
1. Orientation and red-state confirmation — done
2. Inspect existing runner/parser/pytest patterns and verify local-only preconditions — done
3. Implement standalone runner directive handling for console and named runs — done
4. Implement pytest plugin parity for named runs, output expectations, and console collection — done
5. Run spec-only/focused gates and apply minimal fixes — done
6. Diff audit, docs/help consistency check, and final checkpoint state — done

## Resume State
- Last completed batch: Diff audit, docs/help consistency check, and final checkpoint state
- Files edited so far: `.march/code-log.md`, `src/mustmatch/doc_runner.py`, `src/mustmatch/pytest_plugin.py`
- Existing partial edits: preserve
- Tests passing: yes — targeted `tests/test_doc_runner.py`, `make test`, and `make check`
- Next concrete action: final response
- Current blocker: none

## Out of Scope
- GoToolkit documentation rewrites
- New commands, config keys, or global CLI flags
- Parser-level semantic validation redesign
- Support for merged streams, arbitrary file descriptors, stdin modeling, or shell tracing
- Adding, relaxing, or deleting shipped-contract assertions

## Adjacent Fixes
- (empty)

## Commands and Changes
- `checkpoint status`
- `git fetch origin main && git rebase origin/main` — branch already up to date
- Read `.march/ticket.md`, `.march/design-final.md`, `.march/spec-red-check.json`, and existing `.march/code-log.md`
- `make test` — confirmed 10 expected red failures and 55 passing tests
- Replaced stale `.march/code-log.md` content with current code-step log structure
- Inspected `src/mustmatch/doc_runner.py`, `src/mustmatch/pytest_plugin.py`, `src/mustmatch/runtime.py`, `tests/test_doc_runner.py`, `docs/12-named-runs.md`, and `docs/13-standalone-doc-runner.md`
- `rg` confirmed existing runner/parser/pytest entry points; preconditions verified local `mustmatch`, `pyproject.toml`, `docs/`, and `tests/` exist
- Edited `src/mustmatch/doc_runner.py` to parse `exit`/`exit_code` and `stream`, compare selected streams for console blocks, accept expected nonzero named runs, and let output blocks inherit the run stream
- Edited `src/mustmatch/pytest_plugin.py` to mirror directive parsing, named-run validation/cache semantics, output stream inheritance, and console block collection/execution
- `uv run python -m pytest tests/test_doc_runner.py -q` — 14 passed
- `make test` — 67 passed
- `make check` — checks passed
- `git diff --check && git diff --stat && rg -n "exit=2 stream=stderr|Named Runs Can Capture Expected Errors|Expected Errors Can Match Stderr|set \\+e|stderr redirection|temporary files" docs/12-named-runs.md docs/13-standalone-doc-runner.md` — whitespace clean; changed files are code-log plus the two runner surfaces; docs still contain the landed no-shell-ceremony examples

Code decisions:
- Kept directive interpretation at the Python runner edges; the Rust parser remains syntax-only.
- Mirrored helper behavior in `doc_runner.py` and `pytest_plugin.py` because the two runner paths already had parallel private helpers and failure classes.
- Included `console mustmatch` collection when `--mustmatch-lang=bash`, matching standalone runner compatibility behavior where bash mode includes console/output blocks.

Proof results:
- Pre-edit `make test`: 10 failed, 55 passed, matching `.march/spec-red-check.json`.
- Post-edit targeted: `uv run python -m pytest tests/test_doc_runner.py -q` → 14 passed.
- Post-edit spec-only/focused: `make test` → 67 passed.
- Post-edit check: `make check` → checks passed.

Over-edit audit:
- Retained only runner-edge directive parsing, selected-stream routing, expected-exit validation/cache behavior, pytest console collection/execution, and mechanical use of existing compare/runtime helpers.
- No shipped-contract assertions were added, relaxed, or deleted.
- No adjacent fixes were needed.

## Deviations from Design
- None
