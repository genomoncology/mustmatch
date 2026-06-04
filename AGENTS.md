# AGENTS.md — mustmatch

mustmatch is the workspace's behavioral-contract runner: a Rust core
(`crates/mustmatch-core` — parser, comparator, normalizer, coercion, fixture) plus a
single Rust CLI binary named `mustmatch` that asserts command output and runs
executable markdown specs. Every other repo uses it for `make spec`. Read
`CLAUDE.md` at the workspace root for global rules and `README.md` here for what
mustmatch does.

## Behavioral contract

mustmatch's observable surface is its CLI — `… | mustmatch [not] [like] EXPECTED`
assertions and `mustmatch test` running markdown specs. The behavioral contract is
**mustmatch `spec/*.md`**, run via `make spec`: mustmatch dogfoods its own runner. The
reviewer scopes the reverse-traceability audit to `spec/*`.

Error paths, parser internals, and the comparison engine are **unit tests** — `cargo
test` for the Rust core and CLI. Executable documentation lives in `spec/` and is run
by the Rust binary.

## The gates (done = all green)

- `make lint` — `cargo fmt --check` + `cargo clippy -- -D warnings`.
- `make test` — unit tests: `cargo test`.
- `make spec` — outside-in behavioral contract: `mustmatch test spec/` through the
  Rust binary.

## Layout & conventions

- `crates/mustmatch-core` — Rust engine (parse / compare / normalize / coerce / fixture).
- `crates/mustmatch-cli` — standalone Rust `mustmatch` binary (`match` / `test` /
  `lint` / `verify-matrix`).
- `spec/` — the behavioral contract.
- Public repo, published to PyPI (MIT): no domain content, no absolute local paths.

## How work arrives

Via March tickets (team `mustmatch`). Repo setup — this file, the Makefile gate wiring,
the spec harness — lives on `main` and is not rebuilt inside feature tickets; specs and
gates evolve with the behavior they cover.
