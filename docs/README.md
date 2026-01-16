# mustmatch Documentation

Complete documentation for testing CLI output and documentation.

## Quick Links

- **[Getting Started](getting-started.md)** — 10-minute intro
- **[Complete Guide](guide.md)** — Comprehensive tutorial
- **[CLI Reference](reference/cli-reference.md)** — All commands and options

## Documentation Structure

### Getting Started

Start here if you're new to mustmatch:

- [Getting Started](getting-started.md) — Quick 10-minute tutorial
- [Complete Guide](guide.md) — In-depth walkthrough

### Use Cases

Real-world examples and patterns:

- [Document-Driven Development](use-cases/document-driven-development.md) — DDD paradigm explained
- [DevOps Verification](use-cases/devops-verification.md) — Self-verifying scripts
- [CI Integration](use-cases/ci-integration.md) — GitHub Actions, GitLab CI, etc.

### Reference

Technical documentation:

- [CLI Reference](reference/cli-reference.md) — Complete command reference

### Philosophy

Conceptual guides:

- [Why Test Documentation?](philosophy/why-test-documentation.md) — The case for tested docs

### Recipes

How-to guides and patterns:

- [JSON Testing](recipes/json-testing.md) — Practical JSON patterns

## Key Concepts

### Document-Driven Development (DDD)

mustmatch enables a new development paradigm where:
- **Documentation comes first** — write docs with examples
- **Examples are tests** — every code block must work
- **Tests are docs** — users read actual integration tests
- **CI verifies everything** — broken examples = failed build

**Benefits:**
- Documentation always accurate
- Perfect onboarding experience
- API-first design thinking
- Integration tests for free

See [Document-Driven Development](use-cases/document-driven-development.md) for details.

### Core Features

**CLI Output Assertions:**
```bash
echo "hello" | mustmatch "hello"                # Exact match
echo "hello world" | mustmatch like "world"     # Contains
echo "ok" | mustmatch not like "error"          # Negation
echo '{"a":1}' | mustmatch '{"a":1}'           # JSON
date +%Y-%m-%d | mustmatch '/^\d{4}/'          # Regex
```

**Documentation Testing:**
````markdown
# Your docs become tests

```bash
command | mustmatch "expected output"
```
````

```bash
# Test your docs
mustmatch test docs/
```

## Quick Start

### 1. Install

```bash skip
pip install mustmatch
```

### 2. Verify Output

```bash
echo "hello" | mustmatch "hello"
ls -la | mustmatch like "README"
```

### 3. Test Documentation

````bash
cat > example.md << 'EOF'
# Example

```bash
echo "test" | mustmatch "test"
```
EOF

mustmatch test example.md
````

### 4. Add to CI

```yaml
# .github/workflows/docs.yml
- run: pip install mustmatch
- run: mustmatch test docs/
```

## Learning Path

### Beginner

1. [Getting Started](getting-started.md) — Learn basics
2. Try examples on your own files
3. Create your first tested doc

### Intermediate

1. [Complete Guide](guide.md) — Master all features
2. [CI Integration](use-cases/ci-integration.md) — Add to CI/CD
3. [JSON Testing](recipes/json-testing.md) — API patterns

### Advanced

1. [Document-Driven Development](use-cases/document-driven-development.md) — Adopt DDD workflow
2. [DevOps Verification](use-cases/devops-verification.md) — Self-verifying scripts
3. [Why Test Documentation?](philosophy/why-test-documentation.md) — Deep philosophy

## Common Questions

### What is mustmatch?

A CLI tool that:
1. Asserts command output matches expected values
2. Tests code blocks in markdown documentation
3. Enables Document-Driven Development

### Why test documentation?

- Examples break over time
- Users hit broken examples
- Trust in docs erodes
- Support burden increases

Testing docs prevents all of this.

### How is this different from pytest?

pytest is for unit tests. mustmatch is for:
- CLI output verification
- Documentation testing
- Integration tests via docs
- DevOps script verification

They complement each other. Use both.

### What is Document-Driven Development?

Like Test-Driven Development, but:
- Write documentation first (with examples)
- Examples ARE tests
- Implement until docs pass
- Ship with self-proving docs

See [Document-Driven Development](use-cases/document-driven-development.md).

## Examples

### CLI Tool Development

````markdown
# mytool Documentation

```bash skip
mytool --version | mustmatch like "mytool"
mytool process data.txt | mustmatch like "Success"
```
````

```bash skip
mustmatch test README.md  # Verifies examples work
```

### API Documentation

````markdown
# API Docs

```bash skip
curl https://api.example.com/users | \
    mustmatch like '{"users":[{"id"'
```
````

### DevOps Scripts

```bash skip
#!/bin/bash
# deploy.sh

kubectl apply -f service.yaml | mustmatch like "created"
curl http://myapp/health | mustmatch '{"status":"ok"}' || exit 1
echo "✓ Deploy successful"
```

### Infrastructure Verification

```bash skip
# health-check.sh
systemctl is-active myapp | mustmatch "active"
curl localhost:8080/health | mustmatch '{"status":"ok"}'
df -h / | mustmatch not like "100%"
```

## Next Steps

Choose your path:

**Want to get started quickly?**
→ [Getting Started](getting-started.md)

**Want comprehensive coverage?**
→ [Complete Guide](guide.md)

**Want real-world examples?**
→ [Use Cases](use-cases/)

**Want technical details?**
→ [CLI Reference](reference/cli-reference.md)

**Want to understand the philosophy?**
→ [Why Test Documentation?](philosophy/why-test-documentation.md)

## Contributing

Found an issue? Want to contribute?

- Repository: https://github.com/botassembly/mustmatch
- Issues: https://github.com/botassembly/mustmatch/issues

## License

MIT
