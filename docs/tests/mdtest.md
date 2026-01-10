# Markdown Test Runner

Run bash code blocks in your markdown documentation as tests with `outmatch test`.

Your documentation contains executable examples. The test runner extracts every fenced `bash` block and runs it. If any command exits non-zero, that test fails. Your docs become a living test suite.

---

## Getting Started

### How do I run tests on my documentation?

Point `outmatch test` at a file or directory:

```bash
printf '```bash\necho hello\n```\n' > /tmp/basic.md
outmatch test /tmp/basic.md --quiet
```

### What exit codes does it return?

Exit 0 for all tests passing:

```bash
printf '```bash\ntrue\n```\n' > /tmp/pass.md
outmatch test /tmp/pass.md --quiet && echo "exit 0" | outmatch "exit 0"
```

Exit 1 if any test fails:

```bash
printf '```bash\nexit 1\n```\n' > /tmp/fail.md
outmatch test /tmp/fail.md --quiet 2>&1 || test $? -eq 1
```

### Can I test an entire directory?

Yes. It discovers markdown files recursively:

```bash
rm -rf /tmp/testdir
mkdir -p /tmp/testdir
printf '```bash\necho a\n```\n' > /tmp/testdir/a.md
printf '```bash\necho b\n```\n' > /tmp/testdir/b.md
outmatch test /tmp/testdir --quiet | outmatch --contains "2 passed"
```

`node_modules` and similar directories are automatically excluded:

```bash
rm -rf /tmp/testdir2
mkdir -p /tmp/testdir2/node_modules
printf '```bash\necho good\n```\n' > /tmp/testdir2/good.md
printf '```bash\nexit 1\n```\n' > /tmp/testdir2/node_modules/skip.md
outmatch test /tmp/testdir2 --quiet | outmatch --contains "1 passed"
```

---

## Output Formats

### What output modes are available?

**Default mode** - Progress and summary:

```bash
printf '```bash\necho hi\n```\n' > /tmp/default.md
outmatch test /tmp/default.md 2>&1 | outmatch --contains "Results:"
```

**Quiet mode** - Summary only:

```bash
printf '```bash\necho a\n```\n```bash\necho b\n```\n' > /tmp/quiet.md
outmatch test /tmp/quiet.md --quiet | outmatch --contains "2 passed"
```

**Verbose mode** - Full block details:

```bash
printf '# Section\n```bash\necho test\n```\n' > /tmp/verbose.md
outmatch test /tmp/verbose.md --verbose 2>&1 | outmatch --contains "Block (line"
```

**TAP format** - Machine-readable:

```bash
printf '```bash\necho ok\n```\n' > /tmp/tap.md
outmatch test /tmp/tap.md --tap | outmatch --contains "TAP version 13"
```

```bash
printf '```bash\necho a\n```\n```bash\necho b\n```\n' > /tmp/tap2.md
outmatch test /tmp/tap2.md --tap | outmatch --contains "1..2"
```

### How do I generate report files?

**JUnit XML** for CI integration:

```bash
printf '```bash\necho test\n```\n' > /tmp/junit.md
outmatch test /tmp/junit.md --junit-xml /tmp/report.xml --quiet
cat /tmp/report.xml | outmatch --contains "testsuite"
```

**JSON** for custom processing:

```bash
printf '```bash\necho test\n```\n' > /tmp/json.md
outmatch test /tmp/json.md --json /tmp/report.json --quiet
cat /tmp/report.json | outmatch --contains '"passed": 1'
```

---

## Filtering Tests

### How do I run specific tests?

**By content pattern** - Include blocks containing text:

