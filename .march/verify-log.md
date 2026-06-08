Decision: approved

## Checkpoint Summary
- Read `.march/ticket.md`, `.march/code-log.md`, `.march/checkpoint.json`, and the stale prior `.march/verify-log.md`; the prior verify log was from an earlier ticket and has been replaced.
- Preflight staged the ticket work products up front: `.github/workflows/release.yml` and `.march/code-log.md`. The required `git diff --cached --name-only main..HEAD` form is rejected by this git version, so I used the equivalent staged-vs-main check, `git diff --cached --name-only main`, plus `git diff --name-only main..HEAD` and `git diff --name-only`.
- Inspected the final staged workflow diff before choosing probes: release workflow edits are action ref version bumps only.

## Checklist Verification
- Every top-level `uses:` in `.github/workflows/release.yml` resolves and is Node 24-capable or composite: checkout v6, upload-artifact v7, download-artifact v8, maturin-action v1, setup-uv v7, and action-gh-release v3 all declare `node24`; PyPI publish `release/v1` is composite.
- No behavioral release workflow change: parsed YAML matches `main` after normalizing only action ref versions; jobs, `environment: release`, `id-token: write`, `contents: write`, artifact names/patterns/paths, and smoke-before-publish ordering are preserved.
- `spec/15-release-smoke.md` still passes under `make spec`; it matches action names/order rather than versions.
- Full gate `make lint && make test && make spec` is green.

## Exercise Results
- Parsed `main:.github/workflows/release.yml` and the current workflow with PyYAML, normalized current action refs back to base refs, and confirmed the parsed workflows are otherwise identical.
- Verified release workflow invariants directly: `environment: release`, `permissions.id-token: write`, `permissions.contents: write`, `name: wheels-${{ matrix.target }}`, `path: dist/*.whl`, `name: sdist`, `path: dist/*.tar.gz`, `pattern: wheels-*`, `merge-multiple: true`, `path: dist`, and `run: make smoke` are present.
- Resolved every unique top-level `uses:` ref with `git ls-remote` and fetched upstream action metadata:
  - `actions/checkout@v6` tag exists; `runs.using: node24`.
  - `actions/upload-artifact@v7` tag exists; `runs.using: node24`.
  - `actions/download-artifact@v8` tag exists; `runs.using: node24`.
  - `PyO3/maturin-action@v1` tag exists; `runs.using: node24`.
  - `astral-sh/setup-uv@v7` tag exists; `runs.using: node24`.
  - `softprops/action-gh-release@v3` tag exists; `runs.using: node24`.
  - `pypa/gh-action-pypi-publish@release/v1` branch exists; top-level action is `runs.using: composite`.
- Checked the PyPI publish composite caveat: `release/v1` contains a guarded fallback `actions/setup-python@v5.6.0`/Node20 step, but it is behind `if: steps.pre-installed-python.outputs.python-path == ''`; this release job runs on `ubuntu-latest`, where Python is preinstalled. I did not switch the release path to upstream `unstable/v1` because that would increase release risk and is not the documented stable ref.
- Focused `make spec`: green (`82 passed, 2 skipped`).
- Out-of-scope sweep found `.github/workflows/test.yml` still uses `actions/checkout@v4`; upstream metadata declares `runs.using: node20`, so I filed a planning issue instead of expanding this release-workflow ticket.

## Reusable Verification Learning
- High-signal probe: parse and compare workflow YAML after normalizing only `uses:` ref versions; this catches accidental behavior drift while allowing the intended version bumps.
- High-signal probe: resolve each action ref and inspect `runs.using` from upstream `action.yml`/`action.yaml`, while treating branch refs separately from tags.
- Composite-action internals can include guarded fallback `uses:` steps; record the caveat, but do not automatically switch release publishing to an upstream unstable branch.
- Improved-test destination: future lint/gate coverage could scan workflows for known Node20-only action pins; the concrete `.github/workflows/test.yml` follow-up is filed.

## Findings Fixed
- No bounded in-scope defect was found in `.github/workflows/release.yml`, so no code repair was needed.

## Regression Results
- `make lint`: green (`cargo fmt --check` and `cargo clippy -- -D warnings`).
- `make test`: green (31 CLI unit tests, 5 runner error-path integration tests, 48 core tests, doc-tests green).
- `make spec`: green (`82 passed, 2 skipped`).

## Issues Filed
- `/home/ian/workspace/planning/mustmatch/issues/027-upgrade-test-yml-checkout-node24.md` — `.github/workflows/test.yml` still uses `actions/checkout@v4` (`node20`), outside this release-workflow ticket.

## Final Scope Check
- Final repo diff is limited to `.github/workflows/release.yml`, `.march/code-log.md`, and this `.march/verify-log.md` artifact.
- The workflow diff remains version-only; no jobs, permissions, environment, artifact naming/patterns, smoke gate, publish logic, trusted-publisher config, specs, or docs were changed.
