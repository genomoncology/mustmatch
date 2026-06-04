# Named runs

A named run decouples the command from the output that checks it. Tag a `bash`
block with `run id=<name>` to capture its result, then assert that result in a
later block with `expect=<name>`. This keeps the document readable — the command
is shown once, and one or more expectations refer back to it — and lets a later
command reuse a run's JSON output.

## Run once, expect later

```bash run id=version
printf 'tool 1.4.2\n'
```

```text expect=version contains
tool 1.4.2
```

## Reuse JSON fields with `{{id.field}}`

A `{{run-id.field}}` placeholder runs that named run, parses its stdout as JSON,
and substitutes the dotted field path. `uses=` declares the dependency so it
runs first.

```bash run id=meta
printf '{"name":"widget","version":"1.4.2"}\n'
```

```bash run id=greeting uses=meta
printf 'Using {{meta.name}} v{{meta.version}}\n'
```

```text expect=greeting contains
Using widget v1.4.2
```

## Expected exits and stderr

A run can document a non-zero exit with `exit=` and select `stream=stderr`; the
expectation reads the same stream as its run.

```bash run id=warn exit=3 stream=stderr
printf 'disk almost full\n' >&2
exit 3
```

```text expect=warn contains
disk almost full
```

## Caching and cycles

A named run executes at most once per document (per row, for table runs) and its
result is cached, so multiple expectations and `{{id.field}}` lookups share one
execution. A run that depends on itself through `uses=` is reported as a cyclic
dependency error rather than looping.
