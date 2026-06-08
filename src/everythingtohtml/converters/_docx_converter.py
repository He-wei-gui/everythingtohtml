"""DOCX -> HTML via mammoth (requires the ``docx`` extra).

Mammoth maps Word's semantic styles (headings, lists, tables, bold/italic) to
clean HTML rather than trying to reproduce pixel-perfect layout, which is exactly
what we want for readable, restyleable output.
"""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import wrap_document
from .._stream_info import StreamInfo

__all__ = ["DocxConverter"]

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class DocxConverter(DocumentConverter):
    """Convert Microsoft Word ``.docx`` documents to semantic HTML."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return ext == ".docx" or mimetype == _DOCX_MIME

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        try:
            import mammoth
        except ImportError as exc:
            raise MissingDependencyException(
                "DOCX support requires the 'docx' extra. "
                "Install it with: pip install everythingtohtml[docx]"
            ) from exc

        result = mammoth.convert_to_html(file_stream)
        body = result.value or "<p><em>(empty document)</em></p>"

        title = _first_heading_text(body) or stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(
            html,
            title=title,
            metadata={"mammoth_messages": [str(m) for m in result.messages]},
        )


def _first_heading_text(html_body: str) -> str | None:
    """Cheap, dependency-free extraction of the first heading's text."""
    import re

    match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html_body, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return text or None
