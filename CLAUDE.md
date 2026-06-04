# mustmatch

Single Rust CLI for assertion pipelines and executable Markdown specs.

## Build And Test

```bash
make lint
make test
make spec
```

## Project Structure

```text
mustmatch/
├── crates/
│   ├── mustmatch-core/     # Rust core: parser, comparator, normalizer, coercion, fixture
│   └── mustmatch-cli/      # Rust `mustmatch` CLI binary
├── spec/                   # Behavioral contract run by `mustmatch test`
├── tests/fixtures/         # Rust runner and quality-command fixtures
└── pyproject.toml          # maturin binary-wheel packaging metadata
```

## CLI Features

- `mustmatch [not] [like] EXPECTED` for stdin assertions
- `mustmatch test spec/` for executable Markdown specs
- `mustmatch lint` for static spec-quality checks
- `mustmatch verify-matrix` for design proof-matrix reference checks

## Version

Current: **0.1.0**
