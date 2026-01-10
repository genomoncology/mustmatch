# Version

Check the installed version of outmatch.

## Version flag

```bash
outmatch --version | outmatch --contains "0.2.0"
```

## Version exits cleanly

```bash
outmatch --version
test $? -eq 0
```
