# Quick Start

## Basic Usage

Pipe command output to mustmatch:

```bash
echo "hello" | mustmatch "hello"
```

Exit code is 0 on match, 1 on mismatch.

## Substring Matching

Use `like` to check if output contains text:

```bash
echo "hello world" | mustmatch like "hello"
echo "hello world" | mustmatch like "world"
date | mustmatch like "2026"
```

## Negation

Use `not` to assert absence:

```bash
echo "success" | mustmatch not "error"
echo "success" | mustmatch not like "error"
```

## Regex

Wrap patterns in slashes:

```bash
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
echo "version 1.2.3" | mustmatch '/version \d+\.\d+\.\d+/'
```

## JSON

JSON is compared semantically:

```bash
# Field order doesn't matter
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Subset matching
echo '{"status":"ok","count":42}' | mustmatch like '{"status":"ok"}'
```

## Combining Flags

```bash
echo "HELLO" | mustmatch -i "hello"
echo "HELLO WORLD" | mustmatch -i like "world"
```

## Exit Codes

Exit codes: 0 = success, 1 = failure, 2 = invalid arguments.

```bash
# Success returns 0
echo "ok" | mustmatch "ok"

# Chain commands with &&
echo "ok" | mustmatch "ok" && echo "success" | mustmatch "success"
```

## Using in Scripts

```bash
if echo "ready" | mustmatch "ready"; then
    echo "Status confirmed"
fi
```

## Text Normalization

mustmatch automatically cleans output:

```bash
# ANSI codes stripped
ls --color=always | mustmatch like "README"

# Whitespace trimmed
echo "  hello  " | mustmatch "hello"

# Newlines normalized (CRLF → LF)
printf "hello\r\n" | mustmatch "hello"
```

## Checking Help and Version

```bash
mustmatch --help | mustmatch like "Usage:"
mustmatch --version | mustmatch like "mustmatch"
```
