"""JSON -> HTML, rendered as a collapsible, syntax-highlighted tree."""

from __future__ import annotations

import json
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["JsonConverter"]

_ACCEPTED_EXTENSIONS = {".json", ".jsonl", ".ndjson"}
_ACCEPTED_MIME_TYPES = {"application/json", "application/x-ndjson"}


class JsonConverter(DocumentConverter):
    """Render JSON as nested ``<details>`` elements so large blobs stay navigable.

    Supports both plain JSON and line-delimited JSON (``.jsonl`` / ``.ndjson``).
    """

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
        text = read_text(file_stream, stream_info)
        ext = stream_info.normalized_extension()

        if ext in (".jsonl", ".ndjson"):
            data: Any = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            data = json.loads(text)

        body = f'<div class="json-tree">{_render(data)}</div>'
        title = stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)


def _render(value: Any) -> str:
    """Recursively render a decoded JSON value to HTML."""
    if isinstance(value, dict):
        if not value:
            return '<span class="json-empty">{}</span>'
        items = "".join(
            f'<li><span class="json-key">{escape_text(str(k))}</span>: {_render(v)}</li>'
            for k, v in value.items()
        )
        return f"<details open><summary>object ({len(value)})</summary><ul>{items}</ul></details>"
    if isinstance(value, list):
        if not value:
            return '<span class="json-empty">[]</span>'
        items = "".join(f"<li>{_render(v)}</li>" for v in value)
        return f"<details open><summary>array ({len(value)})</summary><ol>{items}</ol></details>"
    if isinstance(value, str):
        return f'<span class="json-string">"{escape_text(value)}"</span>'
    if isinstance(value, bool):
        return f'<span class="json-bool">{str(value).lower()}</span>'
    if value is None:
        return '<span class="json-null">null</span>'
    return f'<span class="json-number">{escape_text(str(value))}</span>'
