# Examples

These are realistic examples you can reuse directly in local scripts and CI steps. They intentionally combine shell tools with mustmatch assertions so failures are easy to diagnose. Use them as patterns for new executable documentation.

## Pipeline Checks

mustmatch works naturally in command chains. This keeps verification close to the command producing output.

```bash
printf "one\ntwo\nthree\n" | tail -1 | mustmatch "three"
printf "alpha,beta,gamma\n" | cut -d, -f2 | mustmatch "beta"
echo "status=ok" | mustmatch like "ok"
```

## Quiet Failure Control

`-q` suppresses mismatch text while preserving exit status. This is useful when you only need pass/fail control flow.

```bash
echo "test" | mustmatch -q "other" || status=$?
echo "${status:-0}" | mustmatch "1"
unset status
```
