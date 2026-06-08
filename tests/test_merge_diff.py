"""Tests for multi-document merge and diff."""

from __future__ import annotations

from pathlib import Path

import pytest

from everythingtohtml import EverythingToHtml


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


def test_merge_stacked(eth: EverythingToHtml, write_file) -> None:
    a: Path = write_file("a.md", "# Alpha\n\nApple text.\n")
    b: Path = write_file("b.md", "# Beta\n\nBanana text.\n")
    result = eth.merge([str(a), str(b)])

    assert "Alpha" in result.html and "Beta" in result.html
    assert result.html.index("Alpha") < result.html.index("Beta")
    assert "Apple text." in result.html and "Banana text." in result.html
    assert '<nav class="merge-toc"' in result.html  # table of contents for >1 doc
    assert 'id="doc-1"' in result.html and 'id="doc-2"' in result.html


def test_merge_columns(eth: EverythingToHtml, write_file) -> None:
    a: Path = write_file("a.md", "# Left\n\nleft body\n")
    b: Path = write_file("b.md", "# Right\n\nright body\n")
    result = eth.merge([str(a), str(b)], layout="columns")
    assert "merge-columns" in result.html
    assert "merge-col" in result.html


def test_merge_custom_labels(eth: EverythingToHtml, write_file) -> None:
    a: Path = write_file("a.md", "# Ignored A\n")
    b: Path = write_file("b.md", "# Ignored B\n")
    result = eth.merge([str(a), str(b)], labels=["First Doc", "Second Doc"])
    assert "First Doc" in result.html and "Second Doc" in result.html


def test_merge_no_toc(eth: EverythingToHtml, write_file) -> None:
    a: Path = write_file("a.md", "# A\n")
    b: Path = write_file("b.md", "# B\n")
    result = eth.merge([str(a), str(b)], include_toc=False)
    assert '<nav class="merge-toc"' not in result.html


def test_merge_requires_sources(eth: EverythingToHtml) -> None:
    with pytest.raises(ValueError):
        eth.merge([])


def test_diff(eth: EverythingToHtml, write_file) -> None:
    old: Path = write_file("old.md", "# Spec\n\nLine one.\nLine two.\n")
    new: Path = write_file("new.md", "# Spec\n\nLine one.\nLine two changed.\n")
    result = eth.diff(str(old), str(new))

    assert result.title == "Document comparison"
    assert 'class="diff"' in result.html  # difflib's comparison table
    assert "diff-legend" in result.html
    # The changed line text should surface somewhere in the diff.
    assert "changed" in result.html


def test_diff_custom_labels(eth: EverythingToHtml, write_file) -> None:
    old: Path = write_file("old.md", "# X\n\nsame\n")
    new: Path = write_file("new.md", "# X\n\nsame\n")
    result = eth.diff(str(old), str(new), left_label="v1", right_label="v2")
    assert "v1" in result.html and "v2" in result.html
