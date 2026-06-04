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

awk '/file=|mustmatch test|\| mustmatch/{print}' ../tests/smoke/smoke.md | mustmatch like "file=
| mustmatch
mustmatch test"

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
