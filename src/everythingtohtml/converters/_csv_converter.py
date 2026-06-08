"""CSV/TSV -> HTML ``<table>`` using the stdlib csv module with dialect sniffing."""

from __future__ import annotations

import csv
import io
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["CsvConverter"]

_ACCEPTED_EXTENSIONS = {".csv", ".tsv"}
_ACCEPTED_MIME_TYPES = {"text/csv", "text/tab-separated-values", "application/csv"}


class CsvConverter(DocumentConverter):
    """Render delimited data as an HTML table, treating the first row as headers."""

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

        delimiter = "\t" if ext == ".tsv" else None
        if delimiter is None:
            try:
                dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","

        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = [row for row in reader]

        title = stream_info.filename
        if not rows:
            body = "<p><em>(empty file)</em></p>"
            return DocumentConverterResult(wrap_document(body, title=title), title=title)

        parts: list[str] = ["<table>"]
        header, *data_rows = rows
        parts.append("<thead><tr>")
        parts.extend(f"<th>{escape_text(cell)}</th>" for cell in header)
        parts.append("</tr></thead>")
        parts.append("<tbody>")
        for row in data_rows:
            parts.append("<tr>")
            parts.extend(f"<td>{escape_text(cell)}</td>" for cell in row)
            parts.append("</tr>")
        parts.append("</tbody></table>")

        html = wrap_document("".join(parts), title=title)
        return DocumentConverterResult(html, title=title)
