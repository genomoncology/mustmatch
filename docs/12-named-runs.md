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
printf '{"name":"mytool","version":"1.2.3","extra":{"ignored":true}}\n'
```

```json expect=version-json contains
{
  "name": "mytool",
  "version": "1.2.3"
}
```

## Named Runs Can Capture Expected Errors

Expected failure examples should stay readable: the command remains a plain run
block, while the directives record the expected status and stream. A later
expectation block reads the selected stream without `set +e`, temporary files,
or stderr redirection in the document.

```bash run id=bad-usage exit=2 stream=stderr
mustmatch --bad-option
```

```text expect=bad-usage contains
Error: unknown option: --bad-option
```

## Multiline Text Fragments Stay Contextual

Markdown and text output expectations compare multiline fragments so examples
show useful context instead of brittle one-word checks.

```bash run id=resource-card
cat <<'EOF'
# Resource: widget-123

| Field | Value |
|---|---|
| Name | Example Widget |
| Status | active |
| Owner | platform-team |

## Notes

This resource is safe to show in documentation.
EOF
```

```markdown expect=resource-card contains
| Field | Value |
|---|---|
| Name | Example Widget |
| Status | active |
| Owner | platform-team |

## Notes

This resource is safe to show in documentation.
```

## Follow-Up Commands Reuse JSON Fields

Later run blocks can refer to JSON fields captured by earlier runs with
`{{run-id.path.to.field}}`. This keeps the document focused on the product
workflow instead of showing `jq`, Python one-liners, temporary files, or shell
variables.

```bash run id=resource-summary
printf '{"resource_id":"widget-123","label":"Example Widget"}\n'
```

```bash run id=resource-identity uses=resource-summary
printf 'Identity: {{resource-summary.resource_id}} {{resource-summary.label}}\n'
```

```text expect=resource-identity contains
Identity: widget-123 Example Widget
```

## Leak Checks Stay Separate

Absence assertions can list one forbidden string per line. Keep them separate
from the positive behavior assertion so the reader can tell which block explains
the feature and which block protects safety boundaries.

```text expect=resource-card not-contains
/api/internal
password
secret_token
raw_payload
```
