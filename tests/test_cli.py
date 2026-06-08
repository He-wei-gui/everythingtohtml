"""Tests for the command-line interface."""

from __future__ import annotations

from pathlib import Path

from everythingtohtml.__main__ import main


def test_cli_file_to_stdout(write_file, capsysbinary, monkeypatch) -> None:
    path: Path = write_file("doc.md", "# CLI Title\n")
    exit_code = main([str(path)])
    assert exit_code == 0
    out = capsysbinary.readouterr().out.decode("utf-8")
    assert "<h1>CLI Title</h1>" in out


def test_cli_file_to_output_file(write_file, tmp_path: Path) -> None:
    path: Path = write_file("data.csv", "a,b\n1,2\n")
    out_path = tmp_path / "out.html"
    exit_code = main([str(path), "-o", str(out_path)])
    assert exit_code == 0
    html = out_path.read_text(encoding="utf-8")
    assert "<th>a</th>" in html


def test_cli_unsupported_returns_error(monkeypatch) -> None:
    exit_code = main(["ftp://example.com/file.txt"])
    assert exit_code == 1


def test_cli_stdin(write_file, monkeypatch, capsysbinary) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b"# Piped\n")))
    exit_code = main(["--extension", ".md"])
    assert exit_code == 0
    out = capsysbinary.readouterr().out.decode("utf-8")
    assert "Piped" in out
