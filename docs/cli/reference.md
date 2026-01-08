# CLI Reference

## Usage

```
command | expect [OPTIONS] EXPECTED
command | expect [OPTIONS] -f FILE
```

Reads stdin (actual output), compares to EXPECTED, exits 0 on match or 1 on mismatch.

## Expected Value Sources

The expected value can come from:

1. **Positional argument**: `expect "hello world"`
2. **File**: `expect -f expected.txt`

## Comparison Modes

### Exact Match (Default)

Compares output exactly (trailing newlines are normalized):

```bash
echo "hello world" | expect "hello world"
```

### Contains (`--contains`)

Checks if output contains a substring:

```bash
python --version 2>&1 | expect --contains "Python"
```

### Regex (`--regex`)

Matches output against a regex pattern:

```bash
mycli build | expect --regex 'completed in \d+\.\d+s'
```

### JSON (`--json`)

Compares single JSON values semantically. Field order doesn't matter:

```bash
echo '{"b": 2, "a": 1}' | expect --json '{"a": 1, "b": 2}'
```

### JSONL Semantic (`--jsonl`)

Compares JSON Lines output semantically. Field order within objects doesn't matter:

```bash
echo '{"b": 2, "a": 1}' | expect --jsonl '{"a": 1, "b": 2}'
```

Record order **does** matter:

```bash
# This will FAIL - wrong order
echo '{"id": 1}
{"id": 2}' | expect --jsonl '{"id": 2}
{"id": 1}'
```

### JSONL Set (`--jsonl-set`)

Order-independent JSONL comparison (multiset semantics):

```bash
echo '{"id": 1}
{"id": 2}' | expect --jsonl-set '{"id": 2}
{"id": 1}'
```

### JSONL Key (`--jsonl-key FIELD`)

Match records by a key field, then compare:

```bash
mycli list | expect --jsonl-key id '{"id": 2, "name": "bob"}
{"id": 1, "name": "alice"}'
```

### JSONL Contains (`--jsonl-contains`)

Checks if output contains expected records (partial field matching):

```bash
echo '{"id": 1, "name": "alice"}
{"id": 2, "name": "bob"}' | expect --jsonl-contains '{"id": 2}'
```

## Normalization Options

| Flag | Description |
|------|-------------|
| `--strip-ansi` | Remove ANSI escape sequences (colors) |
| `--normalize-newlines` | Convert CRLF to LF |
| `--trim` | Strip leading/trailing whitespace |
| `--collapse-whitespace` | Collapse whitespace runs to single spaces |
| `--ignore-case`, `-i` | Case-insensitive comparison |

Example:

```bash
# Handle colored output with flexible whitespace
mycli status | expect --strip-ansi --collapse-whitespace "status: OK"
```

## Pattern Transformation

### Replace (`--replace REGEX REPL`)

Replace patterns before comparison (repeatable):

```bash
mycli run | expect --replace '\d+ms' '<time>' "completed in <time>"
```

### Redact (`--redact REGEX`)

Replace patterns with `<redacted>` (repeatable):

```bash
mycli token | expect --redact 'token_[a-z0-9]+' "auth: <redacted>"
```

## JSON Options

### Ignore Paths (`--json-ignore PATH`)

Ignore JSON paths during comparison (repeatable):

```bash
mycli audit | expect --json --json-ignore '$.timestamp' '{"status": "ok"}'
```

Path syntax:
- `$.field` - Top-level field
- `$.user.name` - Nested field
- `$[0].id` - Array index

## Output Options

| Flag | Description |
|------|-------------|
| `-q`, `--quiet` | Suppress diff output on failure |
| `--color auto\|always\|never` | Colorize output (default: auto) |
| `--diff-context N` | Lines of context in diff (default: 3) |

## File Options

| Flag | Description |
|------|-------------|
| `-f`, `--expected-file FILE` | Read expected from file |
| `--update` | Update expected file on mismatch (requires `-f`) |

### Snapshot Updates

```bash
# Update expected file when output changes
mycli help | expect -f expected/help.txt --update
```

## All Options

| Flag | Description |
|------|-------------|
| `EXPECTED` | Expected output (positional) |
| `-f`, `--expected-file FILE` | Read expected from file |
| `--contains` | Substring match |
| `--regex` | Regex pattern match |
| `--json` | JSON semantic comparison |
| `--jsonl` | JSONL semantic comparison |
| `--jsonl-set` | JSONL unordered set comparison |
| `--jsonl-key FIELD` | JSONL key-based comparison |
| `--jsonl-contains` | JSONL subset matching |
| `--strip-ansi` | Remove ANSI escape codes |
| `--normalize-newlines` | Convert CRLF to LF |
| `--trim` | Strip leading/trailing whitespace |
| `--collapse-whitespace` | Collapse whitespace runs |
| `--ignore-case`, `-i` | Case-insensitive |
| `--replace REGEX REPL` | Replace pattern (repeatable) |
| `--redact REGEX` | Redact pattern (repeatable) |
| `--json-ignore PATH` | Ignore JSON path (repeatable) |
| `-q`, `--quiet` | Suppress error output |
| `--color auto\|always\|never` | Color mode |
| `--diff-context N` | Diff context lines |
| `--update` | Update expected file |
| `--version` | Show version |
| `--help` | Show help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Match - assertion passed |
| 1 | Mismatch - assertion failed |
| 2 | Error - invalid arguments or file error |

## Multi-line Expectations

### Using Files (Recommended)

```bash
mycli help | expect -f docs/expected/help.txt
```

### Using Heredoc

```bash
echo "line 1
line 2
line 3" | expect "$(cat <<'EOF'
line 1
line 2
line 3
EOF
)"
```

### Using JSONL Mode

```bash
echo '{"id": 1}
{"id": 2}' | expect --jsonl '{"id": 1}
{"id": 2}'
```

## Tips

1. **Redirect stderr for version commands**:
   ```bash
   python --version 2>&1 | expect --contains "Python"
   ```

2. **Use `pipefail` to catch command failures**:
   ```bash
   set -o pipefail
   failing_cmd | expect "never reached"
   ```

3. **Use `--strip-ansi` for colored output**:
   ```bash
   mycli status | expect --strip-ansi --contains "OK"
   ```

4. **Use `--replace` for volatile content**:
   ```bash
   mycli build | expect --replace '\d+ms' '<time>' "Built in <time>"
   ```

5. **Use `--json-ignore` for timestamps**:
   ```bash
   mycli status | expect --json --json-ignore '$.updated_at' '{"healthy": true}'
   ```

6. **Use `-f` for cleaner multi-line expectations**:
   ```bash
   mycli help | expect -f expected/help.txt
   ```

7. **Use `--update` to maintain snapshots**:
   ```bash
   mycli help | expect -f expected/help.txt --update
   ```
