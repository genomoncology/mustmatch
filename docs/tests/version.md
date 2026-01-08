# Version Tests

Tests for version information.

## Version flag

```bash
outmatch --version | outmatch --contains "0.2.0"
```

## Version exits cleanly

```bash
outmatch --version
test $? -eq 0
```
