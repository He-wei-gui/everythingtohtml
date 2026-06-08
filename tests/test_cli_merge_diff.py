"""CLI tests for multi-source merge and diff."""

from __future__ import annotations

from pathlib import Path

import pytest

from everythingtohtml.__main__ import main


def test_cli_merge(write_file, tmp_path: Path) -> None:
    a = write_file("a.md", "# Alpha\n")
    b = write_file("b.md", "# Beta\n")
    out = tmp_path / "merged.html"
    assert main([str(a), str(b), "-o", str(out)]) == 0
    html = out.read_text(encoding="utf-8")
    assert "Alpha" in html and "Beta" in html
    assert '<nav class="merge-toc"' in html


def test_cli_merge_columns(write_file, tmp_path: Path) -> None:
    a = write_file("a.md", "# Alpha\n")
    b = write_file("b.md", "# Beta\n")
    out = tmp_path / "cols.html"
    assert main([str(a), str(b), "--columns", "-o", str(out)]) == 0
    assert "merge-columns" in out.read_text(encoding="utf-8")


def test_cli_diff(write_file, tmp_path: Path) -> None:
    a = write_file("old.md", "# Doc\n\nsame\nold line\n")
    b = write_file("new.md", "# Doc\n\nsame\nnew line\n")
    out = tmp_path / "diff.html"
    assert main([str(a), str(b), "--diff", "-o", str(out)]) == 0
    assert 'class="diff"' in out.read_text(encoding="utf-8")


def test_cli_diff_wrong_count_errors(write_file) -> None:
    a = write_file("a.md", "# A\n")
    with pytest.raises(SystemExit):
        main([str(a), "--diff"])
