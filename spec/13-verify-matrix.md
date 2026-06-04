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
