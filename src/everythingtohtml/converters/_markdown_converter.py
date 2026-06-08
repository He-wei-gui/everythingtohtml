"""Markdown -> HTML using markdown-it-py (CommonMark + tables/strikethrough)."""

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


class MarkdownConverter(DocumentConverter):
    """Convert Markdown to HTML with GitHub-flavored niceties enabled."""

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
        body = md.render(text)

        match = _FIRST_HEADING.search(text)
        title = match.group(1).strip() if match else stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)
