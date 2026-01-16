# Command Line Interface

mustmatch has a CLI for asserting command output and testing documentation.

## Help Command

````bash
# mustmatch --help works the same way
mustmatch -h | mustmatch "mustmatch - Assert CLI output matches expected value.

Usage:
    command | mustmatch [not] [like] EXPECTED
    mustmatch test [OPTIONS] PATHS

Match stdin against expected:
    echo \"hello\" | mustmatch \"hello\"
    echo \"hello world\" | mustmatch like \"hello\"
    echo \"success\" | mustmatch not like \"error\"
    echo '{\"a\":1}' | mustmatch '{\"a\":1}'
    echo \"v1.2.3\" | mustmatch '/v\d+/'

Test markdown files:
    mustmatch test docs/
    mustmatch test -v README.md

Options:
    -i, --ignore-case    Case-insensitive comparison
    -q, --quiet          Suppress output
    --version            Show version

Test options:
    -v, --verbose        Show each test result
    -x, --fail-fast      Stop on first failure
    --timeout N          Timeout per block (default: 30)
    --lang LANG          Language: bash, python, all
    --memory             Share Python state between blocks"
````

## Matching

The primary use case is piping command output to mustmatch with an expected value.

### Exact Match

By default, mustmatch compares the entire output exactly:

```bash
echo "hello" | mustmatch "hello"
```

### Substring Match

Use `like` to check if the output contains a substring:

```bash
echo "hello world" | mustmatch like "hello"
```

### Negation

Use `not` to invert the match:

```bash
echo "success" | mustmatch not like "error"
```

You can combine `not` with exact matching too:

```bash
echo "hello" | mustmatch not "goodbye"
```

### Case Insensitive

Use `-i` for case-insensitive comparison:

```bash
echo "HELLO" | mustmatch -i "hello"
```

## Auto-Detection

mustmatch automatically detects the comparison mode from the expected value syntax.

### JSON

Values starting with `{` or `[` are compared as JSON. Field order doesn't matter:

```bash
echo '{"b": 2, "a": 1}' | mustmatch '{"a": 1, "b": 2}'
```

Use `like` for subset matching:

```bash
echo '{"a": 1, "b": 2, "c": 3}' | mustmatch like '{"a": 1}'
```

### Regex

Values wrapped in `/` are treated as regular expressions:

```bash
echo "version 1.2.3" | mustmatch '/version \d+\.\d+\.\d+/'
```

## Exit Codes

mustmatch uses exit codes to indicate results:

| Code | Meaning |
|------|---------|
| 0 | Match succeeded |
| 1 | Match failed |
| 2 | Invalid arguments |
