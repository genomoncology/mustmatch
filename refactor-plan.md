# Refactor Implementation Plan

Based on REFACTOR.md specification. Organized by phase.

---

## Phase 1: Add New Grammar (Non-Breaking)

### 1.1 Auto-Detection Module

**New file:** `src/mustmatch/detect.py`

```python
def detect_type(value: str) -> Literal["string", "regex", "json"]:
    """Detect comparison type from syntax."""
    # /pattern/ → regex
    # {...} or [...] → json
    # else → string
```

- Regex: starts with `/` and ends with `/`
- JSON object: starts with `{` and ends with `}`
- JSON array: starts with `[` and ends with `]`
- Everything else: string

**Changes:** `cli.py` - call `detect_type()` when no explicit mode flag given

---

### 1.2 Grammar Parser for `like` and `not`

**File:** `cli.py`

Add positional argument parsing before EXPECTED:

```
mustmatch [-i] [not] [like] EXPECTED
```

Implementation options:
1. Custom argv preprocessing before argparse
2. Use argparse subparsers creatively
3. Parse manually, then delegate to argparse for flags

Recommended: Option 1 - preprocess argv to extract `not`/`like` modifiers, set internal flags, then pass remainder to existing argparse.

**New internal state:**
```python
@dataclass
class MatchMode:
    negated: bool = False      # `not` present
    partial: bool = False      # `like` present
    case_insensitive: bool = False  # -i flag
```

---

### 1.3 Map New Grammar to Existing Comparisons

| New syntax | Maps to existing |
|------------|------------------|
| `mustmatch X` | `--exact` (string) or `--json` (auto-detect) |
| `mustmatch like X` | `--contains` (string) or JSON subset |
| `mustmatch not X` | `--not-exact` |
| `mustmatch not like X` | `--not-contains` |
| `mustmatch /pat/` | `--regex` |
| `mustmatch not /pat/` | `--not-regex` |

No new comparison logic needed - just routing.

---

### 1.4 Hardcode Normalizations

**File:** `cli.py`, `compare.py`

Always apply (remove flags):
- Strip ANSI escape sequences
- Normalize CRLF → LF

These should happen unconditionally in the input normalization step.

---

## Phase 2: Literate Test Output

### 2.1 Update Output Formatters

**File:** `mdtest.py` - functions to modify:

#### `format_block_name()` (line 607)

Change from:
```python
def format_block_name(block: Block) -> str:
    if block.name:
        return f"Block (line {block.line_start}): {block.name}"
    return f"Block (line {block.line_start})"
```

To:
```python
def format_block_name(block: Block, file_path: str) -> str:
    location = f"({file_path}:{block.line_start})"
    if block.name:
        return f"{block.name} {location}"
    return f"Block {location}"
```

#### `format_result_default()` (line 635)

Change to show **failures only** with literate format:

```python
def format_result_default(result: TestResult) -> str:
    lines: list[str] = []

    for file_result in result.files:
        for block_result in file_result.blocks:
            if block_result.status == BlockStatus.FAILED:
                name = format_block_name(block_result.block, file_result.path)
                lines.append(f"FAILED: {name}")
                if block_result.expected:
                    lines.append(f"  Expected: {block_result.expected}")
                if block_result.actual:
                    lines.append(f"  Got: {block_result.actual}")
                lines.append("")

    lines.append(f"{result.failed} failed, {result.passed} passed, {result.total} total")
    return "\n".join(lines)
```

#### `format_result_verbose()` (line 665)

Change to show **all tests** with literate format:

```python
def format_result_verbose(result: TestResult) -> str:
    lines: list[str] = []

    for file_result in result.files:
        for block_result in file_result.blocks:
            name = format_block_name(block_result.block, file_result.path)

            if block_result.status == BlockStatus.PASSED:
                lines.append(f"✓ {name}")
            elif block_result.status == BlockStatus.FAILED:
                lines.append(f"FAILED: {name}")
                if block_result.expected:
                    lines.append(f"  Expected: {block_result.expected}")
                if block_result.actual:
                    lines.append(f"  Got: {block_result.actual}")
                lines.append("")
            elif block_result.status == BlockStatus.SKIPPED:
                lines.append(f"⊘ {name} (skipped)")
            elif block_result.status == BlockStatus.TIMEOUT:
                lines.append(f"⏱ {name} (timeout)")

    lines.append("")
    lines.append(f"{result.failed} failed, {result.passed} passed, {result.total} total")
    return "\n".join(lines)
```

#### `format_result_quiet()` (line 614)

Keep as-is (summary only):
```
✓ 42 passed, ✗ 2 failed, 44 total
```

---

### 2.2 Populate `expected` Field

**File:** `mdtest.py`

When executing blocks, extract the expected value from mustmatch assertions and store in `BlockResult.expected`.

For bash blocks with `| mustmatch "expected"`:
- Parse the mustmatch argument from the command
- Store in `expected` field before execution

Location: `execute_block()` function - add expected extraction logic.

---

## Phase 3: Deprecation Warnings

### 3.1 Add Deprecation Messages

**File:** `cli.py`

When legacy flags are used, emit warning to stderr:

```python
DEPRECATIONS = {
    "--contains": "Use 'mustmatch like' instead",
    "--regex": "Use 'mustmatch /pattern/' instead",
    "--json": "Use 'mustmatch {...}' instead",
    "--not-contains": "Use 'mustmatch not like' instead",
    "--not-regex": "Use 'mustmatch not /pattern/' instead",
}

def warn_deprecation(flag: str) -> None:
    if flag in DEPRECATIONS:
        print(f"Warning: {flag} is deprecated. {DEPRECATIONS[flag]}", file=sys.stderr)
```

Call `warn_deprecation()` when parsing legacy flags.

---

## Phase 4: Remove Deprecated Flags (Major Version)

### 4.1 Remove from CLI

**File:** `cli.py`

Delete argparse definitions for:
- `--contains`
- `--not-contains`
- `--regex`
- `--not-regex`
- `--json`
- `--jsonl` variants
- `--strip-ansi` (now default)
- `--normalize-newlines` (now default)

### 4.2 Update Documentation

- README.md
- docs/*.md
- Help text in cli.py

---

## File Change Summary

| File | Changes |
|------|---------|
| `cli.py` | Grammar parsing, auto-detection, deprecation warnings, flag removal |
| `mdtest.py` | Output formatters, expected field population |
| `detect.py` | **New** - type auto-detection |
| `compare.py` | Ensure normalizations always applied |
| `config.py` | Add `MatchMode` dataclass if needed |

---

## Testing Strategy

1. **Phase 1 tests:** Verify new grammar produces same results as old flags
2. **Phase 2 tests:** Snapshot tests for output format changes
3. **Phase 3 tests:** Verify deprecation warnings appear
4. **Phase 4 tests:** Verify old flags error gracefully

Add tests in `tests/test_refactor.py` for each phase.

---

## Implementation Order

1. `detect.py` - auto-detection (isolated, easy to test)
2. Grammar parsing in `cli.py` (route to existing logic)
3. Output formatters in `mdtest.py` (user-visible improvement)
4. Deprecation warnings (non-breaking)
5. Flag removal (breaking, major version)
