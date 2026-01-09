# Pytest Plugin Tests

Tests that verify the outmatch pytest plugin loads and works correctly.

## Plugin is registered

```bash
pytest docs/tests/version.md --collect-only 2>&1 | outmatch --contains "outmatch-"
```

## Collects markdown files

```bash
pytest docs/tests/version.md --collect-only -q 2>&1 | outmatch --contains "2 tests"
```

## Runs markdown tests

```bash
pytest docs/tests/version.md -v 2>&1 | outmatch --contains "2 passed"
```

## Shows test names from headings

```bash
pytest docs/tests/version.md --collect-only 2>&1 | outmatch --contains "Version flag"
```

## Reports correct file location

```bash
pytest docs/tests/version.md --collect-only 2>&1 | outmatch --contains "version.md"
```
