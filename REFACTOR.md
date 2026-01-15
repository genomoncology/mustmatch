# CLI Refactor Proposal

## Problem

Current CLI has 25+ flags creating cognitive overload:
- 9 mutually-exclusive comparison modes as separate boolean flags
- JSONL alone has 4 variants (`--jsonl`, `--jsonl-set`, `--jsonl-key`, `--jsonl-contains`)
- Normalization flags that should be defaults
- Poor discoverability of `test` and `exec` subcommands

## Proposed Design

### Grammar

```
mustmatch [-i] [not] [like] EXPECTED
mustmatch test PATHS
mustmatch exec -- CMD
```

### Core Commands

| Command | Description |
|---------|-------------|
| `mustmatch EXPECTED` | Exact match (default) |
| `mustmatch like EXPECTED` | Contains/subset match |
| `mustmatch not EXPECTED` | Must NOT match exactly |
| `mustmatch not like EXPECTED` | Must NOT contain |
| `mustmatch test PATHS` | Run markdown doc tests |
| `mustmatch exec -- CMD` | Execute command and assert |

### Auto-Detection by Syntax

| Pattern | Detected Mode |
|---------|---------------|
| `/pattern/` | Regex |
| `{...}` | JSON object |
| `[...]` | JSON array |
| anything else | String |

### Examples

```bash
# Exact string match
echo "hello" | mustmatch "hello"

# Contains (like)
echo "hello world" | mustmatch like "hello"

# Regex (detected by slashes)
echo "v1.2.3" | mustmatch "/v\d+\.\d+/"

# JSON exact (detected by braces)
echo '{"a":1,"b":2}' | mustmatch '{"a":1,"b":2}'

# JSON subset
echo '{"a":1,"b":2}' | mustmatch like '{"a":1}'

# Case insensitive
echo "HELLO" | mustmatch -i "hello"
echo "HELLO WORLD" | mustmatch -i like "hello"

# Negation
echo "success" | mustmatch not like "error"
echo "success" | mustmatch -i not like "ERROR"

# Regex case-insensitive
echo "Hello" | mustmatch -i "/hello/"
```

### Hardcoded Behaviors

Always enabled (no flags needed):
- Strip ANSI escape sequences
- Normalize newlines (CRLF → LF)

### Remaining Flags

| Flag | Description |
|------|-------------|
| `-i`, `--ignore-case` | Case-insensitive comparison |
| `-q`, `--quiet` | Suppress error output |
| `-f FILE` | Read expected from file |
| `--ignore PATH` | Ignore JSON path (e.g., `$.timestamp`) |
| `--update` | Update expected file on mismatch |

### Subcommands

#### `mustmatch test`

```bash
mustmatch test docs/           # Test all markdown files
mustmatch test -v docs/        # Verbose output
mustmatch test --fail-fast .   # Stop on first failure
```

Flags: `-q`, `-v`, `--fail-fast`, `--parallel N`, `--timeout N`, `--lang`, `--memory`

#### `mustmatch exec`

```bash
mustmatch exec --exit-code 0 -- ./script.sh
mustmatch exec --stdout-like "ok" -- curl localhost
mustmatch exec --stderr-not-like "error" -- make build
```

Flags: `--exit-code`, `--stdout`, `--stdout-like`, `--stderr`, `--stderr-like`, `--timeout`

## Migration

### Phase 1: Add New Grammar (Non-Breaking)

- Add `like` and `not` as subcommands
- Add syntax detection for `/regex/` and `{json}`
- Keep all existing flags working

### Phase 2: Deprecation Warnings

- `--contains` → suggest `like`
- `--regex` → suggest `/pattern/`
- `--json` → suggest `{...}` syntax
- `--not-contains` → suggest `not like`

### Phase 3: Remove (Major Version)

- Remove deprecated flags
- Update all documentation

## Comparison: Before and After

### Before (Current)

```bash
# 9 different mode flags
echo '{"a":1}' | mustmatch --json --jsonl-contains '{"a":1}'
echo "hello" | mustmatch --contains --ignore-case "HELLO"
echo "ok" | mustmatch --not-contains "error"
echo "v1.0" | mustmatch --regex "v\d+"
```

### After (Proposed)

```bash
# Natural language, auto-detection
echo '{"a":1}' | mustmatch like '{"a":1}'
echo "hello" | mustmatch -i like "HELLO"
echo "ok" | mustmatch not like "error"
echo "v1.0" | mustmatch "/v\d+/"
```

## Edge Cases

### Literal Braces or Slashes

If expected value starts with `{`, `[`, or `/` but should be treated as string:

```bash
# Use -f to read from file
echo "{not json" > expected.txt
echo "{not json" | mustmatch -f expected.txt

# Or escape (TBD: may need escape syntax)
```

### Empty JSON

```bash
echo '{}' | mustmatch '{}'
echo '[]' | mustmatch '[]'
```

### JSONL

Multi-line JSON auto-detected when stdin contains newline-delimited JSON objects:

```bash
echo -e '{"a":1}\n{"a":2}' | mustmatch like '{"a":1}'
```

## Open Questions

1. Should `like` have an alias (`contains`, `has`, `includes`)?
2. Should regex support flags like `/pattern/i` for case-insensitive?
3. How to handle JSONL-specific modes (set, key-based)?
4. Should `--ignore` work on strings too (line numbers)?
