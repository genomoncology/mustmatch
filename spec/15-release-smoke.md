# Release smoke gate

The normal spec gate proves the source-tree binary. Release also needs a small
installed-wheel smoke gate so packaging and the console entry point fail before
PyPI publish, not after users install the wheel.

## Smoke document is self-contained

The smoke gate has its own self-contained Markdown document. It is separate from
`spec/` because the full contract uses repository fixtures while the release
smoke must run from an installed binary only. The smoke document covers both
installed entry paths: a stdin assertion and a nested `mustmatch test` run over
an embedded example file.

```bash
git -C .. ls-files tests/smoke/smoke.md | mustmatch "tests/smoke/smoke.md"

awk '
  /^````markdown file=nested-smoke\.md$/ { in_fixture=1; print "embedded fixture: nested-smoke.md"; next }
  in_fixture && /^````$/ { in_fixture=0; in_nested_bash=0; next }
  in_fixture && /^```bash$/ { in_nested_bash=1; print "nested executable bash"; next }
  in_fixture && in_nested_bash && /^```$/ { in_nested_bash=0; next }
  in_fixture && in_nested_bash && /^[[:space:]]*[^#].*\|[[:space:]]*mustmatch/ { print "nested assertion pipe"; next }
' ../tests/smoke/smoke.md | mustmatch like "embedded fixture: nested-smoke.md
nested executable bash
nested assertion pipe"

awk '
  /^````markdown file=nested-smoke\.md$/ { in_fixture=1; next }
  in_fixture && /^````$/ { in_fixture=0; next }
  !in_fixture && /^```bash$/ { in_bash=1; next }
  in_bash && /^```$/ { in_bash=0; next }
  in_bash && /^printf .*\| mustmatch/ { print "top-level stdin assertion"; next }
  in_bash && /^mustmatch test nested-smoke\.md \| mustmatch/ { print "top-level nested smoke test command"; next }
' ../tests/smoke/smoke.md | mustmatch like "top-level stdin assertion
top-level nested smoke test command"

awk '/cargo|target\/|\.\.\//{print}' ../tests/smoke/smoke.md | mustmatch ""
```

## Local release smoke target

Maintainers can run the same installed-wheel smoke locally before tagging. The
help output lists the target with the other gates so it is discoverable.

```bash
awk '/^\.PHONY: .*smoke|^smoke:|  smoke/{print}' ../Makefile | mustmatch like ".PHONY:
smoke:
  smoke"
```

## Release publish is gated by smoke

The release workflow runs smoke after wheel artifacts are available and before
PyPI publish. That ordering is the protection: a bad wheel fails the job before
it can ship.

```bash
awk '/publish:|actions\/checkout|actions\/download-artifact|pattern: wheels-\*|run: make smoke|pypa\/gh-action-pypi-publish/{print}' ../.github/workflows/release.yml | mustmatch like "publish:
...
actions/checkout
...
actions/download-artifact
...
pattern: wheels-*
...
run: make smoke
...
pypa/gh-action-pypi-publish"
```
