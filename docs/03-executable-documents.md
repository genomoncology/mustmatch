# Executable Documents

mustmatch treats Markdown as executable documentation. Every `bash` and `python` fence becomes a test case collected by the pytest plugin. This keeps prose and behavior synchronized without duplicating test code.

## Python Blocks

Python blocks run through `exec()` with assertion failures surfaced as test failures. Keep blocks short and focused so failures map clearly to document intent.

```python
value = 2 * 3
assert value == 6
assert isinstance(value, int)
```

## Bash Blocks

Bash blocks execute with `set -e` and fail on non-zero exits. This makes shell examples trustworthy and safe to reuse as command snippets.

```bash
echo "doc blocks are executable" | mustmatch like "executable"
printf "line one\nline two\n" | head -1 | mustmatch "line one"
echo "done" | mustmatch not "error"
```
