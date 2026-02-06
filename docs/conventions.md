# Conventions

These conventions keep executable documentation readable for humans and predictable for automation.

## Document Structure

- H1: capability overview
- H2: scenario with short context
- Tables: expected inputs/outputs
- Code blocks: executable checks for the nearby scenario

## Block Selection

- Use `bash` for CLI behavior checks.
- Use `python` for structured validation.
- Use `python each_row` for table-driven checks.

## Data Modeling In Tables

- Keep column names human-readable.
- Put inputs and expected outputs in the same row.
- Use `str:` prefix for string literals that look numeric (for example `str:zip_code`).

## Shared Setup

Use a `python setup` block when multiple blocks in a section need the same baseline state.

## Expected Failure And Timing

- Use `expect_error="..."` for documented failure behavior.
- Use `perf=...` for lightweight runtime assertions.

## Naming

Prefer numbered, descriptive Markdown file names such as:

- `01-overview.md`
- `02-cli-behavior.md`
- `03-edge-cases.md`
