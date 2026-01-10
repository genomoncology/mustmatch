# Markdown Test Runner

Run bash code blocks in your documentation as tests with `outmatch test`.

## Basic Usage

```bash
# Create and run a test file
echo '`''`''`bash'$'\n''echo hello'$'\n''`''`''`' > /tmp/demo.md
outmatch test /tmp/demo.md --quiet

# Test directories recursively (excludes node_modules)
rm -rf /tmp/testdir && mkdir -p /tmp/testdir
echo '`''`''`bash'$'\n''echo a'$'\n''`''`''`' > /tmp/testdir/a.md
echo '`''`''`bash'$'\n''echo b'$'\n''`''`''`' > /tmp/testdir/b.md
outmatch test /tmp/testdir --quiet | outmatch --contains "2 passed"
```

## Output Modes

```bash
echo '`''`''`bash'$'\n''echo test1'$'\n''`''`''`'$'\n''`''`''`bash'$'\n''echo test2'$'\n''`''`''`' > /tmp/modes.md
outmatch test /tmp/modes.md 2>&1 | outmatch --contains "Results:"
outmatch test /tmp/modes.md --quiet | outmatch --contains "2 passed"
outmatch test /tmp/modes.md --verbose 2>&1 | outmatch --contains "Block (line"
outmatch test /tmp/modes.md --tap | outmatch --contains "TAP version 13"
```

## Report Files

```bash
echo '`''`''`bash'$'\n''echo test'$'\n''`''`''`' > /tmp/report.md
outmatch test /tmp/report.md --junit-xml /tmp/report.xml --quiet
cat /tmp/report.xml | outmatch --contains "testsuite"
outmatch test /tmp/report.md --json /tmp/report.json --quiet
cat /tmp/report.json | outmatch --contains '"passed": 1'
```

## Filtering

```bash
echo '# TestA'$'\n''`''`''`bash'$'\n''echo a'$'\n''`''`''`'$'\n''# TestB'$'\n''`''`''`bash'$'\n''echo b'$'\n''`''`''`' > /tmp/filter.md
outmatch test /tmp/filter.md --include "TestA" --quiet | outmatch --contains "1 passed"
outmatch test /tmp/filter.md --exclude "TestB" --quiet | outmatch --contains "1 passed"
outmatch test /tmp/filter.md --line 3 --quiet | outmatch --contains "1 passed"
```

## Skip Directives

```bash
# Skip with HTML comment
echo '<!-- outmatch: skip -->'$'\n''`''`''`bash'$'\n''exit 1'$'\n''`''`''`'$'\n''`''`''`bash'$'\n''echo runs'$'\n''`''`''`' > /tmp/skip.md
outmatch test /tmp/skip.md --quiet | outmatch --contains "1 skipped"

# Conditional skip via environment variable
echo '<!-- outmatch: skip-if=CI -->'$'\n''`''`''`bash'$'\n''exit 1'$'\n''`''`''`' > /tmp/skipif.md
CI=1 outmatch test /tmp/skipif.md --quiet | outmatch --contains "1 skipped"
```

## Timeouts

```bash
# Per-block timeout
echo '<!-- outmatch: timeout=5 -->'$'\n''`''`''`bash'$'\n''sleep 0.1'$'\n''`''`''`' > /tmp/timeout.md
outmatch test /tmp/timeout.md --quiet

# Global timeout
echo '`''`''`bash'$'\n''sleep 10'$'\n''`''`''`' > /tmp/slow.md
outmatch test /tmp/slow.md --timeout 1 --verbose 2>&1 | outmatch --contains "timeout"
```

## Environment Variables

```bash
# Via --env flag
echo '`''`''`bash'$'\n''test -n "$MY_VAR"'$'\n''`''`''`' > /tmp/env.md
outmatch test /tmp/env.md --env MY_VAR=hello --quiet

# Via directive
echo '<!-- outmatch: env=FOO=bar -->'$'\n''`''`''`bash'$'\n''test "$FOO" = "bar"'$'\n''`''`''`' > /tmp/envdir.md
outmatch test /tmp/envdir.md --quiet
```

## Working Directory

```bash
# Tests run in markdown file's directory by default
mkdir -p /tmp/testcwd
echo '`''`''`bash'$'\n''pwd | grep -q testcwd'$'\n''`''`''`' > /tmp/testcwd/cwd.md
outmatch test /tmp/testcwd/cwd.md --quiet

# Override with --cwd
echo '`''`''`bash'$'\n''pwd'$'\n''`''`''`' > /tmp/cwd.md
outmatch test /tmp/cwd.md --cwd /tmp --quiet
```

## Debugging

```bash
# Verbose shows exit codes
echo '`''`''`bash'$'\n''exit 42'$'\n''`''`''`' > /tmp/fail.md
outmatch test /tmp/fail.md --verbose 2>&1 | outmatch --contains "Exit code 42"

# Stop on first failure
echo '`''`''`bash'$'\n''exit 1'$'\n''`''`''`'$'\n''`''`''`bash'$'\n''echo second'$'\n''`''`''`' > /tmp/multi.md
outmatch test /tmp/multi.md --fail-fast --quiet | outmatch --contains "1 failed"
```

## Test Names

```bash
# Names from headings and comments
echo '# My Test'$'\n''`''`''`bash'$'\n''echo hello'$'\n''`''`''`'$'\n''`''`''`bash'$'\n''# Custom Name'$'\n''echo world'$'\n''`''`''`' > /tmp/names.md
outmatch test /tmp/names.md --verbose 2>&1 | outmatch --contains "My Test"
outmatch test /tmp/names.md --verbose 2>&1 | outmatch --contains "Custom Name"
```

## Edge Cases

```bash
# Empty directories work
rm -rf /tmp/emptydir && mkdir /tmp/emptydir
outmatch test /tmp/emptydir --quiet

# node_modules excluded
rm -rf /tmp/nm && mkdir -p /tmp/nm/node_modules
echo '`''`''`bash'$'\n''echo good'$'\n''`''`''`' > /tmp/nm/good.md
echo '`''`''`bash'$'\n''exit 1'$'\n''`''`''`' > /tmp/nm/node_modules/skip.md
outmatch test /tmp/nm --quiet | outmatch --contains "1 passed"
```
