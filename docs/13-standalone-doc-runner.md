# Standalone Documentation Runner

`mustmatch test` runs documentation examples without pytest. It understands the
same documentation-first shape as the pytest plugin: a command block can be named
once, expected output can live in separate blocks, and later commands can reuse
JSON fields from earlier runs without visible shell plumbing.

## Console Examples Show Command And Output Together

Use `console mustmatch` when documentation should show exactly what a user types
and the output they should expect. Lines beginning with `$ ` are executed; the
following lines are matched against stdout.

```console mustmatch
$ printf '# Example Widget\n\nStatus: active\nOwner: platform-team\n'
# Example Widget

Status: active
```

## Named Runs Work Outside Pytest

A run block captures stdout. A separate JSON block checks the important shape of
that output.

```bash run id=resource-json
printf '{"resource_id":"widget-123","name":"Example Widget","status":"active"}\n'
```

```json expect=resource-json contains
{
  "name": "Example Widget",
  "status": "active"
}
```

## Follow-Up Commands Can Reuse JSON Fields

Use `{{run-id.field}}` inside a later `bash run` block to substitute a JSON value
from a previous run. The Markdown shows the product workflow instead of showing
`jq`, Python one-liners, or temporary files.

```bash run id=resource-detail uses=resource-json
printf 'Resource {{resource-json.resource_id}}: Example Widget\n'
```

```text expect=resource-detail contains
Resource widget-123: Example Widget
```

## Project Contexts Hide Setup

Projects can define named contexts in `pyproject.toml` to keep setup, temporary
state, environment files, required environment variables, and PATH additions out
of the user-facing example. The Markdown names the context, but the command stays
focused on the behavior being documented.

````toml
[tool.mustmatch.contexts.demo]
cwd = "{tmp}"
path = ["{root}/target/debug"]
required_env = ["DEMO_TOKEN"]
setup = ["mytool server add demo --url $DEMO_URL"]
````

````markdown
```bash run id=demo-status context=demo
mytool status --json
```
````

## Leak Checks Stay Separate

```text expect=resource-detail not-contains
/api/internal
raw_payload
password
secret_token
```
