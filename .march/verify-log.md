Decision: approved
Operator verify pending: no

## Checkpoint Summary

- Read `AGENTS.md` and `CLAUDE.md`; the repo contract is `spec/*.md`, run by `make spec` through the Rust `mustmatch` binary.
- Read `.march/ticket.md`, design draft/final, code log, code-review log, checkpoint state, `.march/contract-red-check.json`, validation profiles, investigation/review notes, and `planning/mustmatch/faq.md`.
- Rebase checks at start and before sign-off found `main`/`origin/main` already contained by the branch; pre-sign-off autostash reapplied cleanly and the ticket diff was re-staged.
- Preflight staged all tracked ticket work with `git add -A`; no untracked worktree files remain.

## Planning/FAQ Watch Results — relevant watching/answered entries probed

- Relevant FAQ watching entry: mustmatch previously diverged from the workspace standard by using `CLAUDE.md`/`docs/` instead of `AGENTS.md`/`spec/*.md`.
- Probe result: the worktree now has `AGENTS.md`, `spec/*.md`, and `make spec`; `make spec` is green with 25 passed.
- Security/safety probes covered malformed config, missing contexts, invalid options, explicit missing paths, empty directories, malformed console examples, and embedded-file path traversal.
- Existing planning issue `~/workspace/planning/mustmatch/issues/007-missing-test-path-exits-zero.md` already covers the observed explicit-missing-path behavior after the rename (`mustmatch test <missing-path>` exits 0 with `No markdown files found`), so no duplicate was filed.

## Exercise Results — ran, inputs, observations

- `cargo run -q -p mustmatch-cli --bin mustmatch -- --help` documented public `mustmatch`, `test`, `lint`, and `verify-matrix` usage.
- `cargo run -q -p mustmatch-cli --bin mustmatch -- --version` printed `mustmatch 0.0.4`.
- `printf 'hello\n' | cargo run -q -p mustmatch-cli --bin mustmatch -- 'hello'` exited 0.
- `printf 'hello\n' | cargo run -q -p mustmatch-cli --bin mustmatch -- like 'world'` exited 1 with a substring-missing diagnostic.
- `printf -- '--help\n' | cargo run -q -p mustmatch-cli --bin mustmatch -- -- '--help'` exited 0, proving expected values beginning with `-` remain usable via `--`.
- `cargo run -q -p mustmatch-cli --bin mustmatch -- test --help` documented runner options.
- `uv tool run --from . mustmatch --version` built/installed the local package and printed `mustmatch 0.0.4`.
- `uv build --out-dir <tmp>` built `mustmatch-0.0.4.tar.gz` and a Linux wheel successfully.

## Edge Cases Tested — specific cases, results

- Unknown top-level option: `--wat` exited 2 with `Error: unknown option: --wat`.
- Invalid timeout: `mustmatch test --timeout nope ...` exited 2 with `Error: --timeout must be an integer`.
- Invalid language: `mustmatch test --lang python ...` exited 2 with `Error: --lang must be all or bash`.
- Explicit missing path: exited 0 with `No markdown files found`; pre-existing UX concern already tracked as planning issue 007.
- Empty directory: exited 0 with `No markdown files found`, preserving current no-tests behavior.
- Embedded file path traversal (`file=../escape.txt`): exited 1 with `file path "../escape.txt" must be relative and stay under the fixture cwd`, and no escaped file was created.
- Malformed `mustmatch.toml`: exited 1 with a TOML parse diagnostic including the config path and parse location.
- Missing context: exited 1 with `No mustmatch context named "absent" in config`.
- Malformed console block: exited 1 with `console mustmatch blocks must start commands with `$ ``.

## Contract Audit — contracts reviewed, gaps found, counts before/after, spec-only result

- Reviewed `spec/01-cli-assertions.md`, `spec/02-rust-runner.md`, `spec/03-rust-quality-commands.md`, and `spec/04-rust-binary-cutover.md`.
- Grepped every `.march/contract-red-check.json` proof location; all eight named `spec/04-rust-binary-cutover.md::...` headings exist.
- Ran `make spec` as the configured `spec-only` profile: green, 25 passed. This covers every `lane: check` entry.
- Ran `mustmatch lint` via the Rust binary on changed specs `spec/02`, `spec/03`, and `spec/04`; all reported 0 findings.
- Assertion-strength audit: changed-surface assertions target command names, PASS labels, make dry-run gate shape, Cargo metadata, pyproject metadata, and removed runtime paths. No verify-authored strengthening or trivia pinning was added.
- Counts before/after in verify: no shipped-contract assertions were added, removed, or edited by verify.
- Gap filed: full-blocking/specs cover packaging metadata but not a real wheel build/install smoke; filed `~/workspace/planning/mustmatch/issues/011-binary-wheel-install-smoke-gate.md` as a reliability ratchet rather than authoring a new assertion here.

## Verify Lane — `lane: verify` entries exercised

No `lane: verify` entries exist in `.march/contract-red-check.json`; operator verification is not pending.

## Regression Results — existing features verified

- `cargo run -q -p mustmatch-cli --bin mustmatch -- test -v tests/fixtures/rust-runner` passed with 27 passed, 1 skipped.
- `cargo run -q -p mustmatch-cli --bin mustmatch -- lint tests/fixtures/rust-quality/lint-clean-directive.md --json` exited 0 with `status: pass` and `finding_count: 0`.
- `cargo run -q -p mustmatch-cli --bin mustmatch -- verify-matrix tests/fixtures/rust-quality/verify-matrix-design.md --repo-root . --json` preserved the expected failure shape: 2 references checked, `README.md` ok, `docs/does-not-exist.md` missing.

## Test Suite — full-blocking result

- Ran the configured `full-blocking` profile exactly once: `make lint && make test && make spec`.
- Result: green. Lint passed, Rust unit/doc tests passed (25 CLI tests, 48 core tests, doc-tests empty), and specs passed (25 passed).

## Documentation — parity audit of docs/help/examples

- Audited `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `Makefile`, `.github/workflows/test.yml`, and live CLI help/version output.
- `rg` found no stale `import mustmatch`, `mustmatch.cli`, `mustmatch.pytest_plugin`, `[project.scripts]`, `python-source`, or `module-name` runtime entry points outside deliberate negative assertions.
- README/help/examples describe the Rust binary, PyPI binary-wheel install continuity, `mustmatch test spec/`, and Rust-only repo gates.

## Issues Found and Fixed — fixes + proof

No bounded in-worktree runtime or documentation defects required repair during verify.

## Issues Filed — list with paths

- `~/workspace/planning/mustmatch/issues/011-binary-wheel-install-smoke-gate.md` — reliability ratchet for a binary-wheel build/install smoke outside executable Markdown specs.

## Planning Updates — concrete issues filed or FAQ watching proposal

- Filed the packaging smoke-gate issue above.
- Ran `/home/ian/workspace/scripts/lint-planning.sh mustmatch`; result: all clean.
- No FAQ watching update needed; the prior dogfood-standard watching item is directly resolved/probed by this cutover.

## UX Quality — CLI/UI assessment

- CLI help is concise and script-friendly for top-level assertions and `test` options.
- Error messages for invalid options, malformed config, missing context, malformed console blocks, and fixture path traversal are actionable and do not expose secrets.
- Explicit missing path still exits 0; this remains a pre-existing tracked UX issue (`007-missing-test-path-exits-zero.md`) and did not block this cutover.

Issues filed: 1
