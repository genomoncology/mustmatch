# CLI Documentation Testing Approaches

Comparing different ways to show AND verify CLI output in documentation.

---

## Approach A: Pipe to assertion tool (works today)

```bash
# Simple text output
mycommand --version | expect "mycommand 1.0.0"

# JSONL output
echo '{"input": "data"}' | mycommand process --format jsonl \
  | expect --jsonl '{"output": "result", "status": "ok"}'

# Check output contains substring
mycommand --help | expect --contains "Usage:"
```

**Pros:**
- Works with default mktestdocs bash executor (no custom code)
- Self-contained, single block
- Shows both the command AND expected output

**Cons:**
- Users see the assertion tool in docs
- Slightly more verbose than "pure" output display

---

## Approach B: Following expected block (needs custom executor)

````markdown
```bash
mycommand --version
```

```expected
mycommand 1.0.0
```
````

**Pros:**
- Very clean separation
- Shows output exactly as user would see it
- Natural documentation style

**Cons:**
- Requires custom mktestdocs executor
- Two blocks per example

---

## Approach C: Inline comment (needs custom executor)

```bash
mycommand --version
# OUTPUT: mycommand 1.0.0
```

**Pros:**
- Single block
- Compact

**Cons:**
- Requires custom executor
- Less readable for multi-line output
- Comments feel like "metadata" not "output"

---

## Approach D: Show output, test separately

````markdown
```bash
mycommand --version
```

Output:
```text
mycommand 1.0.0
```
````

Then in a separate test file, verify it.

**Pros:**
- Docs look perfect
- Clear separation of concerns

**Cons:**
- Tests are duplicated/separate from docs
- Can get out of sync

---

## Recommendation

**Approach A (pipe to tool)** is the most practical because:

1. Works TODAY with mktestdocs - no custom executor needed
2. Single block = single test
3. Shows both command AND expected output
4. The assertion tool (`expect`) is short and reads naturally

The documentation reads as: "Run this command, expect this output."

### Making it cleaner

If we name the tool `expect`, docs look like:

```bash
# Version check
mycommand --version | expect "mycommand 1.0.0"

# Process data
echo '{"input": "data"}' | mycommand process --format jsonl \
  | expect --jsonl '{"output": "result", "status": "ok"}'

# Help contains usage
mycommand --help | expect --contains "Usage:"
```

This is reasonably readable AND actually tests the output.

---

## What `expect` supports

1. **Exact match** (default): `cmd | expect "output"`
2. **Contains**: `cmd | expect --contains "substring"`
3. **JSONL semantic**: `cmd | expect --jsonl '{"field": "value"}'`
4. **JSONL subset**: `cmd | expect --jsonl-contains '{"id": 1}'`
5. **Multi-line via heredoc**:
   ```bash
   cmd | expect "$(cat <<'EOF'
   line 1
   line 2
   EOF
   )"
   ```
