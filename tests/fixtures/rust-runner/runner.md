# Rust Runner Fixture

This fixture is intentionally generic. It gives the Rust documentation runner one small example of each block class that ticket 006 supports.

## Bash assertion blocks run

A bash block can pipe command output into the assertion binary.

```bash
printf 'Runner status: active\n' | mustmatch-cli like "Runner status: active"
```

## Console examples execute visible commands

A console block shows the command a reader types and the output the runner checks.

```console mustmatch
$ printf 'Console status: active\n'
Console status: active
```

## Named runs reuse JSON fields

Named runs let a later command reuse structured output without showing JSON plumbing in the document.

```bash run id=resource-json
printf '{"resource_id":"widget-123","status":"active"}\n'
```

```bash run id=resource-detail uses=resource-json
printf 'Resource {{resource-json.resource_id}} is {{resource-json.status}}\n'
```

```text expect=resource-detail contains
Resource widget-123 is active
```

## Contexts hide setup

A context prepares the working directory, PATH, and environment before the documented command runs.

```bash run id=context-demo context=demo
cat state.txt
helper-tool
env | grep '^DOC_VALUE='
```

```text expect=context-demo contains
state=ready
helper=ready
DOC_VALUE=example
```

## Unsupported Python blocks are visible

Python execution is intentionally not part of the Rust runner. During the transition, unsupported Python blocks are reported as skipped instead of silently disappearing.

```python
print("rust runner reports this block as unsupported")
```
