# Suppress directory messages
MAKEFLAGS += --no-print-directory

.PHONY: lint spec build test clean help publish

lint:
	@echo "Running lint..."
	@cargo fmt --check
	@cargo clippy -- -D warnings
	@echo "✓ Lint passed"

spec:
	@echo "Running specs..."
	@cargo build -q -p mustmatch-cli --bin mustmatch
	@PATH="$(CURDIR)/target/debug:$$PATH" ./target/debug/mustmatch test spec/ README.md
	@echo "✓ Specs passed"

build:
	@echo "Building mustmatch..."
	@uv build
	@echo "✓ Build complete"

test:
	@echo "Running tests..."
	@cargo test
	@echo "✓ Tests passed"

clean:
	@rm -rf build dist *.egg-info
	@rm -rf .coverage .coverage.* htmlcov coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

help:
	@echo "mustmatch - CLI output assertion tool"
	@echo ""
	@echo "Targets:"
	@echo "  lint       Run Rust lint gates"
	@echo "  spec       Run executable specs"
	@echo "  build      Build package"
	@echo "  test       Run Rust tests"
	@echo "  clean      Remove build artifacts"
	@echo "  publish    Build and publish to PyPI"

publish: test
	@echo "Publishing to PyPI..."
	@uv build
	@uvx twine upload dist/*
	@echo "✓ Published to PyPI"
