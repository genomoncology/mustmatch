# outmatch Review and Roadmap

**Date**: 2026-01-08
**Current name**: `doctest-expect`
**Proposed name**: `outmatch`

---

## Executive Summary

The tool evolved from a simple 236-line stdin assertion tool to a comprehensive 910-line output testing framework with 9 modules, 7 comparison modes, normalization, pattern transformation, and snapshot testing.

**Assessment**: NOT too complicated. Complexity is opt-in, simple cases remain simple, and each feature solves real problems.

**Recommendation**: Rename to `outmatch` and proceed with targeted feature additions.

---

## Review of Recent Changes

### What Changed (PR #2)

**Structural refactoring** (good):
- ✅ Decomposed 800-line monolith into 9 focused modules
- ✅ Max module size: 340 lines (compare.py), most under 100
- ✅ Used Typer for modern CLI with type hints
- ✅ Self-hosted documentation testing (dogfooding)

**New comparison modes** (good):
- ✅ `--regex` - essential for volatile output (timestamps, IDs)
- ✅ `--jsonl-set` - order-independent JSONL (common need)
- ✅ `--jsonl-key` - match by key field (solves real problem)

**Normalization options** (good):
- ✅ `--strip-ansi` - critical for CLIs with colors
- ✅ `--normalize-newlines` - Windows compat
- ✅ `--trim`, `--collapse-whitespace`, `--ignore-case` - reduce flakiness

**Pattern transformation** (good):
- ✅ `--replace REGEX REPL` - replace volatile content
- ✅ `--redact REGEX` - mask sensitive data
- ✅ Solves "timestamp in output" problem cleanly

**Advanced features** (good):
- ✅ `--expected-file` - cleaner multi-line expectations
- ✅ `--update` - snapshot testing pattern (Jest-style)
- ✅ `--json-ignore PATH` - skip volatile JSON fields
- ✅ Colored diff output with context

### Is It Too Complicated?

**No.** Here's why:

1. **Simple cases are still simple**:
   ```bash
   echo "hello" | expect "hello"  # Still works
   ```

2. **Complexity is opt-in**:
   - Default behavior unchanged
   - Each flag is independent
   - Compose only what you need

3. **Each feature solves real problems**:
   - ANSI stripping: CLIs with colors
   - Regex: Timestamps, IDs, variable output
   - Replace/redact: Volatile content
   - Expected from file: Multi-line expectations
   - Update mode: Snapshot testing workflow

4. **Well-structured**:
   - 9 modules, each focused
   - Clear separation of concerns
   - Testable, maintainable

5. **Follows Unix philosophy**:
   - One tool, many options
   - Flags compose naturally
   - Pipe-friendly

### What Could Be Simpler

**Minor concerns** (not blockers):

1. **Too many JSONL modes?** (7 total modes)
   - Consider: Are all variants needed?
   - Most common: EXACT, CONTAINS, JSONL
   - Less common: REGEX, JSON, JSONL-SET, JSONL-KEY, JSONL-CONTAINS
   - **Verdict**: Keep all - they're opt-in and solve real use cases

2. **Pattern transformation might confuse**:
   - `--replace REGEX REPL` requires pairs
   - `--redact REGEX` simpler but less flexible
   - **Verdict**: Good tradeoff, well-documented

3. **CLI help could be overwhelming**:
   - 20+ flags when you run `--help`
   - **Mitigation**: Group flags logically (already done in code)

### Critical Gap: Documentation

The refactor added comprehensive examples but docs need:
- ✅ Clear "simple → advanced" progression
- ✅ Common recipes section
- ⚠️ When NOT to use certain features
- ⚠️ Performance implications (regex vs exact)

---

## Roadmap

### Phase 1: Rename and Stabilize (Immediate)

#### 1.1 Rename to `outmatch`

**Why**: `doctest-expect` is confusing
- "doctest" conflicts with Python stdlib
- Doesn't describe what it does
- Not discoverable

**Why `outmatch`**:
- Portmanteau: "output" + "match"
- Clear in context: `cmd | outmatch "expected"`
- No conflicts (Python keyword, existing tools)
- Memorable, distinctive

**Changes**:
- Package name: `outmatch`
- CLI command: `outmatch`
- Module: `outmatch` (rename `doctest_expect`)
- Update all docs, imports, examples

