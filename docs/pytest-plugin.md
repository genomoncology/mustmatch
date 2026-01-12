# Pytest Plugin

Run markdown tests as part of your pytest suite.

The outmatch pytest plugin automatically discovers and runs bash blocks
in markdown files alongside your regular tests.

## Setup

Install outmatch in your project - the plugin registers automatically:

```console
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
pytest docs/                      # Run all markdown tests
pytest docs/cli.md                # Run specific file
pytest docs/cli.md --collect-only # See discovered tests
```

## Test Discovery

Every ` ```bash ` block becomes a test item. When you run
`pytest docs/ --collect-only`, you'll see output like:

```
<MarkdownFile cli.md>
  <MarkdownItem Version (line 8)>
  <MarkdownItem Exit Codes (line 20)>
  ...
```

Test names come from the preceding markdown heading.

## Output

Results appear in standard pytest format:

```
docs/cli.md::Version (line 8) PASSED
docs/cli.md::Exit Codes (line 20) PASSED
...
================== 15 passed in 2.34s ==================
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

```
FAILED docs/example.md::Test Name (line 10)
  Command:
    echo "wrong"
  Expected: right
  Actual: wrong
  Exit code: 1
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
