# Continuous Integration with mustmatch

## Overview

Make documentation a quality gate in your CI/CD pipeline. If examples break, builds fail.

## Quick Setup

### GitHub Actions

```yaml
# .github/workflows/docs.yml
name: Test Documentation

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Test documentation
        run: mustmatch test docs/

      - name: Test README
        run: mustmatch test README.md
```

### GitLab CI

```yaml
# .gitlab-ci.yml
test-docs:
  image: python:3.11
  script:
    - pip install mustmatch
    - mustmatch test docs/
    - mustmatch test README.md
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  test-docs:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run:
          name: Install mustmatch
          command: pip install mustmatch
      - run:
          name: Test documentation
          command: mustmatch test docs/

workflows:
  test:
    jobs:
      - test-docs
```

## Advanced Patterns

### Fail Fast on Documentation

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  # Documentation tests run first and fail fast
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test -x docs/  # -x = fail fast

  # Unit tests only run if docs pass
  unit-tests:
    needs: docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/

  # Integration tests require both
  integration:
    needs: [docs, unit-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/integration/
```

### Matrix Testing

Test docs against multiple versions:

```yaml
# .github/workflows/docs-matrix.yml
name: Test Docs

on: [push, pull_request]

jobs:
  test-docs:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install mustmatch
      - run: mustmatch test docs/
```

### Conditional Documentation Tests

Only test changed docs:

```yaml
# .github/workflows/docs-on-change.yml
name: Test Changed Docs

on: pull_request

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v4

      - name: Get changed markdown files
        id: changed-files
        run: |
          FILES=$(git diff --name-only origin/main...HEAD | grep '\.md$' || true)
          echo "files=$FILES" >> $GITHUB_OUTPUT

      - name: Install mustmatch
        if: steps.changed-files.outputs.files != ''
        run: pip install mustmatch

      - name: Test changed docs
        if: steps.changed-files.outputs.files != ''
        run: |
          for file in ${{ steps.changed-files.outputs.files }}; do
            echo "Testing $file"
            mustmatch test "$file"
          done
```

### Documentation Coverage

Track which docs have tests:

```yaml
# .github/workflows/docs-coverage.yml
name: Documentation Coverage

on: [push]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Test docs with verbose output
        run: mustmatch test -v docs/ 2>&1 | tee test-output.txt

      - name: Calculate coverage
        run: |
          TOTAL_BLOCKS=$(grep -c '```' docs/**/*.md || echo 0)
          TESTED_BLOCKS=$(grep -c 'PASS' test-output.txt || echo 0)
          echo "Tested $TESTED_BLOCKS of $TOTAL_BLOCKS code blocks"

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const output = fs.readFileSync('test-output.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Documentation Test Results\n\n```\n' + output + '\n```'
            });
```

### Language-Specific Testing

Test different languages separately:

```yaml
# .github/workflows/docs-by-lang.yml
name: Test Documentation by Language

on: [push, pull_request]

jobs:
  test-bash:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test --lang bash docs/

  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test --lang python docs/
```

## Service Dependencies

### With Docker Compose

Test docs that require services:

```yaml
# .github/workflows/docs-with-services.yml
name: Test Docs with Services

on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'

      - uses: actions/setup-python@v4

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Test API documentation
        run: mustmatch test docs/api/

      - name: Stop services
        if: always()
        run: docker-compose down
```

### With Service Containers

```yaml
# .github/workflows/docs-with-postgres.yml
name: Test Docs with Database

on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Test database documentation
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        run: mustmatch test docs/database/
```

## Pre-commit Hooks

Test docs before committing:

```bash skip
# .git/hooks/pre-commit
#!/bin/bash

echo "Testing documentation..."

# Find staged markdown files
STAGED_MD=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$')

if [ -n "$STAGED_MD" ]; then
    # Test staged docs
    for file in $STAGED_MD; do
        echo "Testing $file"
        mustmatch test "$file" || {
            echo "❌ Documentation tests failed"
            echo "Fix the examples or skip with: git commit --no-verify"
            exit 1
        }
    done
    echo "✓ Documentation tests passed"
fi
```

Install the hook:

```bash skip
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
STAGED_MD=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$')
if [ -n "$STAGED_MD" ]; then
    for file in $STAGED_MD; do
        mustmatch test "$file" || exit 1
    done
fi
EOF

chmod +x .git/hooks/pre-commit
```

## Pull Request Checks

### Require Passing Docs

```yaml
# .github/workflows/pr-check.yml
name: PR Checks

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test docs/

      - name: Block merge if failed
        if: failure()
        run: |
          echo "Documentation tests must pass before merging"
          exit 1
```

### Add Status Check

Configure branch protection rules:
1. Go to repository Settings → Branches
2. Add branch protection rule for `main`
3. Require status checks: `test-docs`
4. Now PRs can't merge until docs pass

## Release Workflows

### Pre-release Verification

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  verify-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch

      - name: Test all documentation
        run: mustmatch test -v .

      - name: Fail release if docs fail
        if: failure()
        run: |
          echo "Cannot release with failing documentation"
          exit 1

  publish:
    needs: verify-docs
    runs-on: ubuntu-latest
    steps:
      - name: Build and publish
        run: ./scripts/publish.sh
```

### Post-release Verification

```yaml
# .github/workflows/post-release.yml
name: Verify Release

on:
  release:
    types: [published]

jobs:
  verify-published:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install released version
        run: pip install mypackage==${{ github.event.release.tag_name }}

      - name: Test docs against release
        run: mustmatch test docs/

      - name: Notify on failure
        if: failure()
        run: |
          echo "Released version doesn't match documentation!"
          # Send alert to Slack/email/etc
```

## Scheduled Testing

Test docs nightly to catch external dependencies:

```yaml
# .github/workflows/nightly-docs.yml
name: Nightly Documentation Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch
      - run: mustmatch test docs/

      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Nightly docs test failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Caching

Speed up CI with caching:

```yaml
# .github/workflows/docs-cached.yml
name: Test Docs (Cached)

on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Cache mustmatch
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-mustmatch-${{ hashFiles('**/requirements.txt') }}

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Test documentation
        run: mustmatch test docs/
```

## Reporting

### Upload Test Results

```yaml
# .github/workflows/docs-report.yml
name: Test Docs with Report

on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mustmatch

      - name: Test docs
        run: mustmatch test -v docs/ 2>&1 | tee test-results.txt
        continue-on-error: true

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.txt

      - name: Fail if tests failed
        run: grep -q "0 failed" test-results.txt
```

## Summary

Key CI integration patterns:

1. **Fail fast**: Test docs before unit tests
2. **Matrix testing**: Test across platforms/versions
3. **Service dependencies**: Use Docker Compose or service containers
4. **Pre-commit hooks**: Catch issues before pushing
5. **Branch protection**: Require passing docs to merge
6. **Release verification**: Block releases with failing docs
7. **Scheduled tests**: Catch external dependency changes
8. **Caching**: Speed up repeated runs

Result: Documentation becomes a first-class quality gate in your CI/CD pipeline.
