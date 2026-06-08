# Verifying a proof matrix

`mustmatch verify-matrix DESIGN --repo-root ROOT` checks that the backticked file
references in a design document's tables actually resolve inside the repo. It
reports each reference as `ok`, `missing`, or `invalid` (outside the repo), and
ignores things that look like routes, commands, or environment variables rather
than repo paths.

## Help

```bash
mustmatch verify-matrix --help | mustmatch -i like "verify-matrix
design
--repo-root
--json"
```

## Resolving references

The embedded design has a table referencing one file that exists (`README.md`,
also embedded here), one that does not (`docs/none.md`), and a URL that is not a
repo path and is left out of the reference set. One missing reference makes the
command exit `1`.

```text file=README.md
# Example repo
```

```text file=design.md
| behavior | location                   |
| -------- | -------------------------- |
| present  | `README.md`                |
| absent   | `docs/none.md`             |
| route    | `https://example.test/v1`  |
```

```bash
mustmatch verify-matrix design.md --repo-root . --json | mustmatch like '"references_checked": 2
"failure_count": 1
"reference": "README.md"
"status": "ok"
"reference": "docs/none.md"
"status": "missing"'
mustmatch verify-matrix design.md --repo-root . >/dev/null 2>&1 && code=0 || code=$?
printf 'exit=%s\n' "$code" | mustmatch like "exit=1"
```

## Escaping expected-value paths

A proof matrix can also cite a path as an expected value rather than as a real
surface reference. Put the marker `expected-missing` in the same table cell as
the expected path. The verifier then checks the real surface references and leaves
the marked expected value out of both JSON and human results.

```text file=README.md
# Example repo
```

```text file=escaped-design.md
| behavior | location    | assertion value                         |
| -------- | ----------- | --------------------------------------- |
| present  | `README.md` | real checked surface                    |
| expected |             | expected-missing `docs/none.md`         |
```

```bash run id=escaped-json exit=0
mustmatch verify-matrix escaped-design.md --repo-root . --json
```

```text expect=escaped-json contains
"references_checked": 1
"failure_count": 0
"reference": "README.md"
"status": "ok"
```

```bash run id=escaped-human exit=0
mustmatch verify-matrix escaped-design.md --repo-root .
```

```text expect=escaped-human contains
OK line
README.md
```

```text expect=escaped-human not-contains
docs/none.md
```
