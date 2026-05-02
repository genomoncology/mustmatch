# Named Runs And Output Blocks

Named run blocks let executable examples read like documentation: the command is
shown once, and the expected output is shown in separate contextual blocks. This
keeps Markdown examples readable while still making the examples executable in
both `mustmatch test` and the pytest plugin.

## Command and JSON Output Are Decoupled

A `bash run` block captures stdout for an example command. A later `json
expect=<id> contains` block checks that stdout contains the expected JSON
structure without requiring the documentation to pipe through shell variables.

```bash run id=version-json
printf '{"name":"genomoncology","version":"0.1.0","extra":{"ignored":true}}\n'
```

```json expect=version-json contains
{
  "name": "genomoncology",
  "version": "0.1.0"
}
```

## Multiline Text Fragments Stay Contextual

Markdown and text output expectations compare multiline fragments so examples
show useful context instead of brittle one-word checks.

```bash run id=trial-card
cat <<'EOF'
# Trial: NCT04267848

| Field | Value |
|---|---|
| Title | BRAF V600E Lung Cancer Basket Study |
| Status | RECRUITING |
| Phase | Phase 2 |

## Eligibility

Adults with BRAF V600E NSCLC
EOF
```

```markdown expect=trial-card contains
| Field | Value |
|---|---|
| Title | BRAF V600E Lung Cancer Basket Study |
| Status | RECRUITING |
| Phase | Phase 2 |

## Eligibility

Adults with BRAF V600E NSCLC
```

## Follow-Up Commands Reuse JSON Fields

Later run blocks can refer to JSON fields captured by earlier runs with
`{{run-id.path.to.field}}`. This keeps the document focused on the product
workflow instead of showing `jq`, Python one-liners, temporary files, or shell
variables.

```bash run id=annotation-summary
printf '{"annotation_id":"ann_braf_v600e","alteration":"BRAF V600E"}\n'
```

```bash run id=annotation-identity uses=annotation-summary
printf 'Identity: {{annotation-summary.annotation_id}} {{annotation-summary.alteration}}\n'
```

```text expect=annotation-identity contains
Identity: ann_braf_v600e BRAF V600E
```

## Leak Checks Stay Separate

Absence assertions can list one forbidden string per line.

```text expect=trial-card not-contains
/api/
token_value
raw_payload
COSMIC
```
