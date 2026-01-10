"""Pytest configuration for coverage in subprocesses."""

import os
import sys
from pathlib import Path


def pytest_configure(config):
    """Enable coverage for subprocesses.

    Uses COVERAGE_PROCESS_START and a local sitecustomize.py to enable
    coverage tracking in subprocesses without modifying system site-packages.
    """
    # Import the module to ensure it's in coverage
    import outmatch  # noqa: F401

    # Find the project root (where pyproject.toml is)
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    tests_dir = Path(__file__).parent

    # Set up coverage for subprocesses
    if pyproject_path.exists():
        os.environ["COVERAGE_PROCESS_START"] = str(pyproject_path)

        # Create a local sitecustomize.py in tests directory for subprocess
        # coverage. This avoids modifying system site-packages.
        sc_path = tests_dir / "sitecustomize.py"
        sc_content = "import coverage; coverage.process_startup()\n"
        try:
            # Only write if different or missing
            needs_write = not sc_path.exists()
            if not needs_write:
                needs_write = sc_path.read_text() != sc_content
            if needs_write:
                sc_path.write_text(sc_content)
        except OSError:
            # Can't write, skip subprocess coverage
            pass

        # Add tests directory to PYTHONPATH so subprocesses find sitecustomize
        pythonpath = os.environ.get("PYTHONPATH", "")
        tests_dir_str = str(tests_dir)
        if tests_dir_str not in pythonpath:
            if pythonpath:
                os.environ["PYTHONPATH"] = f"{tests_dir_str}:{pythonpath}"
            else:
                os.environ["PYTHONPATH"] = tests_dir_str

    # Ensure the package is importable in subprocesses
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Also add src to PYTHONPATH for subprocesses
    pythonpath = os.environ.get("PYTHONPATH", "")
    if src_path not in pythonpath:
        if pythonpath:
            os.environ["PYTHONPATH"] = f"{src_path}:{pythonpath}"
        else:
            os.environ["PYTHONPATH"] = src_path
