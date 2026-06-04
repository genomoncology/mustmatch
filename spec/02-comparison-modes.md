# Comparison modes

`mustmatch` chooses one of five comparison modes from the **shape of the expected
value**, then `like` decides between strict and subset/substring matching:

| Expected looks like | Mode | `like` effect |
|---------------------|------|---------------|
| plain text | exact | substring |
| `/pattern/flags` | regex | (regex always) |
| one `{ … }` / `[ … ]` | JSON | subset |
| several `{ … }` lines | JSONL | per-object subset |

## Exact text (default)

Plain text compares for full equality after normalization.

```bash
printf 'status: ready\n' | mustmatch "status: ready"
```

## Substring with `like`

On plain text, `like` switches to "appears anywhere".

```bash
printf 'alpha beta gamma\n' | mustmatch like "beta"
```

## Regular expressions

An expected value wrapped in slashes is a regex — assert structural shape rather
than a brittle exact value.

```bash
printf 'build 2026\n' | mustmatch "/build [0-9]{4}/"
```

The `i` flag makes the pattern case-insensitive.

```bash
printf 'ERROR: disk full\n' | mustmatch "/error: .*/i"
```

Only the `i` flag is supported; any other flag is rejected with exit `1` and a
message naming the offending flag.

```bash
out=$(printf 'x\n' | mustmatch "/x/g" 2>&1) && code=0 || code=$?
printf 'code=%s\n' "$code"      | mustmatch like "code=1"
printf '%s\n'      "$out"       | mustmatch like "Unsupported regex flags: g"
```

## JSON subset with `like`

When the expected value is a JSON object, `like` checks that it is a **subset**
of the actual JSON — the keys you name must match; extra keys are ignored. Tools
like `jq` are handy for producing the JSON under test.

```bash
printf '{"name":"widget","status":"active","count":3}\n' \
  | mustmatch like '{"status":"active"}'
jq -c -n '{service:"api",ready:true,port:8080}' | mustmatch like '{"ready":true}'
```

## Exact JSON ignores key order

Without `like`, JSON compares for deep equality — but key order does not matter,
because both sides are parsed before comparison.

```bash
printf '{"b":2,"a":1}\n' | mustmatch '{"a":1,"b":2}'
```

## JSONL (one object per line)

Several `{ … }` lines are compared as JSON Lines. With `like`, each expected
object must be a subset of some actual line.

```bash
printf '{"id":1,"ok":true}\n{"id":2,"ok":false}\n' | mustmatch like '{"id":1}
{"id":2,"ok":false}'
```
