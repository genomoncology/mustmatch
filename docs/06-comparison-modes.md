# Comparison Modes

mustmatch auto-detects comparison mode from expected-value syntax. You can still influence behavior with grammar (`like`, `not`) and flags (`-i`). These examples verify mode selection boundaries.

## Exact, Contains, And Negation

Plain strings default to exact mode. `like` performs contains checks, and `not` flips the final expectation. When the expected plain-text value spans multiple lines, contains mode still applies, but each non-empty expected line is checked independently. In that multiline plain-text case, `not like` means none of those expected lines may appear.

```bash
echo "ready" | mustmatch "ready"
echo "ready now" | mustmatch like "ready"
echo "ready now" | mustmatch not like "failed"
printf 'ready now\nstill healthy\n' | mustmatch like "ready
healthy"
printf 'ready now\nstill healthy\n' | mustmatch not like "failed
panic"
```

## Regex And JSON Family

Regex mode is activated by slash-delimited literals. JSON objects and arrays are matched semantically, and JSONL is detected when expected content has multiple JSON-object lines. Multi-line JSONL `like` uses subset semantics per expected object, not plain-text substring matching.

```bash
echo "2026-02-10" | mustmatch "/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/"
printf '{"a":1,"b":2}\n' | mustmatch '{"b":2,"a":1}'
printf '{"event":"start"}\n{"event":"end"}\n' | mustmatch like '{"event":"start"}'
printf '{"a":1,"b":2}\n{"c":3,"d":4}\n' | mustmatch like $'{"a":1}\n{"c":3}'
```
