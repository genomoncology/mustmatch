# CLI Assertions

The CLI compares normalized stdin against one expected value. It supports exact, contains, regex, JSON, and negated checks with a compact grammar. This file exercises each mode directly from shell commands.

## Exact And Contains

Exact mode is the default. Adding `like` switches to substring semantics for plain text values.

```bash
echo "alpha" | mustmatch "alpha"
echo "alpha beta" | mustmatch like "beta"
echo "alpha beta" | mustmatch not like "gamma"
```

## Multi-line Like

Multi-line plain-text `like` keeps contains mode, but it treats each non-empty expected line as its own substring assertion. That keeps shell specs compact while still reporting which lines are missing or forbidden.

```bash
printf 'PARK2 | causes | omim\nPINK1 | causes | omim\n' | mustmatch like "PARK2
PINK1
causes"

printf '  PARK2 | causes\n  PINK1 | causes\n' | mustmatch like "  PARK2

  PINK1"

printf 'HELLO there\nsome WORLD\n' | mustmatch -i like "hello
world"
```

Failures still report the exact lines that made the assertion fail, including the separate rule for negated multi-line checks.

```bash
tmpdir="$(mktemp -d)"
stderr="$tmpdir/stderr.txt"
if printf 'PARK2 | causes | omim\n' | mustmatch like $'PARK2\nNOTCH1' 2>"$stderr"; then
  echo "multi-line like unexpectedly passed"
  exit 1
fi
cat "$stderr" | mustmatch like "Missing 1 of 2 expected lines:"
cat "$stderr" | mustmatch like '"NOTCH1"'
rm -rf "$tmpdir"
```

```bash
tmpdir="$(mktemp -d)"
stderr="$tmpdir/stderr.txt"
if printf 'PARK2 | causes | omim\n' | mustmatch not like $'PARK2\nNOTCH1' 2>"$stderr"; then
  echo "multi-line not like unexpectedly passed"
  exit 1
fi
cat "$stderr" | mustmatch like "Found 1 of 2 forbidden lines:"
cat "$stderr" | mustmatch like '"PARK2"'
rm -rf "$tmpdir"
```

## Regex

Regex mode uses `/pattern/flags` syntax. The `i` flag is supported and can also be combined with `--ignore-case`.

```bash
echo "v1.2.3" | mustmatch "/^v[0-9]+[.][0-9]+[.][0-9]+$/"
echo "HELLO" | mustmatch "/^hello$/i"
echo "HELLO" | mustmatch -i "/^hello$/"
```

## JSON And Subset

JSON comparisons are semantic and ignore object key order. Using `like` with JSON checks for subset containment.

```bash
printf '{"b":2,"a":1}\n' | mustmatch '{"a":1,"b":2}'
printf '{"status":"ok","count":42}\n' | mustmatch like '{"status":"ok"}'
printf '{"items":[{"id":1},{"id":2}]}\n' | mustmatch like '{"items":[{"id":2}]}'
```
