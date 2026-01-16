# Text Normalization

mustmatch automatically normalizes text before comparison.

## ANSI Color Codes

ANSI escape sequences are always stripped:

```bash
# Color codes stripped automatically
echo -e "\033[31mhello\033[0m" | mustmatch "hello"
echo -e "\033[1;32mworld\033[0m" | mustmatch "world"
```

## Whitespace Trimming

Leading and trailing whitespace is always trimmed:

```bash
# Leading spaces
echo "  hello" | mustmatch "hello"

# Trailing spaces
echo "hello  " | mustmatch "hello"

# Both
echo "  hello  " | mustmatch "hello"

# Tabs
echo -e "\thello\t" | mustmatch "hello"
```

## Newline Normalization

CRLF is normalized to LF:

```bash
# CRLF converted to LF
printf "hello\r\n" | mustmatch "hello"

# Multiple lines with CRLF normalized
printf "line1\r\nline2\r\n" | mustmatch like "line1"
```

## Case Insensitive

Use `-i` flag for case-insensitive matching:

```bash
echo "HELLO" | mustmatch -i "hello"
echo "HeLLo WoRLd" | mustmatch -i "hello world"
```

## Combining Normalizations

All normalizations work together:

```bash
# ANSI + whitespace + CRLF
echo -e "  \033[31mhello\033[0m  \r\n" | mustmatch "hello"

# ANSI + case insensitive
echo -e "\033[32mHELLO\033[0m" | mustmatch -i "hello"
```
