# Overview

mustmatch is an assertion layer for command pipelines and executable Markdown. The same package gives you a small CLI for stdin checks and a pytest plugin for docs-as-tests. This overview establishes the core behavior that later files build on.

## Two Surfaces

The CLI is optimized for shell pipelines, while the pytest plugin executes `bash` and `python` blocks embedded in docs. Both surfaces share the same comparison and normalization rules, so examples stay consistent between terminal checks and documentation tests.

| Surface | Purpose | Entry point |
|---------|---------|-------------|
| CLI | Assert command output from stdin | `mustmatch` |
| Pytest plugin | Run markdown blocks as tests | `python -m pytest docs/` |

## Basic Behavior

A passing match exits with code `0`. These commands demonstrate exact, contains, and negated contains assertions in normal pipelines.

```bash
echo "hello" | mustmatch "hello"
echo "hello world" | mustmatch like "world"
echo "operation successful" | mustmatch not like "error"
```
