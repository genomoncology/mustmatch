# Normalization

Before comparing, `mustmatch` normalizes **both** the actual output and the
expected value so that rendering noise never breaks an assertion. Three
transforms are applied, all on by default:

- **strip ANSI** colour/escape sequences;
- **normalize newlines** — `\r\n` and lone `\r` become `\n`;
- **trim** leading and trailing whitespace.

## ANSI colour is stripped

A coloured `FAILED` banner asserts cleanly against the plain word.

```bash
printf '\033[31mFAILED\033[0m\n' | mustmatch "FAILED"
```

## Surrounding whitespace is trimmed

Leading/trailing spaces and blank lines around the output are trimmed, so a doc
need not reproduce them.

```bash
printf '   spaced out   \n\n' | mustmatch "spaced out"
```

## Carriage returns fold to newlines

Windows `\r\n` line endings compare equal to plain `\n`.

```bash
printf 'line1\r\nline2\r\n' | mustmatch "line1
line2"
```

A lone `\r` (an in-place progress update) also folds to a newline.

```bash
printf 'progress\rdone\n' | mustmatch "progress
done"
```
