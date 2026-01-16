# Examples

Real-world examples using actual commands.

## File Operations

```bash
# List current directory
ls -a | mustmatch like "."

# Echo to file and read back
echo "test content" > /tmp/test-mustmatch.txt
cat /tmp/test-mustmatch.txt | mustmatch "test content"
rm /tmp/test-mustmatch.txt
```

## Text Processing

```bash
# grep output
printf "line 1\nline 2\nerror in line 3\n" | grep error | mustmatch like "error"

# sed output
echo "hello" | sed 's/hello/goodbye/' | mustmatch "goodbye"

# awk output
echo "field1 field2" | awk '{print $2}' | mustmatch "field2"

# cut output
echo "a,b,c" | cut -d, -f2 | mustmatch "b"
```

## Date and Time

```bash
# Date format
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'

# Year
date +%Y | mustmatch '/^\d{4}$/'

# Check date components
date +%m | mustmatch '/^(0[1-9]|1[0-2])$/'
```

## JSON

```bash
# Simple JSON
echo '{"status":"ok"}' | mustmatch '{"status":"ok"}'

# Field order independent
echo '{"b":2,"a":1}' | mustmatch '{"a":1,"b":2}'

# Nested JSON
echo '{"data":{"count":5}}' | mustmatch '{"data":{"count":5}}'

# Subset matching
echo '{"status":"ok","count":42,"extra":"data"}' | \
    mustmatch like '{"status":"ok"}'

# JSON array
echo '[1,2,3]' | mustmatch '[1,2,3]'
```

## Environment and Variables

```bash
# Check environment variable
echo "$HOME" | mustmatch '/.+/'

# PWD
echo $PWD | mustmatch like "mustmatch"
```

## Exit Codes

```bash
# True command
true && echo "success" | mustmatch "success"

# Chaining
echo "step1" | mustmatch "step1" && echo "step2" | mustmatch "step2"
```

## Help and Version Checking

```bash
# Check help exists
mustmatch --help | mustmatch like "Usage:"

# Verify version format
mustmatch --version | mustmatch like "mustmatch"

# Check specific help section
mustmatch --help | mustmatch like "Options:"
```

## Case Insensitive

```bash
echo "Hello" | mustmatch -i "hello"
echo "WORLD" | mustmatch -i like "world"
```

## Negation

```bash
# Not equal
echo "ok" | mustmatch not "error"

# Doesn't contain
echo "operation successful" | mustmatch not like "error"
echo "operation successful" | mustmatch not like "fail"
```

## Head and Tail

```bash
# First line
printf "line1\nline2\nline3\n" | head -1 | mustmatch "line1"

# Last line
printf "line1\nline2\nline3\n" | tail -1 | mustmatch "line3"

# First N lines
ls -la | head -5 | mustmatch like "total"
```

## Word Count

```bash
# Count words
echo "one two three" | wc -w | mustmatch like "3"

# Count characters
echo "hello" | wc -c | mustmatch like "6"
```

## Sorting

```bash
# Sort output
printf "c\nb\na" | sort | head -1 | mustmatch "a"

# Unique lines
printf "a\na\nb" | sort -u | wc -l | mustmatch like "2"
```
