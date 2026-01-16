"""
mustmatch: CLI output assertion tool for documentation testing.

Public API:
    - CLI: `mustmatch` command (see cli.py)
    - pytest plugin: auto-loaded via entry point (see pytest_plugin.py)

All other functionality is internal.
"""

from .version import __version__

__all__ = ["__version__"]
