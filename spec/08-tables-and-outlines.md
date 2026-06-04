# Tables and scenario outlines

A Markdown table next to a block turns one example into many: tag the block with
`each_row` and it runs once per row. Bare `{{column}}` placeholders come from the
current row; dotted `{{run-id.field}}` placeholders still come from named-run JSON
(see `07-named-runs.md`). A `str:label` column gives each row a readable name in
the output.

## One block, one row each with `each_row`

| input | expected | str:label    |
|-------|----------|--------------|
| 2     | 4        | double-two   |
| 3     | 6        | double-three |

```bash each_row
expr {{input}} '*' 2 | mustmatch like '{{expected}}'
```

## Coercion and `str:` columns

Numeric cells are coerced before substitution (so `007` becomes `7`), while a
`str:` column keeps its text exactly. Here the same cell is read both ways.

| value | str:code | expected          | str:label |
|-------|----------|-------------------|-----------|
| 007   | 007      | numeric=7 raw=007 | seven     |
| 010   | 010      | numeric=10 raw=010| ten       |

```bash each_row
printf 'numeric=%s raw=%s\n' {{value}} {{code}} | mustmatch like '{{expected}}'
```

## Choosing among tables with `table=`

When more than one table is in scope, name the one a block should use with
`table=`. The block below sits under **Sizes** but drives the **Palette** rows.

### Palette

| color   | str:label   |
|---------|-------------|
| crimson | crimson-row |

### Sizes

| size  | str:label |
|-------|-----------|
| large | large-row |

```bash each_row table="Palette"
printf '%s\n' {{color}} | mustmatch like '{{color}}'
```

## Scenario outlines (one table drives command and expectation)

A named run and its expectation can share a table: input columns substitute into
the command, output columns into the expectation, row by row.

### Adder cases

| left | right | sum   | str:label     |
|------|-------|-------|---------------|
| 1    | 2     | 1 + 2 | one-plus-two  |
| 4    | 5     | 4 + 5 | four-plus-five|

```bash run id=adder each_row
printf '{{left}} + {{right}}\n'
```

```text expect=adder each_row contains
{{sum}}
```