**Timeline**: 1 day

#### 1.2 Error Message Quality Audit

Review error messages for:
- Clarity: Are failures obvious?
- Actionability: Do errors suggest fixes?
- Verbosity: Are diffs readable?

**Test scenarios**:
- Simple mismatch: "hello" vs "world"
- JSONL record mismatch
- Regex pattern failure
- File not found
- Invalid arguments

**Output levels**:
- `--quiet`: Suppress all output (exit code only)
- (default): Show concise diff
- (verbose already via `--diff-context`)

**Timeline**: 2 days

---

### Phase 2: Markdown File Testing (High Priority)

**Goal**: Run `outmatch` directly on markdown files containing bash blocks.

**Problem**: Currently requires pytest + mktestdocs integration. Users want standalone markdown testing.

**Design**:

```bash
# Run all bash blocks in a markdown file
outmatch test docs/cli.md

# With verbosity
outmatch test docs/ --quiet      # Just pass/fail count
outmatch test docs/              # Show which blocks failed
outmatch test docs/ --verbose    # Show full diffs
```

**Implementation**:

1. Add `outmatch test [FILES...]` subcommand
2. Parse markdown for bash blocks (reuse mktestdocs logic or write own)
3. Execute blocks, capture output
4. Look for `| outmatch` patterns in blocks
5. Report results with block line numbers

**Output format**:

```
Running tests in docs/cli.md...

  ✓ Block 1 (line 23): Basic usage
  ✗ Block 2 (line 45): Version check
    Expected: findterms 0.1.0
    Actual:   findterms 0.2.0
  ✓ Block 3 (line 67): Help text

Results: 2 passed, 1 failed, 3 total
```

**Verbosity levels**:
- `--quiet`: "2/3 passed"
- Default: Block-level pass/fail with line numbers
- `--verbose`: Include full diffs for failures

**Timeline**: 1 week

**Status**: RECOMMENDED - fills gap between "just a CLI tool" and "pytest integration"

---

### Phase 3: PyTest Plugin (Medium Priority)

**Goal**: Native pytest integration without mktestdocs dependency.

**Why**:
- `mktestdocs` is not maintained actively
- Simplify dependency tree
- Better pytest integration (fixtures, markers, etc.)
- Not Python-specific (test any CLI)

**Design**:

```python
# tests/test_docs.py
import pytest
from outmatch.pytest import collect_markdown_tests

@pytest.mark.parametrize("test", collect_markdown_tests("docs/"))
def test_bash_blocks(test):
    test.run()  # Executes block, asserts via outmatch patterns
```

**Implementation**:

1. Create `outmatch.pytest` module
2. Implement `collect_markdown_tests(path)` collector
3. Parse markdown, find bash blocks
4. Create test items with proper pytest integration
5. Support pytest fixtures, markers
6. Parallel execution via pytest-xdist

