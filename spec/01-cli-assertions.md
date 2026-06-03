# mustmatch CLI Assertions

`mustmatch` asserts that a command's output matches an expected value. Pipe a
command's stdout in and compare it — exactly, as a substring with `like`, or against
a regular expression. This is the surface every consuming repo drives through
`make spec`.

## Exact match

An expected value with no modifier must match the output exactly (after
normalization).

```bash
echo "hello" | mustmatch "hello"
```

## Substring match with `like`

`like` passes when the expected text appears anywhere in the output, so a spec can
assert a meaningful fragment instead of pinning the whole line.

```bash
echo "hello world" | mustmatch like "world"
```

## Regex match

An expected value wrapped in slashes is treated as a regular expression — useful for
asserting structural shape (a version string, an identifier) rather than a volatile
exact value.

```bash
echo "v1.2.3" | mustmatch "/^v[0-9]+[.][0-9]+[.][0-9]+$/"
```
