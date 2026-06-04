# Changelog

## 0.1.0 — 2026-06-04

### Added

- Bash table scenarios and scenario outlines for executable Markdown specs (007).
- Embedded fixture files for specs, including guarded fixture paths that stay under
  the temporary fixture directory (008).
- Suite, file, and context lifecycle hooks for spec setup and teardown (009).

### Changed

- Reimplemented `mustmatch lint` and `mustmatch verify-matrix` in Rust while
  preserving the commands introduced in 0.0.4 (010).
- Cut over the shipped `mustmatch` command to a single Rust binary distributed as a
  maturin `bindings = "bin"` wheel with no Python runtime dependency (011).
- Switched repository gates to the Rust binary: `make lint`, `make test`, and
  `make spec` (011).

### Removed

- Removed the Python CLI/runtime, pytest plugin, and PyO3 binding crate from this
  repository (011).

### Notes

- Consumers that still rely on the old pytest plugin should remain pinned to
  `mustmatch==0.0.4` until they migrate their specs to `mustmatch test`.

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
