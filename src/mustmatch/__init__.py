"""
mustmatch: CLI output assertion tool for documentation testing.

Public API:
    - CLI: `mustmatch` command (see cli.py)
    - pytest plugin: repo-local pytest config preloads `mustmatch.pytest_plugin`;
      installed consumers can also auto-load it via the `pytest11` entry point

All other functionality is internal.
"""

from .version import __version__

__all__ = ["__version__"]
