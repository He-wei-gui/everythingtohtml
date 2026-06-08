"""Catch-all converter that renders any text as a ``<pre>`` block."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["PlainTextConverter"]

# Mimetypes we are happy to treat as plain text. Anything that decodes cleanly is
# also accepted at low priority so the engine always has a fallback.
_TEXTUAL_MIME_PREFIXES = ("text/",)
_TEXTUAL_MIME_TYPES = {
    "application/x-yaml",
    "application/json",
    "application/xml",
}


class PlainTextConverter(DocumentConverter):
    """Render arbitrary text content inside a preformatted block.

    Registered at generic priority so it acts as the final fallback after every
    specific converter has declined.
    """

    priority = DocumentConverter.PRIORITY_GENERIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        if mimetype.startswith(_TEXTUAL_MIME_PREFIXES) or mimetype in _TEXTUAL_MIME_TYPES:
            return True
        # As a true fallback, accept anything that decodes as UTF-8 text.
        pos = file_stream.tell()
        sample = file_stream.read(4096)
        file_stream.seek(pos)
        if not sample:
            return True
        try:
            sample.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        text = read_text(file_stream, stream_info)
        title = stream_info.filename
        body = f"<pre>{escape_text(text)}</pre>"
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)
