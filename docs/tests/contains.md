# Contains Matching

Check if output includes a substring with `--contains`.

Use contains matching when you care about specific content but not the surrounding text. Help messages, log output, error messages - anything with boilerplate or variable content you want to ignore.

## When should I use contains instead of exact matching?

When the output includes information you don't control or don't care about:

```bash
echo "hello world" | outmatch --contains "world"
```

The output has "hello" too, but you only wanted to verify "world" is present.

## Where in the output does it look?

Anywhere. Beginning, middle, or end:

```bash
echo "hello world" | outmatch --contains "hello"
```

```bash
echo "the quick brown fox" | outmatch --contains "quick brown"
```

## Does it work across multiple lines?

Yes. The substring can appear on any line:

```bash
printf "line one\nline two\nline three" | outmatch --contains "line two"
```

## Is matching case-sensitive?

Yes, by default:

```bash
echo "Hello World" | outmatch --contains "hello" || test $? -eq 1
```

Add `--ignore-case` or `-i` for case-insensitive matching:

```bash
echo "Hello World" | outmatch --contains --ignore-case "hello"
```

## What about whitespace in the expected value?

Leading and trailing whitespace is stripped from the expected value:

```bash
echo "hello world" | outmatch --contains "  world  "
```

This makes tests more readable and less fragile.

## What happens when the substring isn't found?

Exit code 1:

```bash
echo "hello world" | outmatch --contains "goodbye" || test $? -eq 1
```

Empty output with non-empty expected also fails:

```bash
printf "" | outmatch --contains "something" || test $? -eq 1
```
