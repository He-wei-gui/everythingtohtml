"""HTML -> clean, self-contained HTML.

Useful for normalizing scraped or fragment HTML into a standalone document:
strips scripts, lifts the title, and re-wraps the body with the default styles.
"""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["HtmlConverter"]

_ACCEPTED_EXTENSIONS = {".html", ".htm", ".xhtml"}
_ACCEPTED_MIME_TYPES = {"text/html", "application/xhtml+xml"}

# Tags that should never survive into the cleaned output.
_STRIP_TAGS = ("script", "style", "noscript", "iframe", "object", "embed")


class HtmlConverter(DocumentConverter):
    """Normalize arbitrary HTML into a clean standalone document."""

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
        *,
        keep_styles: bool = False,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from bs4 import BeautifulSoup

        text = read_text(file_stream, stream_info)
        soup = BeautifulSoup(text, "html.parser")

        strip = list(_STRIP_TAGS)
        if keep_styles:
            strip.remove("style")
        for tag in soup(strip):
            tag.decompose()

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else stream_info.filename

        body_tag = soup.body
        body = body_tag.decode_contents() if body_tag else soup.decode_contents()

        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)
