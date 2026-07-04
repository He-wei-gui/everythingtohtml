"""Tests for the dependency-light, built-in text converters."""

from __future__ import annotations

import pytest

from everythingtohtml import EverythingToHtml, StreamInfo


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


def _convert(eth: EverythingToHtml, data: str, ext: str):
    return eth.convert(data.encode("utf-8"), stream_info=StreamInfo(extension=ext))


def test_markdown_renders_structure(eth: EverythingToHtml) -> None:
    md = "# Title\n\nText with **bold** and a [link](https://example.com).\n"
    result = _convert(eth, md, ".md")
    assert result.html.startswith("<!DOCTYPE html>")
    assert "<h1>Title</h1>" in result.html
    assert "<strong>bold</strong>" in result.html
    assert '<a href="https://example.com">link</a>' in result.html
    assert result.title == "Title"


def test_markdown_table(eth: EverythingToHtml) -> None:
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    result = _convert(eth, md, ".md")
    assert "<table>" in result.html
    assert "<th>a</th>" in result.html
    assert "<td>1</td>" in result.html


def test_markdown_math(eth: EverythingToHtml) -> None:
    # Raw string keeps LaTeX backslashes exactly as written.
    md = (
        "# M\n\nInline $x^2 + y_i$ and a matrix:\n\n"
        "$$\n"
        r"A = \begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}"
        "\n$$\n"
    )
    result = _convert(eth, md, ".md")
    # MathJax is injected only when math is present, and renders our delimiters.
    assert "mathjax@3" in result.html
    assert '<div class="math-block">' in result.html
    assert r"\begin{bmatrix}" in result.html  # LaTeX (and its `\`) survive Markdown
    assert "1 &amp; 2" in result.html  # `&` column separators preserved, escaped
    assert r"\(x^2 + y_i\)" in result.html  # inline math; `_` not treated as emphasis


def test_markdown_multiline_matrix_math_survives(eth: EverythingToHtml) -> None:
    md = r"""
$$
\begin{pmatrix} 1 & 3 \\ 5 & 2 \\ 0 & 4 \end{pmatrix}_{3\times2}
\begin{pmatrix} 3 & 6 & 9 & 4 \\ 2 & 7 & 8 & 3 \end{pmatrix}_{2\times4}
=
\begin{pmatrix} 9 & \boxed{?} & 33 & 13 \\ 19 & 44 & 61 & 26 \\ 8 & 28 & 32 & \boxed{?} \end{pmatrix}_{3\times4}
$$
"""
    result = _convert(eth, md, ".md")

    assert '<div class="math-block">' in result.html
    assert (
        r"\begin{pmatrix} 1 &amp; 3 \\ 5 &amp; 2 \\ 0 &amp; 4 \end{pmatrix}_{3\times2}"
        in result.html
    )
    assert r"\boxed{?}" in result.html
    assert "<strong>{3\\times2}</strong>" not in result.html
    assert "<p>_{3\\times4}" not in result.html


def test_markdown_without_math_stays_lightweight(eth: EverythingToHtml) -> None:
    result = _convert(eth, "# Plain\n\nJust prose, no formulas.", ".md")
    assert "mathjax" not in result.html.lower()  # no CDN dependency for plain docs


def test_csv_to_table(eth: EverythingToHtml) -> None:
    result = _convert(eth, "name,age\nAlice,30\nBob,25\n", ".csv")
    assert "<thead>" in result.html
    assert "<th>name</th>" in result.html
    assert "<td>Alice</td>" in result.html
    assert result.html.count("<tr>") == 3  # header + 2 rows


def test_csv_escapes_html(eth: EverythingToHtml) -> None:
    result = _convert(eth, "col\n<script>\n", ".csv")
    assert "<script>" not in result.html
    assert "&lt;script&gt;" in result.html


def test_tsv_uses_tab_delimiter(eth: EverythingToHtml) -> None:
    result = _convert(eth, "a\tb\n1\t2\n", ".tsv")
    assert "<th>a</th>" in result.html
    assert "<th>b</th>" in result.html


def test_json_tree(eth: EverythingToHtml) -> None:
    result = _convert(eth, '{"name": "x", "values": [1, 2, true, null]}', ".json")
    assert "json-tree" in result.html
    assert "json-key" in result.html
    assert "json-null" in result.html
    assert '<span class="json-string">"x"</span>' in result.html


def test_jsonl(eth: EverythingToHtml) -> None:
    result = _convert(eth, '{"a": 1}\n{"a": 2}\n', ".jsonl")
    assert "array (2)" in result.html


def test_html_normalization_strips_scripts(eth: EverythingToHtml) -> None:
    html = "<html><head><title>Doc</title></head><body><h1>Hi</h1><script>alert(1)</script></body></html>"
    result = _convert(eth, html, ".html")
    assert "alert(1)" not in result.html
    assert "<h1>Hi</h1>" in result.html
    assert result.title == "Doc"


def test_plain_text_fallback(eth: EverythingToHtml) -> None:
    result = _convert(eth, "just some text < & >", ".txt")
    assert "<pre>" in result.html
    assert "&lt; &amp; &gt;" in result.html


def test_rss_feed(eth: EverythingToHtml) -> None:
    rss = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<title>My Feed</title><description>desc</description>"
        "<item><title>Post One</title><link>https://x.com/1</link>"
        "<description>Body</description></item></channel></rss>"
    )
    result = _convert(eth, rss, ".rss")
    assert result.title == "My Feed"
    assert "<article>" in result.html
    assert 'href="https://x.com/1"' in result.html
    assert "Post One" in result.html


def test_atom_feed(eth: EverythingToHtml) -> None:
    atom = (
        '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
        "<title>Atom Feed</title>"
        '<entry><title>Entry One</title><link href="https://x.com/a"/>'
        "<summary>Summary</summary></entry></feed>"
    )
    result = _convert(eth, atom, ".atom")
    assert result.title == "Atom Feed"
    assert "Entry One" in result.html
    assert 'href="https://x.com/a"' in result.html


def test_ipynb(eth: EverythingToHtml, sample_notebook: str) -> None:
    result = eth.convert(
        sample_notebook.encode("utf-8"), stream_info=StreamInfo(extension=".ipynb")
    )
    assert result.title == "My Notebook"
    assert "code-cell" in result.html
    assert "print(&#x27;hello&#x27;)" in result.html or "print('hello')" in result.html
    assert "hello" in result.html


def test_yaml(eth: EverythingToHtml) -> None:
    pytest.importorskip("yaml")
    result = _convert(eth, "name: test\nitems:\n  - a\n  - b\n", ".yaml")
    assert "json-tree" in result.html
    assert "name" in result.html
    assert "test" in result.html


def test_rst(eth: EverythingToHtml) -> None:
    pytest.importorskip("docutils")
    rst = "Title\n=====\n\nSome *emphasised* text.\n"
    result = _convert(eth, rst, ".rst")
    assert "<em>emphasised</em>" in result.html
    assert "Title" in result.html
