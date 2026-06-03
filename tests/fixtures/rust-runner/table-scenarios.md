# Rust Runner Table Scenarios And Outlines

Bash table scenarios let fixture rows drive executable documentation without a Python block. Bare `{{column}}` placeholders come from the current table row, while dotted `{{run-id.field}}` placeholders still come from named run JSON output.

## Bash each_row substitutes table columns

A bash block with `each_row=<table>` runs once for every row in the named table. The `str:label` column gives each row a readable result label.

| input | expected | str:label |
|-------|----------|-----------|
| 2     | 4        | double-two |
| 3     | 6        | double-three |

```bash each_row="Bash each_row substitutes table columns"
expr {{input}} '*' 2 | mustmatch like '{{expected}}'
```

## Scenario outlines substitute inputs and outputs

A named run and its expectation can share the same table. Input columns substitute into the command, and expected-output columns substitute into the expectation for the same row.

| left  | right | equation    | status       | str:label |
|-------|-------|-------------|--------------|-----------|
| alpha | one   | alpha + one | status=ready | alpha-case |
| beta  | two   | beta + two  | status=done  | beta-case |

```bash run id=outline-row each_row="Scenario outlines substitute inputs and outputs"
printf '{{left}} + {{right}}\n{{status}}\n'
```

```text expect=outline-row each_row="Scenario outlines substitute inputs and outputs" contains
{{equation}}
{{status}}
```

## Selected Rows

Numeric columns use mustmatch coercion before substitution, while `str:` columns preserve raw text.

| value | str:code | expected |
|-------|----------|----------|
| 007   | 007      | numeric=7 raw=007 |
| 010   | 010      | numeric=10 raw=010 |

## Ignored Rows

This table is intentionally closer to the block than the selected table. The later example names the selected table so the runner does not accidentally use this one.

| value | str:code | expected |
|-------|----------|----------|
| 999   | BAD      | numeric=999 raw=BAD |

## Table selection and coercion use the named case table

When several tables are in scope, `table=<name>` selects the intended rows. Without a `str:label` column, row reporting falls back to `row-1`, `row-2`, and so on.

```bash each_row table="Selected Rows"
printf 'numeric={{value}} raw={{code}}\n' | mustmatch like '{{expected}}'
```
