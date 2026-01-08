# Version Tests

Tests for version information.

## Version flag

```bash
expect --version | expect --contains "0.2.0"
```

## Version exits cleanly

```bash
expect --version
test $? -eq 0
```
