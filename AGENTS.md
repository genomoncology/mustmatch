# AGENTS.md — mustmatch

mustmatch is the workspace's behavioral-contract runner: a Rust core
(`crates/mustmatch-core` — parser, comparator, normalizer, coercion, fixture) with a
CLI that asserts command output and runs executable markdown specs. Every other repo
uses it for `make spec`. Read `CLAUDE.md` at the workspace root for global rules and
`README.md` here for what mustmatch does.

## Behavioral contract

mustmatch's observable surface is its CLI — `… | mustmatch [not] [like] EXPECTED`
assertions and `mustmatch test` running markdown specs. The behavioral contract is
**mustmatch `spec/*.md`**, run via `make spec`: mustmatch dogfoods its own runner. The
reviewer scopes the reverse-traceability audit to `spec/*`.

Error paths, parser internals, and the comparison engine are **unit tests** — `cargo
test` for the Rust core, `pytest tests/` for the Python CLI. The legacy `docs/` tree is
executable documentation run under pytest and is being migrated into `spec/`.

## The gates (done = all green)

- `make lint` — `ruff` (Python); `cargo fmt --check` + `cargo clippy -- -D warnings` as
  Rust gates land.
- `make test` — unit tests: `pytest tests/` (and `docs/` during the migration) and
  `cargo test`.
- `make spec` — outside-in behavioral contract: `mustmatch test spec/`.

## Layout & conventions

- `crates/mustmatch-core` — Rust engine (parse / compare / normalize / coerce / fixture).
- `crates/mustmatch-cli` — standalone Rust assertion binary (growing a `test` runner).
- `crates/mustmatch-python` — PyO3 bindings exposing the core as `mustmatch._core`.
- `src/mustmatch/` — Python CLI (`match` / `test` / `lint` / `verify-matrix`), runtime,
  pytest plugin.
- `spec/` — the behavioral contract. `docs/` — legacy executable docs (migrating).
- Public repo, published to PyPI (MIT): no domain content, no absolute local paths.

## How work arrives

Via March tickets (team `mustmatch`). Repo setup — this file, the Makefile gate wiring,
the spec harness — lives on `main` and is not rebuilt inside feature tickets; specs and
gates evolve with the behavior they cover.
