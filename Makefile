# Suppress directory messages
MAKEFLAGS += --no-print-directory

.PHONY: check build test coverage clean help publish

check:
	@echo "Running checks..."
	@uv sync --extra dev
	@uv run ruff check --select I --fix src
	@uv run ruff check src
	@echo "✓ Checks passed"

build:
	@echo "Building mustmatch..."
	@uv sync --extra dev
	@uv build
	@echo "✓ Build complete"

test:
	@echo "Running tests..."
	@uv sync --extra dev
	@uv run pytest docs/ README.md -q
	@echo "✓ Tests passed"

coverage:
	@echo "Running coverage..."
	@uv sync --extra dev
	@rm -f .coverage .coverage.* docs/.coverage docs/.coverage.*
	@COVERAGE_PROCESS_START="$(shell pwd)/.coveragerc" COVERAGE_FILE="$(shell pwd)/.coverage" uv run coverage run -m pytest docs/ README.md -q
	@uv run coverage combine --quiet . docs
	@uv run coverage report
	@uv run coverage html
	@uv run coverage xml
	@echo "✓ Coverage: htmlcov/index.html"

clean:
	@rm -rf build dist *.egg-info
	@rm -rf .coverage .coverage.* docs/.coverage docs/.coverage.* htmlcov coverage.xml
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

help:
	@echo "mustmatch - CLI output assertion tool"
	@echo ""
	@echo "Targets:"
	@echo "  check      Linting and code checks"
	@echo "  build      Build package"
	@echo "  test       Run all tests"
	@echo "  coverage   Generate coverage report"
	@echo "  clean      Remove build artifacts"
	@echo "  publish    Build and publish to PyPI"

publish: test
	@echo "Publishing to PyPI..."
	@uv build
	@uvx twine upload dist/*
	@echo "✓ Published to PyPI"
