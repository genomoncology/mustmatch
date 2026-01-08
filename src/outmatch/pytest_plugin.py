"""
Pytest plugin for outmatch markdown testing.

This module is automatically loaded by pytest via the entry point.
It makes MarkdownTest available for testing markdown documentation.
"""

from outmatch.pytest import MarkdownTest

__all__ = ["MarkdownTest"]

# The plugin doesn't add any hooks - users import MarkdownTest directly
# and use it with pytest.mark.parametrize. This entry point just ensures
# the plugin is discoverable and provides a namespace for future hooks.
