# Pytest Integration

Run markdown tests as part of your pytest suite.

The outmatch pytest plugin automatically discovers and runs markdown files alongside your regular tests. No extra configuration needed - just run `pytest` on your docs directory.

## How do I run markdown tests with pytest?

Just point pytest at your markdown files:

<!-- outmatch: skip -->
```bash
pytest docs/tests/version.md --collect-only
```

## Does it discover tests automatically?

Yes. Pytest collects markdown files and shows the test count.

## Do tests run normally?

Yes. Results appear in standard pytest output:

<!-- outmatch: skip -->
```bash
pytest docs/tests/version.md -v
```

## Where do test names come from?

From markdown headings. Test names like "Version flag" appear in output.

## Does it show file locations?

Yes. File paths like `version.md` are reported alongside test names.
