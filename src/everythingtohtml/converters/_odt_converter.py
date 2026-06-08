"""OpenDocument Text (``.odt``) -> HTML.

ODT is a ZIP whose ``content.xml`` holds the document in the OpenDocument schema.
We map the common block elements — headings, paragraphs, lists, and tables — to
semantic HTML using only the core dependencies (``zipfile`` + ``defusedxml``), so
no optional extra is required.
"""

from __future__ import annotations

import zipfile
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["OdtConverter"]

_ODT_MIME = "application/vnd.oasis.opendocument.text"


class OdtConverter(DocumentConverter):
    """Convert OpenDocument Text documents to semantic HTML."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        if ext == ".odt" or mimetype == _ODT_MIME:
            return True
        pos = file_stream.tell()
        head = file_stream.read(80)
        file_stream.seek(pos)
        return head[:2] == b"PK" and b"mimetypeapplication/vnd.oasis.opendocument.text" in head

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from defusedxml.ElementTree import fromstring

        with zipfile.ZipFile(file_stream) as archive:
            content = fromstring(archive.read("content.xml"))
            title = _read_meta_title(archive, fromstring) or stream_info.filename

        text_root = _find_descendant(content, "text")
        body = _render_blocks(text_root) if text_root is not None else ""
        if not body.strip():
            body = "<p><em>(empty document)</em></p>"

        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _read_meta_title(archive: zipfile.ZipFile, fromstring: Any) -> str | None:
    try:
        meta = fromstring(archive.read("meta.xml"))
    except KeyError:
        return None
    for element in meta.iter():
        if _localname(element.tag) == "title" and element.text:
            return element.text.strip()
    return None


def _find_descendant(element: Any, name: str) -> Any:
    for descendant in element.iter():
        if _localname(descendant.tag) == name:
            return descendant
    return None


def _render_blocks(parent: Any) -> str:
    parts: list[str] = []
    for child in parent:
        parts.append(_render_block(child))
    return "".join(parts)


def _render_block(element: Any) -> str:
    name = _localname(element.tag)

    if name == "h":
        level = element.get(_outline_attr(element)) or "1"
        try:
            depth = min(max(int(level), 1), 6)
        except ValueError:
            depth = 1
        text = _text_of(element).strip()
        return f"<h{depth}>{escape_text(text)}</h{depth}>" if text else ""

    if name == "p":
        text = _text_of(element).strip()
        return f"<p>{escape_text(text)}</p>" if text else ""

    if name == "list":
        items = []
        for item in element:
            if _localname(item.tag) == "list-item":
                items.append(f"<li>{_render_blocks(item)}</li>")
        return f"<ul>{''.join(items)}</ul>" if items else ""

    if name == "table":
        return _render_table(element)

    # Unknown container (e.g. text:section) — descend into its block children.
    if len(element):
        return _render_blocks(element)
    return ""


def _render_table(table: Any) -> str:
    rows: list[str] = []
    for row in table.iter():
        if _localname(row.tag) != "table-row":
            continue
        cells = []
        for cell in row:
            if _localname(cell.tag) == "table-cell":
                cells.append(f"<td>{_render_blocks(cell) or escape_text(_text_of(cell))}</td>")
        if cells:
            rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table>{''.join(rows)}</table>" if rows else ""


def _outline_attr(element: Any) -> str:
    """Return the namespaced ``text:outline-level`` attribute key, if present."""
    for key in element.attrib:
        if _localname(key) == "outline-level":
            return key
    return "outline-level"


def _text_of(element: Any) -> str:
    """Concatenate the text content of an element, honouring ODF whitespace tags."""
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        name = _localname(child.tag)
        if name == "line-break":
            parts.append("\n")
        elif name == "tab":
            parts.append("\t")
        elif name == "s":  # one or more spaces
            count = 1
            for key, value in child.attrib.items():
                if _localname(key) == "c":
                    try:
                        count = int(value)
                    except ValueError:
                        count = 1
            parts.append(" " * count)
        else:
            parts.append(_text_of(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)