**Benefits over mktestdocs**:
- Direct integration (no subprocess)
- Better error reporting (pytest's native output)
- Fixture support (setup/teardown)
- Marker support (`@pytest.mark.slow`)
- Coverage integration

**Timeline**: 2 weeks

**Status**: RECOMMENDED - better than mktestdocs for Python projects

---

### Phase 4: Language-Agnostic Testing (Low Priority)

**Goal**: Test CLIs in any language, not just Python projects.

**Use case**:
- Rust CLI with markdown docs
- Go CLI with markdown docs
- Any language + markdown

**Design**:

Make `outmatch` completely standalone:
- No Python test framework required
- Reads markdown, runs tests, reports results
- Exit code 0 (all pass) or 1 (any fail)

**Usage**:

```bash
# In Rust project
outmatch test README.md

# In CI
outmatch test docs/ || exit 1
```

**Implementation**:

Enhance Phase 2 to be completely standalone:
- No pytest dependency
- JUnit XML output for CI (`--junit-xml=report.xml`)
- TAP format output (`--tap`)
- JSON output (`--json`)

**Timeline**: 1 week (after Phase 2)

**Status**: NICE TO HAVE - makes tool universal

---

## Ideas: 10 Crazy Things We Could Do

### 1. **Shell Script Testing** (Rejected for now)

**Idea**: Run a shell script with `outmatch` assertions, report results.

**Why rejected**:
- Shell scripts should just use `outmatch` directly
- `set -e` already handles failures
- Adding a test runner is scope creep
- Better done by shell test frameworks (bats, shunit2)

**Verdict**: OUT OF SCOPE

---

### 2. **Watch Mode** (Interesting)

```bash
outmatch watch docs/ --rerun-on-change
```

**Use case**: TDD workflow for documentation

**Implementation**: Watch files, re-run on change (like `pytest-watch`)

**Verdict**: POSSIBLE FUTURE (after Phase 2)

---

### 3. **Record Mode** (Very Interesting)

```bash
# Record actual output as expected
mycli run | outmatch --record mycli.txt
```

**Use case**: Generate expected files from current output

**Implementation**: Write stdin to file

**Verdict**: EASY WIN (alias for `tee`)

---

### 4. **Approval Testing** (Jest-style)

```bash
outmatch test docs/ --update-snapshots
```

**Use case**: Bulk update all expected files

**Implementation**: Enhance `--update` to work with markdown testing

**Verdict**: NICE TO HAVE (after Phase 2)

---

### 5. **Interactive Diff** (Git-style)

```bash
outmatch test docs/ --interactive
# Shows diff, asks: [A]ccept, [R]eject, [S]kip, [Q]uit
```

**Use case**: Review and approve changes interactively

**Verdict**: POSSIBLE FUTURE (nice UX)

---

### 6. **Coverage Tracking**

```bash
outmatch test docs/ --coverage
# Reports which CLI commands/flags are tested
```

**Use case**: Ensure all CLI features have doc tests

**Verdict**: INTERESTING but complex

---

### 7. **Fuzz Testing Integration**

```bash
outmatch fuzz mycli --corpus=inputs/ --oracle=outmatch_checks.sh
```

**Use case**: Generate test inputs, assert invariants

**Verdict**: OUT OF SCOPE (dedicated fuzzers exist)

---

### 8. **Performance Regression Detection**

```bash
outmatch bench docs/ --compare-to=baseline.json
```

**Use case**: Track CLI performance over time

**Verdict**: OUT OF SCOPE (use hyperfine, pyperf)

---

### 9. **Multi-Language Docs**

```bash
outmatch test docs/ --lang=python,bash,ruby
```

**Use case**: Test multiple code block types in same file

**Verdict**: ALREADY POSSIBLE (run twice with different `--lang`)

---

### 10. **HTTP API Testing** (Most Interesting)

```bash
curl /api/users | outmatch --jsonl-key id users.expected.jsonl
```

**Use case**: Test REST APIs in documentation

**Current state**: Already works! Just pipe curl to outmatch

**Enhancement**: Add `--http` mode that handles status codes, headers

```bash
outmatch --http GET /api/users --expect-status 200 --expect-json '{"users": [...]}'
```

**Verdict**: POSSIBLE FUTURE (different tool? `httpatch`?)

---

## Priorities

### Must Have (Phase 1)
1. ✅ Rename to `outmatch`
2. ✅ Error message audit

### Should Have (Phase 2)
3. 🎯 Markdown file testing (`outmatch test docs/`)
4. 🎯 Verbosity levels (quiet, default, verbose)

### Nice to Have (Phase 3+)
5. 💡 PyTest plugin
6. 💡 Watch mode
7. 💡 Interactive approval
8. 💡 Language-agnostic CI output (JUnit, TAP)

### Out of Scope
- ❌ Shell script test runner
- ❌ HTTP API testing (separate tool)
- ❌ Fuzz testing
- ❌ Performance benchmarking

---

## Success Metrics

After Phase 2 completion:

1. **Usability**: Run `outmatch test README.md` in any project
2. **Discoverability**: Clear error messages guide users
3. **Adoption**: Used in FindTerms and BotAssembly docs
4. **Dogfooding**: All `outmatch` docs tested by `outmatch`

---

## Next Actions

1. Review and approve this roadmap
2. Rename to `outmatch` (PR)
3. Error message audit (PR)
4. Begin Phase 2: Markdown testing (PR)
5. Update `spec/mktestdocs-standard.md` to reference `outmatch`
6. Publish `outmatch` to PyPI (not git dependency)
