# CLI Assertions

The CLI compares normalized stdin against one expected value. It supports exact, contains, regex, JSON, and negated checks with a compact grammar. This file exercises each mode directly from shell commands.

## Exact And Contains

Exact mode is the default. Adding `like` switches to substring semantics for plain text values.

```bash
echo "alpha" | mustmatch "alpha"
echo "alpha beta" | mustmatch like "beta"
echo "alpha beta" | mustmatch not like "gamma"
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
