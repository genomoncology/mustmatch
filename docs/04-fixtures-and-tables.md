# Fixtures And Tables

Markdown tables are first-class fixture data for executable documentation. In the Rust documentation runner, `bash each_row` turns rows into scenario data: bare `{{column}}` placeholders come from the current row, while dotted `{{run-id.field}}` placeholders still come from named-run JSON output.

## Bash Table Scenarios

A bash block with `each_row=<table>` runs once per row of the named table. Numeric columns are coerced before substitution, while `str:` headers are exposed without the prefix and keep their raw string value.

````markdown
## Double Values

| input | output | str:label |
|-------|--------|-----------|
| 2     | 4      | double-two |
| 3     | 6      | double-three |

```bash each_row="Double Values"
expr {{input}} '*' 2 | mustmatch like '{{output}}'
```
````

The `str:label` column is optional. When it is present, verbose output uses it as the row label; otherwise rows are reported as `row-1`, `row-2`, and so on.

## Scenario Outlines

A named `bash run id=<id> each_row=<table>` block and a matching `expect=<id> each_row=<table>` block form a scenario outline. The command and expected output are templated from the same row and compared in lockstep.

````markdown
## Status Lines

| name  | status       | expected     | str:label |
|-------|--------------|--------------|-----------|
| alpha | status=ready | alpha ready  | alpha-case |
| beta  | status=done  | beta done    | beta-case |

```bash run id=status-line each_row="Status Lines"
printf '{{name}} {{status}}\n'
```

```text expect=status-line each_row="Status Lines" contains
{{expected}}
```
````

Both fences name the same table so the runner can execute and compare each row independently.

## Selecting A Table

When multiple tables are in scope, `table=<name>` selects the intended rows. A non-empty `each_row=<name>` also selects a table; if both `each_row=<name>` and `table=<name>` are present, they must refer to the same table.

````markdown
## Selected Rows

| value | str:code | expected |
|-------|----------|----------|
| 007   | 007      | numeric=7 raw=007 |

```bash each_row table="Selected Rows"
printf 'numeric={{value}} raw={{code}}\n' | mustmatch like '{{expected}}'
```
````

Here `value` renders as the coerced number `7`, while `code` renders as the raw string `007` because its header is `str:code`.

## Document Fixture

The Python pytest plugin still exposes `md`, `scenarios`, and typed `TableRow` values for legacy Python documentation tests. New table-driven documentation should prefer the bash forms above so it also works with `mustmatch-cli test`.
