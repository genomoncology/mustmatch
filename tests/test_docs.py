"""Run documentation tests using outmatch's own MarkdownTest.

This dogfoods the pytest plugin - the tool tests itself through
executable markdown examples using its own infrastructure.
"""

from pathlib import Path

import pytest

from outmatch.pytest import MarkdownTest

DOCS_DIR = Path(__file__).parent.parent / "docs" / "tests"


def get_markdown_tests():
    """Discover all bash blocks in markdown test files."""
    return list(MarkdownTest.discover(DOCS_DIR))


@pytest.mark.parametrize(
    "test",
    get_markdown_tests(),
    ids=lambda t: f"{t.file.stem}:{t.line}",
)
def test_docs(test):
    """Execute each bash block from documentation."""
    test.run(cwd=Path.cwd())
