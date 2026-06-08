"""PDF -> HTML via pdfminer.six (requires the ``pdf`` extra).

PDFs describe positioned glyphs rather than semantic structure, so we recover
readable prose: text blocks become paragraphs and each page becomes a section.
This keeps the output clean and model-friendly without pretending to reconstruct
the original layout pixel-for-pixel.
"""

from __future__ import annotations

from typing import Any, BinaryIO, cast

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["PdfConverter"]


class PdfConverter(DocumentConverter):
    """Convert a PDF document into readable, paragraph-structured HTML."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        if ext == ".pdf" or mimetype == "application/pdf":
            return True
        pos = file_stream.tell()
        head = file_stream.read(5)
        file_stream.seek(pos)
        return head == b"%PDF-"

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTTextContainer
        except ImportError as exc:
            raise MissingDependencyException(
                "PDF support requires the 'pdf' extra. "
                "Install it with: pip install everythingtohtml[pdf]"
            ) from exc

        sections: list[str] = []
        # pdfminer types its parameter narrowly; the engine guarantees a seekable
        # binary stream here, which is exactly what extract_pages consumes.
        pages = extract_pages(cast(Any, file_stream))
        for page_number, page_layout in enumerate(pages, start=1):
            paragraphs: list[str] = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if not text:
                        continue
                    # PDF text containers wrap mid-sentence; collapse soft breaks.
                    collapsed = " ".join(line.strip() for line in text.splitlines())
                    paragraphs.append(f"<p>{escape_text(collapsed)}</p>")
            body = "".join(paragraphs) or "<p><em>(no extractable text)</em></p>"
            sections.append(
                f'<section class="page" id="page-{page_number}">'
                f'<p class="page-number">Page {page_number}</p>{body}</section>'
            )

        if not sections:
            sections.append("<p><em>(empty document)</em></p>")

        title = stream_info.filename
        html = wrap_document("\n".join(sections), title=title)
        return DocumentConverterResult(html, title=title)
