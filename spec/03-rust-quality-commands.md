# Rust Quality Commands

`mustmatch-cli lint` and `mustmatch-cli verify-matrix` provide the Rust binary
versions of mustmatch's static quality checks. They read Markdown files, report
stable structured findings, and do not execute documentation examples.

## Lint help

The lint command documents the spec path it inspects and the JSON/options a user
can rely on from scripts.

```bash
cargo run -q -p mustmatch-cli -- lint --help | mustmatch -i like "mustmatch-cli lint
spec
--min-like-len
--json"
```

## Lint reports assertion and shell findings

Lint reports unsupported assertion modes, too-short `like` literals, and shell
syntax problems from the same Markdown file. Findings are reported as structured
rule names so a caller can decide how to display or aggregate them.

```console mustmatch exit=1
$ cargo run -q -p mustmatch-cli -- lint ../tests/fixtures/rust-quality/lint-findings.md --json
"status": "fail"
"finding_count": 3
"rule": "invalid-mustmatch-mode"
"rule": "short-like-pattern"
"rule": "invalid-shell-syntax"
```

## Lint accepts directive-bearing clean shell fences

Shell fences remain lintable when directives follow the language token. A clean
file exits successfully and reports no findings.

```console mustmatch
$ cargo run -q -p mustmatch-cli -- lint ../tests/fixtures/rust-quality/lint-clean-directive.md --json
"status": "pass"
"finding_count": 0
```

## Verify-matrix help

The verify-matrix command documents the design file it inspects, the repo root
used to resolve references, and the JSON output mode for automation.

```bash
cargo run -q -p mustmatch-cli -- verify-matrix --help | mustmatch -i like "mustmatch-cli verify-matrix
design
--repo-root
--json"
```

## Verify-matrix resolves only repo-like references

Proof matrices often contain command examples next to file references. The Rust
command checks real repo files, reports missing repo files, and leaves routes,
shell commands, and environment-expanded values out of the reference set.

```console mustmatch exit=1
$ cargo run -q -p mustmatch-cli -- verify-matrix ../tests/fixtures/rust-quality/verify-matrix-design.md --repo-root .. --json
"references_checked": 2
"failure_count": 1
"reference": "README.md"
"status": "ok"
"reference": "docs/does-not-exist.md"
"status": "missing"
```
