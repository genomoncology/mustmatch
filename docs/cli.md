# CLI Reference

Complete reference for mustmatch command-line options.

## Version

```bash
mustmatch --version
```

## Basic Grammar

```
mustmatch [-i] [not] [like] EXPECTED
```

| Modifier | Meaning |
|----------|---------|
| `like` | Partial/contains match |
| `not` | Negate the assertion |
| `-i` | Case-insensitive |

## Auto-Detection

The type of comparison is automatically detected from the expected value:

| Pattern | Detected Type |
|---------|---------------|
| `/pattern/` | Regex |
| `{...}` | JSON object |
| `[...]` | JSON array |
| other | String |

```bash
# String match (default)
echo "hello" | mustmatch "hello"

# Regex match (auto-detected from /.../)
echo "v1.2.3" | mustmatch "/v\d+\.\d+/"

# JSON match (auto-detected from {...})
echo '{"a":1}' | mustmatch '{"a":1}'
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Match - output matched expected value |
| 1 | Mismatch - output differs from expected |
| 2 | Error - invalid arguments |

```bash
# Exit 0 on match
echo "hello" | mustmatch "hello"

# Exit 1 on mismatch
echo "hello" | mustmatch "world" || test $? -eq 1

# Exit 2 on error (missing expected value)
echo "test" | mustmatch 2>&1 || test $? -eq 2
```

## Like (Contains) Matching

Use `like` for substring/contains matching:

```bash
# Substring match
echo "hello world" | mustmatch like "hello"

# Works with JSON for subset matching
echo '{"a":1,"b":2}' | mustmatch like '{"a":1}'
```

## Negation

Use `not` to assert something is NOT present:

```bash
# Assert string is absent
echo "hello world" | mustmatch not "error"

# Assert substring is absent
echo "hello world" | mustmatch not like "error"

# Assert regex doesn't match
echo "success: ok" | mustmatch not "/[Ee]rror/"
```

## Case-Insensitive Matching

Use `-i` for case-insensitive comparison:

```bash
echo "Hello World" | mustmatch -i "hello world"
echo "Hello World" | mustmatch -i like "HELLO"
```

## Quiet Mode

Suppress all output, use exit code only:

```bash
# -q / --quiet suppresses output
if echo "hello" | mustmatch -q "hello"; then
    echo "matched"
fi
```

## Color Control

Control ANSI color output with `--color`:

| Value | Behavior |
|-------|----------|
| `auto` | Color if stderr is a TTY |
| `always` | Always use color |
| `never` | Never use color |

```bash
# Force no color
echo "hello" | mustmatch --color never "world" 2>&1 || true
```

## File-Based Expected Values

Read expected value from a file with `-f` / `--file`:

```bash
# Create expected file
echo "test content" > /tmp/expected.txt
echo "test content" | mustmatch -f /tmp/expected.txt
rm /tmp/expected.txt
```

## JSON Matching

JSON values are auto-detected from `{...}` or `[...]`:

```bash
# Exact JSON match (field order doesn't matter)
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# JSON subset match with "like"
echo '{"a":1,"b":2,"c":3}' | mustmatch like '{"a":1}'

# Ignore specific fields with --ignore
echo '{"id":"abc","ts":123,"data":"x"}' | mustmatch --ignore '$.ts' '{"id":"abc","data":"x"}'
```

## Subcommands

### Test Command

Run code blocks in markdown files:

```console
$ mustmatch test docs/
$ mustmatch test -v README.md
$ mustmatch test --lang python --memory docs/tutorial.md
```

### Exec Command

Execute a command and assert on its output:

```bash
# Assert exit code
mustmatch exec --exit-code 0 -- echo "hello"

# Assert stdout
mustmatch exec --stdout "hello" -- echo -n "hello"

# Assert stdout contains text
mustmatch exec --stdout-like "hello" -- echo "hello world"
```

## Full Options List

```
mustmatch [OPTIONS] [not] [like] EXPECTED

Modifiers:
  not                    Negate the match (must NOT match)
  like                   Partial match (contains/subset)

Options:
  -i, --ignore-case      Case-insensitive comparison
  -q, --quiet            Suppress all output
  -f, --file FILE        Read expected value from file
  --ignore PATH          Ignore JSON path (repeatable)
  --color MODE           auto | always | never
  --version              Show version and exit
  -h, --help             Show help and exit

Subcommands:
  mustmatch test         Run markdown documentation tests
  mustmatch exec         Execute command and assert on output
```
