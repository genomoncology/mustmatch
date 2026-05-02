# Good Executable Documentation

Executable documentation should read like product documentation and behave like a
contract test. The goal is not to expose the test harness; the goal is to make a
reader trust that the documented workflow is real.

## 1. Documentation First, Test Second

A reader should learn the product without noticing the harness. Introduce the
user goal, then show the command and the important output.

## 2. Show The Real User Command

Prefer the command a user would type:

````markdown
```bash run id=detail uses=match
mytool annotation get {{match.annotation_id}} identity
```
````

Avoid visible extraction plumbing such as `jq`, Python one-liners, shell loops,
temporary files, or environment-variable handoffs unless that plumbing is the
feature being documented.

## 3. Hide Setup, But Name It Clearly

Use contexts or fixtures for auth, temp homes, PATH changes, server setup, and
other harness work. The document should name the context's purpose, not explain
its mechanics in every example.

````markdown
```bash run id=server-status context=demo-server
mytool server status --json
```
````

## 4. Assert Meaningful Fragments

Prefer contextual multiline output over one-word checks. One-word assertions pass
too easily and rarely explain behavior.

````markdown
```markdown expect=resource-card contains
# Resource: widget-123

| Field | Value |
|---|---|
| Status | active |
```
````

## 5. Separate Positive And Safety Assertions

Keep expected behavior blocks distinct from leak checks. Positive assertions tell
the reader what should happen; safety assertions protect boundaries.

````markdown
```text expect=resource-card not-contains
token_value
raw_payload
/api/internal
```
````

## 6. Test Contracts, Not Formatting Trivia

Use exact output only when exactness matters. Otherwise prefer JSON subset checks
or contextual Markdown/text contains checks. This keeps docs stable when harmless
formatting changes happen.

## 7. Keep Framework Docs Generic

Framework documentation should use generic examples such as `mytool`,
`resource_id`, `detail`, and `status`. Domain projects should use their real
language and data. For example, Must Match docs stay generic; GoToolkit docs can
use GoMC, BRAF, and annotation workflows.

## 8. Make Live Dependencies Explicit

Default documentation tests should be deterministic. Live examples should either
fail clearly when required credentials are missing or be explicitly opt-in.

## 9. One Behavior Per Section

Each heading should map to one concept the user can understand and one behavior
the runner verifies. If a section needs several unrelated assertions, split it.

## 10. Prefer Progressive Disclosure

Start with the common path. Add contexts, substitution, streams, setup, and
failure modes only after the reader understands the core loop.
