"""reStructuredText -> HTML via docutils (requires the ``rst`` extra)."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["RstConverter"]

_ACCEPTED_EXTENSIONS = {".rst", ".rest"}
_ACCEPTED_MIME_TYPES = {"text/x-rst"}


class RstConverter(DocumentConverter):
    """Convert reStructuredText documents to HTML."""

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
        try:
            from docutils.core import publish_parts
        except ImportError as exc:
            raise MissingDependencyException(
                "RST support requires the 'rst' extra. "
                "Install it with: pip install everythingtohtml[rst]"
            ) from exc

        text = read_text(file_stream, stream_info)
        parts = publish_parts(
            source=text,
            writer_name="html5",
            settings_overrides={"report_level": 5, "halt_level": 5},
        )
        body = parts.get("html_body") or parts.get("fragment") or ""
        title = parts.get("title") or stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)
