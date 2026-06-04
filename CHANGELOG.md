# Changelog

## 0.0.4

### Added

- `mustmatch verify-matrix` to validate proof-matrix file references inside
  Markdown design documents.
- `mustmatch lint` to report assertion mistakes and shell syntax problems in
  Markdown specs without executing their code blocks.
- Executable specs for the Rust CLI surface in `spec/`.

### Changed

- Cut over the shipped command to a single Rust binary named `mustmatch`.
- PyPI packaging now builds the Rust binary with maturin `bindings = "bin"`.
- Repo gates are Rust-only: `make lint`, `make test`, and `make spec`.

### Removed

- Removed the Python CLI/runtime, pytest plugin, and PyO3 binding crate from this
  repo.
