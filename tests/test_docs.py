"""Run documentation tests using mktestdocs.

This replaces unit tests with self-hosted documentation tests.
The tool tests itself through executable markdown examples.
"""

from pathlib import Path

import pytest
from mktestdocs import check_md_file

DOCS_DIR = Path(__file__).parent.parent / "docs" / "tests"


def get_test_files():
    """Get all markdown test files."""
    if DOCS_DIR.exists():
        return list(DOCS_DIR.glob("*.md"))
    return []


@pytest.mark.parametrize(
    "md_file",
    get_test_files(),
    ids=lambda p: p.stem,
)
def test_docs(md_file):
    """Test each documentation file."""
    check_md_file(fpath=md_file)
