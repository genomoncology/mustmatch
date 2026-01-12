# Pytest Plugin

Run markdown tests as part of your pytest suite.

The outmatch pytest plugin automatically discovers and runs bash blocks
in markdown files alongside your regular tests.

## Setup

Install outmatch in your project - the plugin registers automatically:

<!-- outmatch: skip -->
```bash
pip install outmatch
```

Configure pytest to find your docs:

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests", "docs"]
```

## Running Tests

Point pytest at your markdown files:

<!-- outmatch: skip -->
```bash
# Run all markdown tests
pytest docs/

# Run specific file
pytest docs/cli.md

# See what tests are discovered
pytest docs/cli.md --collect-only
```

## Test Discovery

Every ` ```bash ` block becomes a test item:

```bash
pytest docs/cli.md --collect-only 2>&1 | \
    outmatch --contains "<MarkdownItem"
```

Test names come from the preceding markdown heading:

```bash
pytest docs/cli.md -v 2>&1 | outmatch --contains "Version"
```

## Output Format

Results appear in standard pytest format:

```bash
pytest docs/cli.md 2>&1 | outmatch --contains "passed"
```

File paths are reported alongside test names:

```bash
pytest docs/cli.md -v 2>&1 | outmatch --contains "cli.md"
```

## Mixing with Unit Tests

Markdown tests run alongside regular pytest tests:

```bash
pytest tests/ docs/cli.md 2>&1 | outmatch --contains "passed"
```

## Skipping Blocks

Use HTML comments to skip blocks that shouldn't run in pytest:

```markdown
<!-- outmatch: skip -->
` ` `bash
# This block won't run
` ` `
```

## Failure Output

When a block fails, pytest shows:
- File path and line number
- Block name (from heading)
- The command that failed
- stdout/stderr output
- Exit code

```bash
cat << 'EOF' > /tmp/pytest-fail.md
## Failing Test
` ` `bash
exit 1
` ` `
EOF
sed -i 's/` ` `/```/g' /tmp/pytest-fail.md
pytest /tmp/pytest-fail.md 2>&1 | outmatch --contains "Exit code: 1"
```

## Comparison with outmatch test

| Feature           | pytest plugin          | outmatch test        |
|-------------------|------------------------|----------------------|
| Integration       | Works with pytest      | Standalone           |
| Parallelism       | Via pytest-xdist       | Built-in `--parallel`|
| Reports           | pytest reporters       | JUnit, JSON, TAP     |
| Configuration     | pyproject.toml/pytest.ini | CLI flags         |
| Block directives  | skip only              | skip, timeout, env   |

Use the pytest plugin when you want markdown tests integrated into
your existing pytest workflow. Use `outmatch test` for standalone
documentation testing or when you need advanced features like
per-block timeouts.
