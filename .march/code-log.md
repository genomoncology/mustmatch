# Code Log

## Commands run

- `checkpoint status`
- `GIT_EDITOR=true git rebase main`
- `git --no-pager diff --stat main..HEAD | tail -1`
- `uv sync --extra dev`
- `uv run python -m pytest docs/ README.md -q`
- `uv run pytest docs/ README.md -q`
- `uv run python -m pytest docs/08-configuration.md -q -vv`
- `uv run python -m pytest -p mustmatch.pytest_plugin --trace-config --co -q docs/01-overview.md`
- `uv run python -m pytest -p no:mustmatch -p mustmatch.pytest_plugin --trace-config --co -q docs/01-overview.md`
- `uv run pytest -p no:mustmatch -p mustmatch.pytest_plugin --trace-config --co -q docs/01-overview.md`
- `make check`
- `make test`
- `make coverage`

## What changed

- Added repo-local pytest bootstrap in `pyproject.toml` so checkout-local runs preload `mustmatch.pytest_plugin` from `src`.
- Switched repo-owned pytest and coverage invocations in `Makefile`, CI, and contributor docs to interpreter-module form (`python -m pytest`, `python -m coverage`).
- Added an executable regression proof in `docs/08-configuration.md` that asserts `uv run pytest --trace-config --co -q docs/01-overview.md` registers `mustmatch.pytest_plugin`.
- Fixed coverage startup/reporting to reuse the existing `pyproject.toml` coverage config and normalize temporary subprocess package paths back to `src/mustmatch`.

## Tests and proof

- The new `docs/08-configuration.md` bootstrap proof failed before implementation and passed after the config change.
- `uv run pytest docs/ README.md -q` now passes in this worktree even with the stale `.venv/bin/pytest` shebang.
- `uv run python -m pytest docs/ README.md -q` passes.
- `make check` passes.
- `make test` passes.
- `make coverage` passes.

## Deviations from the approved design

- The approved design proposed `addopts = ["-p", "mustmatch.pytest_plugin"]`. In a healthy virtualenv that double-registers the plugin against the existing `pytest11` entry point and crashes pytest with `ValueError: Plugin already registered under a different name`.
- To preserve the same bootstrap intent without breaking healthy environments, I implemented `addopts = ["-p", "no:mustmatch", "-p", "mustmatch.pytest_plugin"]`. This disables the entry-point alias during repo-local runs, then preloads the module path directly.
- While verifying the updated `coverage` target, I found the repo already stored coverage config in `pyproject.toml` rather than `.coveragerc`, and subprocess CLI executions recorded `/tmp/tmp*/mustmatch/...` paths. I updated the target and added `[tool.coverage.paths]` so `make coverage` finishes cleanly.
