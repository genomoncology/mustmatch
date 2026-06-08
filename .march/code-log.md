## Execution Order
1. Replace stale code log; record quickfix scope, exact files, and version targets.
2. Bump only `.github/workflows/release.yml` action major tags to Node-24-capable releases while preserving jobs, permissions, environment, and artifact names/patterns.
3. Run focused proof (`make spec`) and full repo gates (`make lint`, `make test`, `make spec`).
4. Audit diff/status for scope creep and finalize this log for verify.

## Resume State
- Last completed batch: Final diff/status audit completed.
- Files changed so far: `.github/workflows/release.yml`, `.march/code-log.md`
- Tests green: `make lint && make test && make spec` green; final spec count 82 passed, 2 skipped.
- Next concrete action: ready for verify.
- Current blocker: none.

## Scope Guardrails
- Do not change workflow jobs, job order, triggers, `environment: release`, permissions, smoke/publish ordering, artifact names, artifact patterns, or paths.
- Do not refactor YAML, publish logic, trusted-publisher configuration, Makefile, smoke target, specs, or docs unless a version-pinned assertion requires parity.
- Do not change `.github/workflows/test.yml`; ticket is release workflow only.

## Commands and Changes
- `checkpoint status` — initial checklist read.
- Read `.march/ticket.md`, `.march/checkpoint.json`, and existing `.march/code-log.md`; existing log was stale from a different ticket and replaced.
- Surveyed `.github/workflows/release.yml` and `spec/15-release-smoke.md`.
- `grep` confirmed `spec/15-release-smoke.md` matches action names, not versions.
- Remote action metadata checked with `git ls-remote` and `curl` against `action.yml`:
  - `actions/checkout@v6` uses `node24`.
  - `actions/upload-artifact@v7` uses `node24`.
  - `actions/download-artifact@v8` uses `node24`.
  - `PyO3/maturin-action@v1` already uses `node24`.
  - `softprops/action-gh-release@v3` uses `node24`.
  - `astral-sh/setup-uv@v7` uses `node24`.
  - `pypa/gh-action-pypi-publish@release/v1` is composite, so no Node runtime pin.
- Edited `.github/workflows/release.yml` only for action pins:
  - `actions/checkout@v4` -> `@v6`.
  - `actions/upload-artifact@v4` -> `@v7`.
  - `actions/download-artifact@v4` -> `@v8`.
  - `astral-sh/setup-uv@v5` -> `@v7`.
  - `softprops/action-gh-release@v2` -> `@v3`.
  - Left `PyO3/maturin-action@v1` and `pypa/gh-action-pypi-publish@release/v1` unchanged after runtime verification.
- `grep -n "uses:" .github/workflows/release.yml` confirmed no remaining release-workflow `uses:` entry on a Node-20-only version.
- `make spec` — green (82 passed, 2 skipped); `spec/15-release-smoke.md` release publish assertion still passes without spec edits because it matches action names, not versions.
- `make lint && make test && make spec` — green (`cargo fmt --check`, `cargo clippy -- -D warnings`, 31 CLI unit tests, 5 runner error-path integration tests, 48 core tests, doc-tests, and 82 specs passed with 2 skipped).
- `git diff --stat` / `git diff -- .github/workflows/release.yml .march/code-log.md` / `git status --short --branch` / `git ls-files --others --exclude-standard` — only `.github/workflows/release.yml` and `.march/code-log.md` changed; no untracked files. Workflow diff is version pins only.

## Final Verification
- gate command: `make lint && make test && make spec`
- gate result: green
- files changed: `.github/workflows/release.yml`, `.march/code-log.md`
- proof/docs/specs/help updated: no spec/doc/help text changes required; `spec/15-release-smoke.md` still passes because it asserts action names and release ordering, not versions.
- Ready for verify: yes
