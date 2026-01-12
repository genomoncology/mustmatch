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

```console
pytest docs/                  # Run all markdown tests
pytest docs/cli.md            # Run specific file
pytest docs/cli.md --collect-only   # See discovered tests
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

## Output

Results appear in standard pytest format:

```bash
pytest docs/cli.md 2>&1 | outmatch --contains "passed"
```

## Skipping Blocks

Use HTML comments to skip blocks that shouldn't run:

```markdown
<!-- outmatch: skip -->
` ` `bash
# This block won't run
` ` `
```

## Failure Output

When a block fails, pytest shows the file, line, command, and exit code:

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

## pytest vs outmatch test

| Feature           | pytest plugin        | outmatch test        |
|-------------------|----------------------|----------------------|
| Integration       | Works with pytest    | Standalone           |
| Parallelism       | Via pytest-xdist     | Built-in `--parallel`|
| Reports           | pytest reporters     | JUnit, JSON, TAP     |
| Block directives  | skip                 | skip, timeout, env   |

Use pytest when integrating with existing test suites.
Use `outmatch test` for standalone doc testing or advanced features.
