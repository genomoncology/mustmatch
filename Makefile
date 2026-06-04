# Suppress directory messages
MAKEFLAGS += --no-print-directory

.PHONY: lint spec build smoke test clean help publish

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

smoke:
	@echo "Running installed-wheel smoke..."
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	if [ -n "$${SMOKE_WHEEL:-}" ]; then \
		wheel="$$SMOKE_WHEEL"; \
		if [ ! -f "$$wheel" ]; then \
			echo "SMOKE_WHEEL does not exist: $$wheel" >&2; \
			exit 1; \
		fi; \
	else \
		wheelhouse="$$tmp/wheelhouse"; \
		mkdir -p "$$wheelhouse"; \
		uv build --wheel --out-dir "$$wheelhouse"; \
		set -- "$$wheelhouse"/*.whl; \
		if [ "$$#" -ne 1 ] || [ ! -f "$$1" ]; then \
			echo "Expected exactly one built wheel in $$wheelhouse" >&2; \
			exit 1; \
		fi; \
		wheel="$$1"; \
	fi; \
	uv venv "$$tmp/venv" >/dev/null; \
	uv pip install --python "$$tmp/venv/bin/python" "$$wheel"; \
	PATH="$$tmp/venv/bin:$$PATH"; \
	export PATH; \
	resolved=$$(command -v mustmatch); \
	case "$$resolved" in "$$tmp/venv/bin/"*) ;; *) echo "installed mustmatch not first on PATH: $$resolved" >&2; exit 1;; esac; \
	mustmatch test tests/smoke/smoke.md
	@echo "✓ Smoke passed"

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
	@echo "  smoke      Build/install wheel and run package smoke"
	@echo "  test       Run Rust tests"
	@echo "  clean      Remove build artifacts"
	@echo "  publish    Build and publish to PyPI"

publish: test
	@echo "Publishing to PyPI..."
	@uv build
	@uvx twine upload dist/*
	@echo "✓ Published to PyPI"
