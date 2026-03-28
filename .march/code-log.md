# Code Log

## Commands run

- `checkpoint status`
- `GIT_EDITOR=true git rebase main`
- `git --no-pager diff --stat main..HEAD | tail -1`
- `cargo test -p mustmatch-core --lib`
- `uv run python -m pytest docs/03-executable-documents.md docs/10-verify-matrix.md docs/11-lint.md -q`
- `uv run python -m pytest docs/03-executable-documents.md --collect-only -q | mustmatch like "Nested Fences In Bash Blocks"`
- `uv sync --extra dev --reinstall-package mustmatch`
- `uv run python -m pytest docs/03-executable-documents.md -q`
- `uv run python -m pytest docs/10-verify-matrix.md docs/11-lint.md -q`
- `make check < /dev/null > ... 2>&1`
- `make test < /dev/null > ... 2>&1`
- `uv run python -m pytest docs/ README.md -q < /dev/null > ... 2>&1`
- `git --no-pager status --short`
- `git add .github/workflows/test.yml CLAUDE.md Makefile README.md crates/mustmatch-core/src/parser.rs docs/03-executable-documents.md`
- `git --no-pager diff --cached`
- `cargo fmt`

## What changed

- Added `is_closing_fence` in `crates/mustmatch-core/src/parser.rs`, reusing `parse_fence_start` so a closing fence must have no info string while still allowing longer same-marker closing fences.
- Added two Rust parser regression tests in `crates/mustmatch-core/src/parser.rs` for nested inner fences and longer closing fences with trailing spaces.
- Extended `docs/03-executable-documents.md` with a new `Nested Fences In Bash Blocks` executable regression proof.
- Updated `Makefile`, `.github/workflows/test.yml`, `CLAUDE.md`, and `README.md` to use `uv sync --extra dev --reinstall-package mustmatch` before Python-side verification so Rust-core changes rebuild the editable `mustmatch._core` extension.
- Wrote the external planning artifact `/home/ian/workspace/planning/mustmatch/planning/quality-bar.md` with refreshed smoke tests, timings, fragile areas, security boundaries, and spec health.

## Tests and proof

- The new Rust regression test `keeps_inner_fence_with_info_inside_bash_block` failed before the parser fix and passed after it.
- `uv run python -m pytest docs/03-executable-documents.md --collect-only -q | mustmatch like "Nested Fences In Bash Blocks"` failed before the fix (section skipped) and passed after the parser fix plus editable-package rebuild.
- `uv run python -m pytest docs/03-executable-documents.md -q` passes with `3 passed`.
- `uv run python -m pytest docs/10-verify-matrix.md docs/11-lint.md -q` passes with `6 passed`.
- `cargo test -p mustmatch-core --lib` passes with `30 passed`.
- `make check` passes.
- `make test` passes with `33 passed in 4.38s`.
- `uv run python -m pytest docs/ README.md -q` passes with `33 passed in 4.24s`.

## Deviations from the approved design

- The executable-doc proof in `docs/03-executable-documents.md` does **not** include a literal inner line containing only ```` ``` ```` inside an outer triple-backtick Markdown fence. With the existing indentation behavior intentionally left unchanged, that line would become a real closing fence in the surrounding Markdown source. The docs proof therefore focuses on the actual regression line ```` ```python ```` while the Rust unit tests cover closing-fence semantics and longer closing fences precisely.
- The approved design did not call for build-script changes, but they were necessary for trustworthy verification. Plain `uv sync --extra dev` left `src/mustmatch/_core.abi3.so` stale after Rust edits, which caused Python-side pytest runs to exercise the old parser binary.
