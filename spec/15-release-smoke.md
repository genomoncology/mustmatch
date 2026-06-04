# Release smoke gate

The normal spec gate proves the source-tree binary. Release also needs a small
installed-wheel smoke gate so packaging and the console entry point fail before
PyPI publish, not after users install the wheel.

## Smoke document is tracked

The smoke gate has its own self-contained Markdown document. It is separate from
`spec/` because the full contract uses repository fixtures while the release
smoke must run from an installed binary only.

```bash
git -C .. ls-files tests/smoke/smoke.md | mustmatch "tests/smoke/smoke.md"
```

## Local release smoke target

Maintainers can run the same installed-wheel smoke locally before tagging. The
help output lists the target with the other gates so it is discoverable.

```bash
make -C .. help | mustmatch like "Targets:
  smoke"
```

## Release publish is gated by smoke

The release workflow runs smoke after wheel artifacts are available and before
PyPI publish. That ordering is the protection: a bad wheel fails the job before
it can ship.

```bash
awk '/make smoke|pypa\/gh-action-pypi-publish/{print}' ../.github/workflows/release.yml | mustmatch like "make smoke
...
pypa/gh-action-pypi-publish"
```
