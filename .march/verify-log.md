# Verify Log — 004 Release mustmatch 0.0.4 to PyPI

Decision: approved

## Checkpoint Summary

All 16 checklist items completed. No aborts. No repo repairs needed in this step — all prior fixes were applied by code review. The one remaining blocker (PyPI trusted publisher) is external infrastructure and has been filed as a critical issue.

## Quality Bar Results

| Smoke test | Result | Notes |
| --- | --- | --- |
| `make check < /dev/null` | PASS | 0.06s (baseline 0.05s — within noise) |
| `make test` | PASS | 33 passed in 4.42s, wall 12.1s (baseline 11.24s — within noise) |
| `uv run python -m pytest docs/ README.md -q` | PASS | 33 passed in 4.52s, wall 4.69s (baseline 4.40s — within noise) |
| `Nested Fences In Bash Blocks` collect probe | PASS | exit 0 |
| `cargo test -p mustmatch-core --lib` | PASS | 30 passed |

**Performance baselines:** All results within run-to-run noise of recorded baselines. No regressions, no meaningful improvements. Baselines unchanged.

**Fragile areas probed:**
- Rust fence handling: `Nested Fences In Bash Blocks` probe passes ✓
- Pytest bootstrap double-registration: `make test` runs full suite without `ValueError` ✓
- Editable PyO3 extension freshness: `make test` rebuilds extension before running ✓
- Bash block collection gate: existing specs all still collected correctly ✓

**Security boundaries:**
- `verify-matrix` with nonexistent file → exit 2, no path traversal attempted ✓
- Subprocess execution gated on `| mustmatch` rule — no change in this ticket ✓

## Exercise Results

**CLI surface:**
```
mustmatch --version          → "mustmatch 0.0.4"  exit 0
mustmatch --help             → full usage, all subcommands listed
mustmatch verify-matrix --help → subcommand help  exit 0
mustmatch lint --help        → subcommand help  exit 0
echo "hello world" | mustmatch like "hello"   → exit 0
echo "hello world" | mustmatch not like "error" → exit 0
echo "hello world" | mustmatch "goodbye"      → diff output  exit 1
```

**Error paths (adversarial):**
```
mustmatch verify-matrix --repo-root . nonexistent.md → "Error: design file not found"  exit 2
mustmatch lint nonexistent.md → "Error: spec file not found"  exit 2
mustmatch (no args)           → "Error: expected value required"  exit 2
mustmatch test --timeout notanumber docs/ → argparse error  exit 2
```

All error messages are descriptive and exit codes match the convention (2 for usage/validation errors, 1 for assertion failures).

**verify-matrix with real file:** Ran against `.march/design-final.md`; all 6 file references resolved correctly (exit 0).

**lint on live specs:**
- `docs/02-cli-assertions.md` → 1 finding (short "beta" pattern on line 11) — pre-existing, not a regression
- `docs/10-verify-matrix.md` → 2 findings (short "design" and "--json" patterns) — pre-existing, exit 1

## Edge Cases Tested

| Case | Input | Result |
| --- | --- | --- |
| Nonexistent design file | `verify-matrix --repo-root . nonexistent.md` | exit 2, clear error |
| Nonexistent spec file | `lint nonexistent.md` | exit 2, clear error |
| No args | `mustmatch` | exit 2, "expected value required" |
| Invalid int flag | `--timeout notanumber` | exit 2, argparse error |
| Match failure | `echo "hello" \| mustmatch "goodbye"` | exit 1, diff output |
| Match success | `echo "hello" \| mustmatch like "hello"` | exit 0, no output |
| Negative match | `echo "hello" \| mustmatch not like "error"` | exit 0, no output |

## Spec Audit

**Specs reviewed:** `docs/01-11` and `README.md` — 33 tests, all passing.

**Coverage:** All new CLI behaviors introduced in tickets 001-003 have executable specs. This release ticket adds no new behavior, only:
- `CHANGELOG.md` (no spec needed — external artifact)
- macOS runner label fix in release.yml (CI config, not testable in executable specs)

**Spec gaps (design-acknowledged):** The proof matrix in `design-final.md` correctly identifies 5 external spec gaps (GitHub Actions, PyPI visibility, fresh-venv install, remote git state, installed CLI from public wheel). These are outside the executable spec scope by design.

**Assertion strength:** Existing assertions are appropriately specific. No weak assertions found that needed strengthening.

**Counts before/after:**
- Executable-doc tests: 33 (unchanged)
- Rust unit tests: 30 (unchanged)

## Regression Results

Full suite `make test` passes: `33 passed in 4.42s`. No regressions in any existing feature.

## Test Suite

`make check < /dev/null 2>&1` → PASS (0.06s)
`make test` (via `make test`) → PASS (`33 passed in 4.42s`, wall 12.1s)

## Documentation

`CHANGELOG.md` reviewed — covers all required items:
- Added: `verify-matrix`, `lint`, `docs/10-verify-matrix.md`, `docs/11-lint.md`
- Fixed: pytest autodiscovery, nested fenced code block parsing
- Changed: quality bar bootstrapped

Format is clean: `# Changelog`, `## 0.0.4`, `### Added/Fixed/Changed` sections. No prose errors.

`README.md` unchanged — no updates required for this release step.

Help text unchanged — verified `--help` output for all subcommands.

## Issues Found and Fixed

**No worktree repairs needed.** All prior code-review repairs were already committed:
- macOS runner label `macos-13` → `macos-15-intel` (commit `97426da`)
- `CHANGELOG.md` added (commit `fc970d5`)
- release.yml `workflow_dispatch` tag input added (part of prior repair)

The GitHub Actions build jobs all succeeded after the runner fix. No further repo changes were needed.

## Issues Filed

1. `planning/mustmatch/issues/004-pypi-trusted-publisher.md` — Critical: PyPI trusted publisher not configured; 0.0.4 wheel builds completed but publish failed with `invalid-publisher`. Requires PyPI account action to configure trusted publisher for `genomoncology/mustmatch` with `environment:release`.
2. `planning/mustmatch/issues/004-github-actions-nodejs.md` — Minor: Node.js 20 deprecation warnings in release.yml for actions/checkout@v4, upload-artifact@v4, download-artifact@v4. Deadline June 2, 2026.
3. `planning/mustmatch/issues/004-qb-update.md` — Quality bar update (no baseline changes).

## Quality Bar Updates

Filed `planning/mustmatch/issues/004-qb-update.md`. No baseline changes — all measurements within noise. No fragile area changes. Spec counts unchanged at 33 + 30.

## UX Quality

CLI follows clig.dev conventions throughout:
- Errors go to stderr with actionable messages.
- Exit codes are consistent: 0 success, 1 assertion failure, 2 usage/validation error.
- `--help` works on all subcommands.
- `--version` emits `mustmatch 0.0.4` to stdout.
- `--json` flag available on `verify-matrix` and `lint` for script use.
- No extraneous stdout noise on success.

One pre-existing UX note (not a regression): `mustmatch lint` on `docs/10-verify-matrix.md` exits 1 for short-like-pattern findings that are within the default `--min-like-len` threshold. This is correct behavior, not a bug. The patterns flagged ("design", "--json") are genuinely borderline but were accepted during spec authoring.

Issues filed: 2 (plus 1 qb-update)
