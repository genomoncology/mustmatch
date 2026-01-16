# CLI Exec Tests

Tests for the mustmatch exec subcommand.

## Exit code check success

```bash
mustmatch exec --exit-code 0 -- echo hello
```

## Exit code check failure

```bash expect-exit=1
mustmatch exec --exit-code 0 -- false
```

## Stdout exact match

```bash
mustmatch exec --stdout "hello" -- echo hello
```

## Stdout contains with like

```bash
mustmatch exec --stdout-like "hello" -- echo "hello world"
```

## Stdout not contains

```bash
mustmatch exec --stdout-not-like "error" -- echo "success"
```

## Missing assertion exits with code 2

```bash expect-exit=2
mustmatch exec -- echo hello
```

## Missing command exits with error

Typer returns exit code 1 for missing required arguments.

```bash expect-exit=1
mustmatch exec --exit-code 0
```
