# Installed wheel smoke

This smoke document is intentionally tiny and self-contained. It proves the
installed `mustmatch` command can run a stdin assertion and can execute a nested
Markdown document materialized from an embedded fixture.

## Installed entry points

````markdown file=nested-smoke.md
# Nested smoke

```bash
printf 'nested package smoke\n' | mustmatch like "package smoke"
```
````

```bash
printf 'installed entry point\n' | mustmatch like "entry point"
```

```bash
mustmatch test nested-smoke.md | mustmatch like "1 passed"
```
