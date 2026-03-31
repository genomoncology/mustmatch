# Code Log

## Commands run

- `checkpoint status`
- `GIT_EDITOR=true git rebase main`
- `git diff --stat main..HEAD | tail -1`
- `uv sync --extra dev --reinstall-package mustmatch`
- `uv run python -m pytest docs/02-cli-assertions.md docs/06-comparison-modes.md -q`
- `cargo test -p mustmatch-core`
- `uv run python -m pytest docs/02-cli-assertions.md -q` (red proof after adding multiline specs)
- `cargo test -p mustmatch-core contains_multiline`
- `make check < /dev/null 2>&1`
- `uv run python -m pytest docs/ README.md -q`
- `cargo test -p mustmatch-core`
- `cargo test -p mustmatch-cli`
- `printf ... | cargo run -q -p mustmatch-cli -- ...` (manual multiline CLI smoke check)

## What changed

- Added `ContainsLineReport` plus `analyze_contains_lines()` in `crates/mustmatch-core/src/comparator.rs`, and routed multiline plain-text contains checks through that shared report while preserving single-line behavior.
- Updated both CLIs to special-case multiline plain-text `like`/`not like` using the shared core report, so positive checks require all non-empty expected lines and negated checks require none of them.
- Exposed the shared contains-line report through the PyO3 binding, updated operator-facing docs in `docs/02-cli-assertions.md` and `docs/06-comparison-modes.md`, and added focused Rust tests for the new behavior.

## Tests and specs added or updated

- Added a `Multi-line Like` executable-doc section in `docs/02-cli-assertions.md` covering positive, blank-line, ignore-case, and failure-message behavior.
- Added a concise multiline mode-boundary example to `docs/06-comparison-modes.md`.
- Added Rust tests for single-line regression coverage, multiline positive matching, blank-line skipping, whitespace preservation, ignore-case matching, vacuous-empty behavior, and found/missing line reporting.

## Deviations from design

- None.
