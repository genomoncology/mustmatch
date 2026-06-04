# Linting specs

`mustmatch lint SPEC` inspects a Markdown spec **without executing it** and
reports stable, structured findings: an unsupported assertion mode, a `like`
literal too short to be meaningful, and shell blocks that fail `bash -n` syntax
checking. It exits `0` when clean and `1` when it finds something.

## Help

```bash
mustmatch lint --help | mustmatch -i like "mustmatch lint
spec
--min-like-len
--json"
```

## Reported findings

The embedded spec below has one of each problem: `mustmatch json` (an
unsupported mode), a 4-character `like` literal (under the default minimum of
10), and a broken `if`/`fi`. Lint reports three findings as JSON and exits `1`.

````markdown file=lint-target.md
```bash
echo '{"status":"ok"}' | mustmatch json
echo alpha | mustmatch like "beta"
if then
fi
```
````

```bash
mustmatch lint lint-target.md --json | mustmatch like '"status": "fail"
"finding_count": 3
"invalid-mustmatch-mode"
"short-like-pattern"
"invalid-shell-syntax"'
mustmatch lint lint-target.md >/dev/null 2>&1 && code=0 || code=$?
printf 'exit=%s\n' "$code" | mustmatch like "exit=1"
```

## A clean spec

A spec with a long-enough `like` literal, a supported mode, and valid shell
reports no findings and exits `0`.

````markdown file=lint-clean.md
```bash
printf 'hello world\n' | mustmatch like "hello world here"
```
````

```console mustmatch
$ mustmatch lint lint-clean.md --json
"status": "pass"
"finding_count": 0
```
