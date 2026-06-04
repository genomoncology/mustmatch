# Embedded fixture files

A `file=<relative/path>` block writes its contents to disk before the commands
in the same section run, so a document can show an input file directly instead of
hiding it in a heredoc. Files are scoped to their section: blocks in the same
section share them, and a new section starts from a clean directory.

## A file becomes a local input

The `json file=config.json` block is materialized; the next command reads it by
its relative path.

```json file=config.json
{"name":"widget","status":"active"}
```

```bash
cat config.json | mustmatch like '"status":"active"'
```

## Shared within a section

Later commands in the same section reuse the same fixture without recreating it.

```text file=state.txt
ready
```

```bash
cat state.txt | mustmatch like "ready"
```

```bash
grep ready state.txt | mustmatch like "ready"
```

## A new section starts clean

A section that declares no files runs from the document's own directory, so the
private fixture directory from the previous section is not in scope — its
`state.txt` is not visible here.

```bash
find . -name state.txt -maxdepth 2 | mustmatch not like "state.txt"
```

## Per-row fixtures

A `file=` block can take `each_row`, rendering its content once per table row so
each row reads its own copy.

| str:name | status | str:label |
|----------|--------|-----------|
| alpha    | ready  | alpha     |
| beta     | done   | beta      |

```text file=row.txt each_row
{{name}}={{status}}
```

```bash each_row
cat row.txt | mustmatch like '{{name}}={{status}}'
```

## Path safety

A `file=` path must be **relative and stay under** the section directory.
Absolute paths and `..` segments are rejected before anything runs, so a
document can never write outside its fixture sandbox.
