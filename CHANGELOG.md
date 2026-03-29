# Changelog

## 0.0.4

### Added

- `mustmatch verify-matrix` to validate proof-matrix file references inside
  Markdown design documents.
- `mustmatch lint` to report assertion mistakes and shell syntax problems in
  Markdown specs without executing their code blocks.
- Executable specs for the new CLI surface in `docs/10-verify-matrix.md` and
  `docs/11-lint.md`.

### Fixed

- `pytest` plugin autodiscovery via the `pytest11` entry point for editable
  installs.
- Nested fenced code blocks in the Rust Markdown parser so nested fences keep
  their intended CommonMark structure.

### Changed

- Bootstrapped the mustmatch team quality bar for this repository.