```bash
printf '```bash\n# include-me\necho yes\n```\n```bash\necho no\n```\n' > /tmp/include.md
outmatch test /tmp/include.md --include "include-me" --quiet | outmatch --contains "1 passed"
```

```bash
printf '# IncludeThis\n```bash\necho hi\n```\n# OtherTest\n```bash\necho bye\n```\n' > /tmp/incname.md
outmatch test /tmp/incname.md --include "IncludeThis" --quiet | outmatch --contains "1 passed"
```

**By exclusion** - Skip blocks containing text:

```bash
printf '```bash\necho run\n```\n```bash\n# exclude-me\necho skip\n```\n' > /tmp/exclude.md
outmatch test /tmp/exclude.md --exclude "exclude-me" --quiet | outmatch --contains "1 passed"
```

```bash
printf '# SkipThis\n```bash\nexit 1\n```\n# RunThis\n```bash\necho ok\n```\n' > /tmp/excname.md
outmatch test /tmp/excname.md --exclude "SkipThis" --quiet | outmatch --contains "1 passed"
```

**By line number** - Run block at specific line:

```bash
printf '```bash\necho first\n```\n```bash\necho second\n```\n' > /tmp/line.md
outmatch test /tmp/line.md --line 2 --quiet | outmatch --contains "1 passed"
```

---

## Skip Directives

### How do I skip a test block?

Add an HTML comment before the block:

```bash
printf '<!-- outmatch: skip -->\n```bash\nexit 1\n```\n```bash\necho runs\n```\n' > /tmp/skip.md
outmatch test /tmp/skip.md --quiet | outmatch --contains "1 skipped"
```

### How do I skip conditionally?

Use `skip-if` with an environment variable:

```bash
printf '<!-- outmatch: skip-if=SKIP_ME -->\n```bash\nexit 1\n```\n' > /tmp/skipif.md
SKIP_ME=1 outmatch test /tmp/skipif.md --quiet | outmatch --contains "1 skipped"
```

---

## Test Configuration

### How do I set a timeout?

Per-block with a directive:

```bash
printf '<!-- outmatch: timeout=5 -->\n```bash\nsleep 0.1\n```\n' > /tmp/timeout.md
outmatch test /tmp/timeout.md --quiet
```

Globally with `--timeout`:

```bash
printf '```bash\nsleep 10\n```\n' > /tmp/slow.md
outmatch test /tmp/slow.md --timeout 1 --verbose 2>&1 | outmatch --contains "timeout"
```

### How do I pass environment variables?

Via `--env`:

```bash
printf '```bash\ntest -n "$MY_VAR" && echo "has var"\n```\n' > /tmp/env.md
outmatch test /tmp/env.md --env MY_VAR=hello --quiet 2>&1 | outmatch --contains "1 passed"
```

Via directive:

```bash
printf '<!-- outmatch: env=FOO=bar -->\n```bash\ntest "$FOO" = "bar"\n```\n' > /tmp/envmeta.md
outmatch test /tmp/envmeta.md --quiet
```

### How do I change the working directory?

Tests run in the markdown file's directory by default:

```bash
mkdir -p /tmp/testcwd
printf '```bash\npwd | grep -q testcwd\n```\n' > /tmp/testcwd/cwd.md
outmatch test /tmp/testcwd/cwd.md --quiet
```

Override with `--cwd`:

```bash
printf '```bash\npwd\n```\n' > /tmp/cwd.md
outmatch test /tmp/cwd.md --cwd /tmp --quiet
```

---

## Debugging Failures

### How do I see what failed?

Verbose mode shows command and output:

```bash
printf '```bash\nfalse\n```\n' > /tmp/vcmd.md
outmatch test /tmp/vcmd.md --verbose 2>&1 | outmatch --contains "Command:"
```

```bash
printf '```bash\nexit 42\n```\n' > /tmp/error.md
outmatch test /tmp/error.md --verbose 2>&1 | outmatch --contains "Exit code 42"
```

### How do I stop on first failure?

Use `--fail-fast`:

```bash
printf '```bash\nexit 1\n```\n```bash\necho second\n```\n' > /tmp/failfast.md
outmatch test /tmp/failfast.md --fail-fast --quiet | outmatch --contains "1 failed"
```

---

## Test Names

### Where do test names come from?

From the nearest heading above the block:

```bash
printf '# My Test\n```bash\necho hello\n```\n' > /tmp/heading.md
outmatch test /tmp/heading.md --verbose 2>&1 | outmatch --contains "My Test"
```

From a comment on the first line:

```bash
printf '```bash\n# Custom Name\necho hello\n```\n' > /tmp/comment.md
outmatch test /tmp/comment.md --verbose 2>&1 | outmatch --contains "Custom Name"
```

---

## TAP and Report Details

### What does TAP output look like on failure?

```bash
printf '```bash\nexit 1\n```\n' > /tmp/tapfail.md
outmatch test /tmp/tapfail.md --tap 2>&1 | outmatch --contains "not ok 1"
```

```bash
printf '<!-- outmatch: skip -->\n```bash\necho hi\n```\n' > /tmp/tapskip.md
outmatch test /tmp/tapskip.md --tap 2>&1 | outmatch --contains "SKIP"
```

```bash
printf '```bash\nsleep 10\n```\n' > /tmp/tapto.md
outmatch test /tmp/tapto.md --tap --timeout 1 2>&1 | outmatch --contains "TIMEOUT"
```

### What does JUnit XML include?

Failures:

```bash
printf '```bash\nexit 1\n```\n' > /tmp/junitfail.md
outmatch test /tmp/junitfail.md --junit-xml /tmp/jfail.xml --quiet 2>&1 || true
cat /tmp/jfail.xml | outmatch --contains "failure"
```

Timeouts:

```bash
printf '```bash\nsleep 10\n```\n' > /tmp/junitto.md
outmatch test /tmp/junitto.md --junit-xml /tmp/jto.xml --timeout 1 --quiet 2>&1 || true
cat /tmp/jto.xml | outmatch --contains "error"
```

Skips:

```bash
printf '<!-- outmatch: skip -->\n```bash\necho hi\n```\n' > /tmp/junitskip.md
outmatch test /tmp/junitskip.md --junit-xml /tmp/jskip.xml --quiet
cat /tmp/jskip.xml | outmatch --contains "skipped"
```

---

## Edge Cases

Long commands and output are truncated in verbose mode:

```bash
printf '```bash\necho line1\necho line2\necho line3\necho line4\necho line5\necho line6\nexit 1\n```\n' > /tmp/longcmd.md
outmatch test /tmp/longcmd.md --verbose 2>&1 | outmatch --contains "..."
```

```bash
printf '```bash\nfor i in $(seq 1 20); do echo "line $i"; done; exit 1\n```\n' > /tmp/longout.md
outmatch test /tmp/longout.md --verbose 2>&1 | outmatch --contains "..."
```

Invalid timeout in metadata is ignored:

```bash
printf '<!-- outmatch: timeout=abc -->\n```bash\necho hi\n```\n' > /tmp/badto.md
outmatch test /tmp/badto.md --quiet
```

Running without a path uses current directory:

```bash
rm -rf /tmp/cwdtest && mkdir /tmp/cwdtest && cd /tmp/cwdtest && printf '```bash\necho test\n```\n' > test.md && outmatch test --quiet
```

Empty directories are not an error:

```bash
rm -rf /tmp/emptydir
mkdir -p /tmp/emptydir
outmatch test /tmp/emptydir --quiet
```
