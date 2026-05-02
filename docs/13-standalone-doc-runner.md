# Standalone Documentation Runner

`mustmatch test` runs documentation examples without pytest. It understands the
same documentation-first shape as the pytest plugin: a command block can be named
once, expected output can live in separate blocks, and later commands can reuse
JSON fields from earlier runs without visible shell plumbing.

## Named Runs Work Outside Pytest

A run block captures stdout. A separate JSON block checks the important shape of
that output.

```bash run id=variant-json
printf '{"annotation_id":"ann_braf_v600e","gene":"BRAF","alteration":"BRAF V600E"}\n'
```

```json expect=variant-json contains
{
  "gene": "BRAF",
  "alteration": "BRAF V600E"
}
```

## Follow-Up Commands Can Reuse JSON Fields

Use `{{run-id.field}}` inside a later `bash run` block to substitute a JSON value
from a previous run. The Markdown shows the product workflow instead of showing
`jq`, Python one-liners, or temporary files.

```bash run id=annotation-card
printf 'Annotation {{variant-json.annotation_id}}: BRAF V600E\n'
```

```text expect=annotation-card contains
Annotation ann_braf_v600e: BRAF V600E
```

## Leak Checks Stay Separate

```text expect=annotation-card not-contains
/api/
raw_payload
token_value
COSMIC
```
