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

## Nested Fences In Bash Blocks

Bash examples sometimes generate Markdown fixtures that begin another fenced block before the surrounding example is finished. The collector should keep the outer bash example intact so the assertions after the heredoc still run.

```bash
tmpdir="$(mktemp -d)"
fixture="$tmpdir/generated.md"
cat > "$fixture" <<'EOF'
# Generated fixture

```python
print("hello from nested fence")
EOF
printf '%s\n' '```' >> "$fixture"
grep -n '```python' "$fixture" | mustmatch like '```python'
grep -n '^```$' "$fixture" | mustmatch like '```'
echo "nested fence survived" | mustmatch "nested fence survived"
rm -rf "$tmpdir"
```
