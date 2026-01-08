"""Pytest configuration for coverage in subprocesses."""

import os
import sys


def pytest_configure(config):
    """Enable coverage for subprocesses."""
    # Import the module to ensure it's in coverage
    import doctest_expect  # noqa: F401

    # Set up coverage for subprocesses
    if "COVERAGE_PROCESS_START" not in os.environ:
        # Create a .coveragerc-like config
        os.environ["COVERAGE_PROCESS_START"] = ""

    # Ensure the package is importable in subprocesses
    src_path = os.path.join(os.path.dirname(__file__), "..", "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
