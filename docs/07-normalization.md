# Normalization

mustmatch normalizes both actual and expected values before comparing. This removes noisy formatting differences and keeps assertions focused on meaning. Normalization covers ANSI escapes, newline variants, and outer whitespace.

## ANSI And Newlines

Terminal color and CRLF differences are stripped automatically. Assertions can stay stable across local shells and CI logs.

```bash
printf '\033[31mhello\033[0m\n' | mustmatch "hello"
printf "hello\r\n" | mustmatch "hello"
printf "line1\r\nline2\r\n" | mustmatch like "line2"
```

## Trimming And Case

Leading and trailing whitespace are trimmed by default. Case-insensitive checks are opt-in with `-i`.

```bash
printf "  hello  \n" | mustmatch "hello"
printf "  HELLO  \n" | mustmatch -i "hello"
printf "VALUE\n" | mustmatch -i like "val"
```
