# Ellipsis (`...`)

When you assert multi-line output with `like`, an ellipsis lets a short doc match
long or volatile output without copying every line. There are two forms:

- a line that is just `...` — a **gap** that skips any number of lines;
- a line ending in `...` — a **prefix anchor** that matches the start of a line
  and ignores the rest.

Ellipsis matching is **ordered** (anchors must appear in sequence), the first
anchor may appear anywhere (an implicit leading gap), and internal whitespace is
collapsed so a clean doc line matches padded table output.

## A `...` gap skips lines

```bash
seq 1 5 | mustmatch like "1
...
5"
```

## A trailing `...` anchors a prefix

The anchor matches the beginning of the line; the volatile tail (a full hash, a
timestamp) is ignored.

```bash
printf 'commit a1b2c3d4e5f6 by Ian on 2026-06-04\n' \
  | mustmatch like "commit a1b2c3d4 ..."
```

## Whitespace is collapsed (padded tables match)

A leading `...` skips a banner line, then the clean doc rows match the padded
output because column padding is collapsed before comparison.

```bash
printf -- '-[ RECORD 1 ]------------\nname        | BRAF\nkind        | kinase\n' \
  | mustmatch like "...
name | BRAF
kind | kinase"
```

## Adjacency needs a gap

Between two anchors with no `...`, the lines must be **adjacent**. When a line
sits between them the match fails and the message tells you to insert `...`.
Here we capture that failure instead of letting it fail the block.

```bash
out=$(printf 'row a\nrow b\nrow c\n' | mustmatch like "...
row a
row c" 2>&1) && code=0 || code=$?
printf 'code=%s\n' "$code" | mustmatch like "code=1"
printf '%s\n'      "$out"  | mustmatch like "Insert"
```
