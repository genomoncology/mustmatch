# Changelog

## 0.1.0 — 2026-06-04

- CLI assertions for exact, substring, regex, JSON subset, case-insensitive, and negative matches.
- `mustmatch test` for executable Markdown documentation through the Rust CLI.
- Bash table scenarios and scenario outlines for row-driven examples.
- Embedded `file=` fixtures for materializing documented inputs.
- Suite, file, and context lifecycle hooks for setup and teardown outside Markdown prose.
- `xfail` directive marking a block as an expected failure (`xfail="reason"`, plus `strict`): the runner reports `XFAIL`/`XPASS` and counts them in the summary, keeping the suite green for known gaps while flagging an unexpected pass.
- `mustmatch lint` for static spec-quality checks.
- `mustmatch verify-matrix` for proof-matrix reference checks.
