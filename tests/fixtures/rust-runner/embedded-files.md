# Rust Runner Embedded Files

Embedded file blocks let documentation show input files directly. The runner materializes those files beside the command that consumes them, so examples can use ordinary relative paths instead of heredocs.

## Embedded JSON files become local inputs

A named `json file=...` block is written before the bash block runs. The command can read the file by its relative path.

```json file=config.json
{"name":"Example Widget","status":"active"}
```

```bash
cat config.json | mustmatch like '"status":"active"'
```

## Section fixture files are shared by later commands

Files belong to the current section. Later commands in the same section can reuse the same fixture without recreating it.

```text file=state/status.txt
ready
```

```bash
cat state/status.txt | mustmatch like 'ready'
```

```bash
grep -n ready state/status.txt | mustmatch like '1:ready'
```

## New sections get fresh fixture directories

A new section starts from a clean working directory. Files from earlier sections are not visible unless this section declares them again.

```bash
find . -path './state/status.txt' -print | mustmatch not like 'state/status.txt'
```

## Row fixtures render table values

Fixture content can use the same row placeholders as bash scenario blocks. Each row receives its own rendered copy before the command reads the file.

| str:name | status | expected | str:label |
|----------|--------|----------|-----------|
| alpha    | ready  | alpha=ready | row-alpha |
| beta     | done   | beta=done   | row-beta |

```text file=row.txt each_row="Row fixtures render table values"
{{name}}={{status}}
```

```bash each_row="Row fixtures render table values"
cat row.txt | mustmatch like '{{expected}}'
```
