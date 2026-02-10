# Comparison Modes

mustmatch auto-detects comparison mode from expected-value syntax. You can still influence behavior with grammar (`like`, `not`) and flags (`-i`). These examples verify mode selection boundaries.

## Exact, Contains, And Negation

Plain strings default to exact mode. `like` performs contains checks, and `not` flips the final expectation.

```bash
echo "ready" | mustmatch "ready"
echo "ready now" | mustmatch like "ready"
echo "ready now" | mustmatch not like "failed"
```

## Regex And JSON Family

Regex mode is activated by slash-delimited literals. JSON objects and arrays are matched semantically, and JSONL is detected when expected content has multiple JSON-object lines.

```bash
echo "2026-02-10" | mustmatch "/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/"
printf '{"a":1,"b":2}\n' | mustmatch '{"b":2,"a":1}'
printf '{"event":"start"}\n{"event":"end"}\n' | mustmatch like '{"event":"start"}'
```
