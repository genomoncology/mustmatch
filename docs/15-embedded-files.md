# Embedded Fixture Files

Embedded file blocks let a Markdown document show input files as first-class documentation. In the Rust documentation runner, a fenced block with `file=<relative/path>` is written into the working directory before later blocks in the same section run. The file block is setup only: it is not executed, asserted, or reported as a PASS line.

## Replace Heredoc Setup With Documented Files

Before embedded files, examples often hid input data inside shell plumbing:

````markdown
```bash
cat > config.json <<'EOF'
{"status":"active"}
EOF
cat config.json | mustmatch like '"status":"active"'
```
````

With `file=`, the document shows the input file separately and the command reads it by relative path:

````markdown
```json file=config.json
{"status":"active"}
```

```bash
cat config.json | mustmatch like '"status":"active"'
```
````

## Section Lifetime

Fixture files belong to the current behavior section. Later commands in the same section can read the same rendered files, and a new H2 section starts with a fresh working directory.

## Row Substitution

A file block can use `each_row=<table>` with the same table selection rules as bash scenario blocks. Bare `{{column}}` placeholders render from the current row, while dotted `{{run-id.field}}` placeholders keep using named-run JSON output.

````markdown
| str:name | status | expected |
|----------|--------|----------|
| alpha    | ready  | alpha=ready |

```text file=row.txt each_row="Row Substitution"
{{name}}={{status}}
```

```bash each_row="Row Substitution"
cat row.txt | mustmatch like '{{expected}}'
```
````

## Context CWD Behavior

When a consuming block uses `context=<name>`, the context is resolved first. Fixture files are then written into the resolved context cwd, so a context with `cwd = "{tmp}"` reads the same relative paths as a no-context example.

## Path Safety And Conflicts

`file=` paths must be relative and stay under the fixture cwd. Absolute paths, Windows drive or UNC prefixes, and `..` path traversal are rejected. A `file=` block is materialization-only setup, so it cannot also carry `run`, `mustmatch-run`, `expect`, `for`, `output`, or `mustmatch-output`.
