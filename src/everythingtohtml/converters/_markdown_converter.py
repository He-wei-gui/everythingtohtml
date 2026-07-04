"""Markdown -> HTML using markdown-it-py (CommonMark + tables/strikethrough/math)."""

from __future__ import annotations

import re
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["MarkdownConverter"]

_ACCEPTED_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}
_ACCEPTED_MIME_TYPES = {"text/markdown", "text/x-markdown"}

# Pull the first ATX heading to use as the document <title>.
_FIRST_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)

# Loaded into <head> only when a document actually contains math, so plain
# documents stay dependency-free. MathJax renders the \( \) / \[ \] delimiters our
# render rules emit (and $$…$$ for good measure). The raw string keeps the doubled
# backslashes the JS config needs.
_MATHJAX_HEAD = r"""<style>.math-block{overflow-x:auto;margin:1rem 0;text-align:center;}</style>
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]'], ['$$', '$$']] },
  options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
"""


class MarkdownConverter(DocumentConverter):
    """Convert Markdown to HTML with GitHub-flavored niceties and LaTeX math."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return ext in _ACCEPTED_EXTENSIONS or mimetype in _ACCEPTED_MIME_TYPES

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from markdown_it import MarkdownIt

        text = read_text(file_stream, stream_info)

        md = (
            MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
            .enable("table")
            .enable("strikethrough")
        )
        has_math = _enable_math(md)

        body = md.render(text)

        match = _FIRST_HEADING.search(text)
        title = match.group(1).strip() if match else stream_info.filename
        extra_head = _MATHJAX_HEAD if (has_math and _document_has_math(body)) else ""
        html = wrap_document(body, title=title, extra_head=extra_head)
        return DocumentConverterResult(html, title=title)


def _enable_math(md: Any) -> bool:
    """Enable ``$…$`` / ``$$…$$`` math parsing; return False if the plugin is absent.

    The plugin protects LaTeX from Markdown (so ``_``, ``\\``, ``&`` survive), and
    our render rules emit MathJax-friendly ``\\(…\\)`` / ``\\[…\\]`` delimiters.
    """
    try:
        from markdown_it.common.utils import escapeHtml
        from mdit_py_plugins.dollarmath import dollarmath_plugin
    except ImportError:  # pragma: no cover - dollarmath ships with mdit-py-plugins
        return False

    md.use(dollarmath_plugin, double_inline=True)

    def render_inline(self: Any, tokens: Any, idx: int, options: Any, env: Any) -> str:
        return "\\(" + escapeHtml(tokens[idx].content) + "\\)"

    def render_block(self: Any, tokens: Any, idx: int, options: Any, env: Any) -> str:
        return '<div class="math-block">\\[' + escapeHtml(tokens[idx].content) + "\\]</div>\n"

    md.add_render_rule("math_inline", render_inline)
    md.add_render_rule("math_inline_double", render_block)
    md.add_render_rule("math_block", render_block)
    return True


def _document_has_math(body: str) -> bool:
    return "\\(" in body or "math-block" in body
