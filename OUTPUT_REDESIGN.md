# Output Redesign Spec

## Problem

Current test output is too verbose for automated workflows:

```
docs/cli.md::Version (line 8) PASSED
docs/cli.md::Exit Codes (line 20) PASSED
docs/cli.md::Quiet Mode (line 35) PASSED
... (126 more lines)
================== 4 failed, 122 passed in 202.67s ===================
```

This fills LLM context windows and obscures failures in CI logs.

## Design Goals

1. **Default output shows only what matters** - failures and summary
2. **Quiet mode is truly quiet** - one line
3. **Verbose mode exists for debugging** - current behavior
4. **Progressive disclosure** - more detail on demand

## Proposed Output Modes

### Quiet (`-q`)

Single line, machine-parseable:

```
✓ 122 passed, ✗ 4 failed, 126 total (3.2s)
```

Exit code tells the story. Use for CI `if` conditions.

### Default (no flag)

Summary + failures only:

```
✗ docs/json.md:73 - Array element access
  Expected: {"items": [{"id": 2}]}
  Actual:   {"items": []}

✗ docs/mdtest.md:243 - Debugging Failures
  Expected to contain: Exit code: 42

4 failed, 122 passed, 126 total (3.2s)
```

Rules:
- Show each failure with file:line, name, and diff/error
- No output for passing tests
- Summary line at end
- Diff truncated to 10 lines (configurable)

### Verbose (`-v`)

Current behavior - every test listed:

```
✓ docs/cli.md:8 - Version
✓ docs/cli.md:20 - Exit Codes
✗ docs/json.md:73 - Array element access
  ...full diff...
```

### Debug (`-vv`)

Verbose + command output for passing tests:

```
✓ docs/cli.md:8 - Version
  Command: outmatch --version | outmatch --contains "0.2.0"
  Output: (empty)
  Duration: 0.12s
```

## Output Flags

| Flag | Behavior |
|------|----------|
| `-q` | One-line summary |
| (none) | Failures + summary |
| `-v` | All tests + failures |
| `-vv` | All tests + command output |
| `--no-color` | Disable ANSI colors |
| `--diff-lines N` | Max diff lines (default: 10) |

## Failure Format

```
✗ {file}:{line} - {name}
  {error_type}:
    {details indented 4 spaces}
    {truncated with "... (N more lines)"}
```

Error types:
- `Mismatch` - with diff
- `Exit code N` - with stderr
- `Timeout` - with duration
- `Error` - with message

## Summary Format

```
{passed} passed, {failed} failed, {skipped} skipped, {total} total ({duration}s)
```

Or on failure:
```
FAILED: {failed} failed, {passed} passed, {total} total ({duration}s)
```

## Implementation

### Files to Change

1. `src/outmatch/mdtest.py`
   - `format_result_quiet()` - already exists, keep as-is
   - `format_result_default()` - rewrite to failures-only
   - `format_result_verbose()` - current default behavior
   - Add `format_result_debug()` for `-vv`

2. `src/outmatch/cli.py`
   - Add `-vv` handling
   - Add `--diff-lines` option

### Backwards Compatibility

Current `-q` behavior is preserved. Current default becomes `-v`.
This is a breaking change for scripts parsing default output.

Consider: environment variable `OUTMATCH_OUTPUT=verbose` to opt-in
to old behavior during migration.

## pytest Plugin

The pytest plugin uses pytest's output system. Changes here only
affect `outmatch test`, not `pytest docs/`.

For pytest, users control verbosity with pytest flags (`-v`, `-q`).

## Examples

### CI Pipeline (quiet)

```yaml
- run: outmatch test docs/ -q
```

Output on success: `✓ 126 passed, 126 total (3.2s)`
Output on failure: `✗ 4 failed, 122 passed, 126 total (3.2s)`

### Local Development (default)

```bash
$ outmatch test docs/
✗ docs/json.md:73 - Array element access
  Mismatch:
    -{"items": [{"id": 2}]}
    +{"items": []}

1 failed, 125 passed, 126 total (3.1s)
```

### Debugging (verbose)

```bash
$ outmatch test docs/ -v
✓ docs/cli.md:8 - Version
✓ docs/cli.md:20 - Exit Codes
✗ docs/json.md:73 - Array element access
  ...
```

## Open Questions

1. Should `--tap` and `--junit-xml` modes be affected?
2. Should we add `--json` output for programmatic parsing?
3. Progress indicator for long-running test suites?
4. Color scheme for colorblind accessibility?

## Timeline

Target: Next sprint

Tasks:
1. Refactor `format_result_*` functions
2. Add `-vv` mode
3. Update docs to reflect new defaults
4. Add migration note to changelog
