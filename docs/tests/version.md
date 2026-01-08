# Version Tests

Tests for version information.

## Version flag

```bash
outmatchall --version | outmatchall --contains "0.2.0"
```

## Version exits cleanly

```bash
outmatchall --version
test $? -eq 0
```
