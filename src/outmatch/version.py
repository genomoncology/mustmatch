"""Version information for outmatch.

The version is read from package metadata (pyproject.toml) at runtime,
making pyproject.toml the single source of truth for the version number.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("outmatch")
except PackageNotFoundError:
    # Package not installed (e.g., running from source without install)
    __version__ = "0.0.0.dev"
