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
        body = _improve_tables(result.value) if result.value else "<p><em>(empty document)</em></p>"

        title = _first_heading_text(body) or stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(
            html,
            title=title,
            metadata={"mammoth_messages": [str(m) for m in result.messages]},
        )


def _improve_tables(body: str) -> str:
    """Make mammoth's bare tables render well.

    Mammoth emits ``<table><tr><td>…`` with no header row and wraps each cell's
    content in a ``<p>``. We promote the first row to a ``<thead>`` of ``<th>``
    cells and unwrap lone cell paragraphs so the default stylesheet can render a
    clean, readable table.
    """
    if "<table" not in body:
        return body
    try:
        from bs4 import BeautifulSoup
    except ImportError:  # pragma: no cover - bs4 is a core dependency
        return body

    soup = BeautifulSoup(body, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if rows and not table.find("th") and not table.find("thead"):
            header = rows[0]
            for cell in header.find_all("td"):
                cell.name = "th"
            header.extract()
            thead = soup.new_tag("thead")
            thead.append(header)
            table.insert(0, thead)
        # Unwrap a cell's single <p> so cells aren't artificially tall.
        for cell in table.find_all(["td", "th"]):
            paragraphs = cell.find_all("p", recursive=False)
            if len(paragraphs) == 1 and not paragraphs[0].find(["p", "ul", "ol", "table"]):
                paragraphs[0].unwrap()
    return str(soup)


def _first_heading_text(html_body: str) -> str | None:
    """Cheap, dependency-free extraction of the first heading's text."""
    import re

    match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html_body, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return text or None
