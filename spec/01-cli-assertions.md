# CLI assertions

`mustmatch` reads a command's output on stdin and asserts it matches one
expected value. Pipe stdout in and compare it — exactly, as a substring with
`like`, negated with `not`, or case-insensitively with `-i`. This is the surface
every consuming repo drives through `make spec`, and the examples below run that
way: each fenced `bash` block executes only because it pipes into `mustmatch`.

## Exact match

With no modifier the expected value must equal the output exactly, after
normalization (see `04-normalization.md` — a trailing newline is trimmed).

```bash
printf 'hello\n' | mustmatch "hello"
```

## Substring match with `like`

`like` passes when the expected text appears anywhere in the output, so a spec
can assert the fragment that matters instead of pinning a whole volatile line.

```bash
printf 'listening on http://127.0.0.1:8080\n' | mustmatch like "listening on"
```

## Negation with `not`

`not` inverts the result: the assertion passes when the expected value is
**absent**. Pair it with `like` to forbid a substring.

```bash
printf 'all systems go\n' | mustmatch not like "error"
```

## Case-insensitive with `-i`

`-i` folds case on both sides before comparing. It composes with `like` and
`not`.

```bash
printf 'READY\n' | mustmatch -i "ready"
printf 'Server: nginx\n' | mustmatch -i like "SERVER"
```

## A literal expected value after `--`

`--` ends option parsing, so an expected value that begins with a dash is taken
literally instead of being read as a flag.

```bash
printf -- '-v\n' | mustmatch -- "-v"
```

## Exit codes

`mustmatch` exits `0` on a match, `1` on a mismatch, and `2` on a usage error.
Guard the non-zero cases (the block runs under `set -e`) and assert the codes.

```bash
printf 'ready\n' | mustmatch "ready"      && pass=$?  || pass=$?
printf 'ready\n' | mustmatch -q "nope"    && miss=0   || miss=$?
printf ''        | mustmatch -q           && usage=0  || usage=$?
printf 'match=%s mismatch=%s usage=%s\n' "$pass" "$miss" "$usage" \
  | mustmatch like "match=0 mismatch=1 usage=2"
```
