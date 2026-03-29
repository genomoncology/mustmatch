# Code Review Log

## Critique

### Design Completeness Audit

| Design item | Matching implementation or proof | Status |
| --- | --- | --- |
| Add `CHANGELOG.md` with `0.0.4` Added/Fixed/Changed coverage | [`CHANGELOG.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/CHANGELOG.md#L1) | Addressed |
| Keep package version at `0.0.4` with no version-file edits | [`pyproject.toml`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/pyproject.toml#L7) unchanged in `git diff main..HEAD` | Addressed |
| Re-run `make check` and `make test` on the release commit | Local reruns passed: `make check`, `make test` | Addressed |
| Push reviewed commit to `origin/main` from this worktree | `git push origin HEAD:main` moved remote `main` to `fc970d5866e977f7bec53ae930e1670e02517830`, then to `97426da083b52d7fdf9461836d86a8aaf5da80d2` for the workflow repair | Addressed after review repair |
| Create and push annotated tag `v0.0.4` on the reviewed release commit | `git tag -a v0.0.4 -m "0.0.4"` and `git push origin refs/tags/v0.0.4`; dereferenced tag points at `fc970d5866e977f7bec53ae930e1670e02517830` | Addressed after review repair |
| Release workflow completes successfully | Initial run `23698797360` failed on unsupported `macos-13`; repaired run `23698824700` reached publish but failed on PyPI trusted publishing | Not fully addressed |
| PyPI exposes `mustmatch==0.0.4` | `python3 -m pip index versions mustmatch` still shows `0.0.3` only | Not addressed |
| Fresh venv installs `mustmatch==0.0.4` | Fresh-venv `pip install mustmatch==0.0.4` failed because the package is not published | Not addressed |
| Installed CLI exposes `verify-matrix` and `lint` help | Blocked by failed publish/install; in-repo CLI surface is already covered by existing executable specs | Blocked by external publish failure |

Initial gaps found:

- The implementation stopped after adding [`CHANGELOG.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/CHANGELOG.md#L1) and local proof. The approved design required the operational release steps too, so remote push/tag/workflow/PyPI verification were initially missing.
- The pre-existing [`code-review-log.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/.march/code-review-log.md) artifact in this worktree was stale and pointed at a different ticket/worktree, which would have misled verify.
- The release workflow in [`release.yml`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/.github/workflows/release.yml#L16) still targeted `macos-13`, and GitHub rejected that job immediately with `The configuration 'macos-13-us-default' is not supported`.

Documentation and contract checks:

- The changelog entry covers all required user-facing release items in Added/Fixed/Changed form at [`CHANGELOG.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/CHANGELOG.md#L3).
- Existing CLI contract docs for shipped commands remain the executable specs at [`docs/10-verify-matrix.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/docs/10-verify-matrix.md#L1) and [`docs/11-lint.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/docs/11-lint.md#L1).
- External publish/install verification is still blocked by PyPI trusted-publisher configuration, not missing repo documentation.

### Test-Design Traceability

| Proof matrix item | Matching test / proof | Result |
| --- | --- | --- |
| `verify-matrix` is part of the shipped CLI surface | `make test`, plus [`docs/10-verify-matrix.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/docs/10-verify-matrix.md#L1) | Present |
| `lint` is part of the shipped CLI surface | `make test`, plus [`docs/11-lint.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/docs/11-lint.md#L1) | Present |
| Repo stays green before release | `make check`, `make test` | Present |
| Changelog file exists and covers release contents | Manual review of [`CHANGELOG.md`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/CHANGELOG.md#L1) | Present as manual artifact |
| Remote `main` received reviewed commit | `git push origin HEAD:main` plus `git ls-remote origin refs/heads/main` | Present |
| Tag `v0.0.4` exists and points at release commit | `git push origin refs/tags/v0.0.4` plus `git ls-remote origin refs/tags/v0.0.4^{}` | Present |
| GitHub Actions publishes the release artifacts | Workflow run `23698824700` | Failing: publish job hit PyPI `invalid-publisher` |
| PyPI exposes `0.0.4` | `python3 -m pip index versions mustmatch` | Missing because publish failed |
| Clean environment installs the published package | Fresh-venv `pip install mustmatch==0.0.4` | Missing because publish failed |
| Installed CLI exposes `verify-matrix` and `lint` help | Fresh-venv `mustmatch verify-matrix --help` and `mustmatch lint --help` | Blocked by failed install |

Blocking traceability gaps:

- Design requires the external publish/install proofs above. Those proofs are still absent because PyPI trusted publishing is misconfigured outside the repo.

### Quality Checks

- Implementation quality: the repo-side release artifact is minimal and correct, but the original implementation left required operational release work undone.
- Duplication review: no redundant helpers or abstractions were introduced. The only code repair was a runner-label correction in [`release.yml`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/.github/workflows/release.yml#L28).
- Security review: no new injection surface was introduced. The remaining blocker is trusted-publisher identity matching on PyPI.
- Performance review: not relevant beyond release workflow execution. No new runtime hot path was introduced.

## Fix Plan

1. Execute the operational release steps that were left undone: push the reviewed commit to remote `main`, create/push `v0.0.4`, and verify the GitHub workflow and public package state.
2. Repair the release workflow’s unsupported Intel macOS runner label so all five build targets can execute.
3. Replace the stale `.march/code-review-log.md` artifact with the real findings from this worktree.
4. If publishing still fails after repo repairs, capture the exact external blocker and leave it as a residual concern for verify.

## Repair

Applied fixes:

- Pushed the reviewed release commit to `origin/main`: `fc970d5866e977f7bec53ae930e1670e02517830`.
- Created and pushed annotated tag `v0.0.4`, confirmed by `git ls-remote origin refs/tags/v0.0.4^{}`.
- Fixed the release workflow runner matrix at [`release.yml`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/.github/workflows/release.yml#L28) by changing the Intel macOS job from `macos-13` to `macos-15-intel`.
- Pushed the workflow repair commit `97426da083b52d7fdf9461836d86a8aaf5da80d2` to `origin/main`.
- Re-dispatched the release workflow for tag `v0.0.4` via `workflow_dispatch` run `23698824700`.
- Replaced the stale review artifact with this file.

### Post-Fix Collateral Damage Scan

- Dead code: none introduced. The workflow still builds the same five target families and the same sdist/publish structure.
- Unused imports or variables: not applicable; only YAML and markdown artifacts changed.
- Resource cleanup conflicts: none introduced.
- Stale error messages: the workflow now fails later, at the real PyPI publish step, instead of the misleading unsupported-runner failure.
- Shadowed variables: not applicable.

## Verification

- `git --no-pager diff main..HEAD` showed only the changelog change before review repair.
- `make check` -> pass
- `make test` -> `33 passed`
- `git push origin HEAD:main` -> remote `main` first advanced to `fc970d5866e977f7bec53ae930e1670e02517830`
- `git tag -a v0.0.4 -m "0.0.4"` and `git push origin refs/tags/v0.0.4` -> pass
- `git ls-remote origin refs/tags/v0.0.4^{}` -> `fc970d5866e977f7bec53ae930e1670e02517830`
- Workflow repair commit `97426da083b52d7fdf9461836d86a8aaf5da80d2` pushed to `origin/main`
- Release workflow run `23698824700` -> all build jobs and `sdist` succeeded; `publish` failed
- `python3 -m pip index versions mustmatch` -> `0.0.3` remains latest published version
- Fresh venv `pip install mustmatch==0.0.4` -> `No matching distribution found`

## Residual Concerns

- PyPI trusted publishing is still misconfigured externally. The `publish` job in run `23698824700` failed with `invalid-publisher`, and PyPI reported no matching trusted publisher for claims including `repository=genomoncology/mustmatch`, `workflow_ref=genomoncology/mustmatch/.github/workflows/release.yml@refs/heads/main`, and `environment=release`.
- Because publish failed, the public-install checks for `mustmatch==0.0.4`, `mustmatch verify-matrix --help`, and `mustmatch lint --help` remain blocked.
- The workflow also emits Node 20 deprecation warnings for `actions/checkout@v4`, `actions/upload-artifact@v4`, and `actions/download-artifact@v4`. Those warnings are not currently breaking the release, but they should be updated before GitHub enforces Node 24 defaults.

## Defect Register

| # | Category | Lintable | Description |
|---|----------|----------|-------------|
| 1 | incomplete-implementation | no | The original implementation stopped after the local changelog change and did not perform the required remote push, tag, workflow, or public verification steps from the approved design. |
| 2 | validation-gap | no | [`release.yml`](/home/ian/workspace/worktrees/004-release-mustmatch-0-0-4-to-pypi/.github/workflows/release.yml#L28) used unsupported runner label `macos-13`, causing the first release run to fail before testing the actual publish path. |
| 3 | stale-doc | no | The pre-existing `.march/code-review-log.md` artifact in this worktree was stale and described another ticket/worktree, so it could not be trusted as review evidence. |
| 4 | external-config | no | PyPI trusted publishing for `mustmatch` is not configured for the current GitHub claims; publish fails with `invalid-publisher`, leaving `0.0.4` unavailable on PyPI. |
