"""Pytest configuration for coverage in subprocesses."""

import os
import sys
from pathlib import Path


def pytest_configure(config):
    """Enable coverage for subprocesses."""
    # Import the module to ensure it's in coverage
    import outmatch  # noqa: F401

    # Find the project root (where pyproject.toml is)
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Set up coverage for subprocesses
    if pyproject_path.exists():
        os.environ["COVERAGE_PROCESS_START"] = str(pyproject_path)

        # Create sitecustomize.py in site-packages to auto-start coverage
        import site
        site_packages = site.getsitepackages()
        if site_packages:
            sc_path = Path(site_packages[0]) / "sitecustomize.py"
            sc_content = "import coverage; coverage.process_startup()\n"
            try:
                # Only write if different or missing
                needs_write = not sc_path.exists()
                if not needs_write:
                    needs_write = sc_path.read_text() != sc_content
                if needs_write:
                    sc_path.write_text(sc_content)
            except (OSError, PermissionError):
                # Can't write to site-packages, skip subprocess coverage
                pass

    # Ensure the package is importable in subprocesses
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
