"""Coverage subprocess support.

When running `make coverage`, pytest executes many examples via subprocesses.
coverage.py only measures those subprocesses if coverage is started on process
startup. coverage does this when `COVERAGE_PROCESS_START` is set and
`coverage.process_startup()` is called at interpreter startup.
"""

from __future__ import annotations

import os


def _maybe_start_coverage() -> None:
    if not os.environ.get("COVERAGE_PROCESS_START"):
        return

    try:
        import coverage
    except Exception:
        return

    coverage.process_startup()


_maybe_start_coverage()

