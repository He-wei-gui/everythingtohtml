"""Combine and compare multiple converted documents in a single HTML page.

These helpers operate on the *output* of converters, so they work for any format
the library supports — merge a folder of Word docs, stack a PDF next to its
Markdown source, or diff two revisions of a spec.
"""

from __future__ import annotations

import difflib

from ._html_builder import escape_attr, escape_text, wrap_document

__all__ = ["body_fragment", "plain_text_lines", "build_merged_html", "build_diff_html"]


_MERGE_STYLE = """
.merge-toc { border: 1px solid #ddd; border-radius: 6px; padding: 0.5rem 1rem; margin-bottom: 2rem; }
.merge-toc ol { margin: 0.3rem 0; }
.merge-doc { margin-bottom: 3rem; padding-bottom: 2rem; border-bottom: 2px solid #eee; }
.merge-doc:last-child { border-bottom: none; }
.merge-doc > h2.merge-title { margin-top: 0; }
.merge-columns { display: flex; gap: 2rem; align-items: flex-start; }
.merge-columns .merge-col { flex: 1 1 0; min-width: 0; }
@media (max-width: 48rem) { .merge-columns { flex-direction: column; } }
"""

_DIFF_STYLE = """
table.diff { width: 100%; border-collapse: collapse; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.85rem; }
table.diff td { padding: 0 0.4rem; vertical-align: top; white-space: pre-wrap; word-break: break-word; }
.diff_header { color: #999; text-align: right; }
td.diff_header { padding-right: 0.6rem; }
.diff_next { background: #f3f3f3; }
.diff_add { background: #d6ffd6; }
.diff_chg { background: #fff5b1; }
.diff_sub { background: #ffd6d6; }
.diff-legend { font-size: 0.85rem; margin: 0.5rem 0 1rem; }
.diff-legend span { padding: 0.1rem 0.4rem; border-radius: 3px; margin-right: 0.5rem; }
@media (prefers-color-scheme: dark) {
  .diff_add { background: #14532d; } .diff_sub { background: #5b1a1a; }
  .diff_chg { background: #5c4d00; } .diff_next, .diff_header { color: #aaa; }
}
"""


def body_fragment(html: str) -> str:
    """Extract the inner ``<body>`` markup from a full HTML document."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    return body.decode_contents() if body else soup.decode_contents()


def plain_text_lines(html: str) -> list[str]:
    """Extract visible text from an HTML document as a list of lines."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def build_merged_html(
    items: list[tuple[str, str]],
    *,
    title: str | None = None,
    layout: str = "stacked",
    include_toc: bool = True,
) -> str:
    """Combine ``(label, body_fragment)`` pairs into one HTML document.

    ``layout="stacked"`` renders documents top-to-bottom with an optional table of
    contents; ``layout="columns"`` places them side by side for visual comparison.
    """
    doc_title = title or "Merged document"

    if layout == "columns":
        cols = "".join(
            f'<section class="merge-col"><h2 class="merge-title">{escape_text(label)}</h2>'
            f"{body}</section>"
            for label, body in items
        )
        body_html = f'<div class="merge-columns">{cols}</div>'
        return wrap_document(
            body_html,
            title=doc_title,
            extra_head=f"<style>{_MERGE_STYLE}</style>\n",
        )

    parts: list[str] = []
    if include_toc and len(items) > 1:
        links = "".join(
            f'<li><a href="#doc-{i}">{escape_text(label)}</a></li>'
            for i, (label, _) in enumerate(items, start=1)
        )
        parts.append(f'<nav class="merge-toc"><strong>Contents</strong><ol>{links}</ol></nav>')

    for i, (label, body) in enumerate(items, start=1):
        parts.append(
            f'<section class="merge-doc" id="doc-{i}">'
            f'<h2 class="merge-title">{escape_text(label)}</h2>{body}</section>'
        )

    return wrap_document(
        "\n".join(parts),
        title=doc_title,
        extra_head=f"<style>{_MERGE_STYLE}</style>\n",
    )


def build_diff_html(
    left_label: str,
    left_lines: list[str],
    right_label: str,
    right_lines: list[str],
    *,
    title: str | None = None,
    context: bool = True,
    numlines: int = 3,
) -> str:
    """Render a side-by-side line diff of two documents' text content."""
    differ = difflib.HtmlDiff(wrapcolumn=72)
    table = differ.make_table(
        left_lines,
        right_lines,
        fromdesc=escape_attr(left_label),
        todesc=escape_attr(right_label),
        context=context,
        numlines=numlines,
    )
    legend = (
        '<p class="diff-legend">'
        '<span class="diff_add">added</span>'
        '<span class="diff_chg">changed</span>'
        '<span class="diff_sub">removed</span></p>'
    )
    body = f"<h1>{escape_text(title or 'Document comparison')}</h1>{legend}{table}"
    return wrap_document(
        body,
        title=title or "Document comparison",
        extra_head=f"<style>{_DIFF_STYLE}</style>\n",
    )
