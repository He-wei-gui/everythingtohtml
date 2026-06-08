"""PPTX -> HTML, one ``<section>`` per slide (requires the ``pptx`` extra)."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["PptxConverter"]

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class PptxConverter(DocumentConverter):
    """Convert PowerPoint ``.pptx`` decks into a slide-per-section HTML document."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return ext == ".pptx" or mimetype == _PPTX_MIME

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        try:
            from pptx import Presentation
        except ImportError as exc:
            raise MissingDependencyException(
                "PPTX support requires the 'pptx' extra. "
                "Install it with: pip install everythingtohtml[pptx]"
            ) from exc

        presentation = Presentation(file_stream)
        parts: list[str] = []
        title: str | None = None

        for index, slide in enumerate(presentation.slides, start=1):
            parts.append(f'<section class="slide" id="slide-{index}">')
            parts.append(f'<p class="slide-number">Slide {index}</p>')
            for shape in slide.shapes:
                parts.append(_render_shape(shape))
                if title is None:
                    title = _shape_title(shape)
            parts.append("</section>")

        title = title or stream_info.filename
        html = wrap_document("\n".join(parts), title=title)
        return DocumentConverterResult(html, title=title)


def _render_shape(shape: Any) -> str:
    if getattr(shape, "has_table", False):
        return _render_table(shape.table)
    if not getattr(shape, "has_text_frame", False):
        return ""
    blocks: list[str] = []
    for paragraph in shape.text_frame.paragraphs:
        text = "".join(run.text for run in paragraph.runs).strip()
        if not text:
            continue
        if paragraph.level and paragraph.level > 0:
            blocks.append(f"<li>{escape_text(text)}</li>")
        else:
            blocks.append(f"<p>{escape_text(text)}</p>")
    return "".join(blocks)


def _render_table(table: Any) -> str:
    parts = ["<table>"]
    for r, row in enumerate(table.rows):
        parts.append("<tr>")
        cell_tag = "th" if r == 0 else "td"
        for cell in row.cells:
            parts.append(f"<{cell_tag}>{escape_text(cell.text)}</{cell_tag}>")
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def _shape_title(shape: Any) -> str | None:
    if getattr(shape, "has_text_frame", False):
        text = shape.text_frame.text.strip()
        if text:
            return text.splitlines()[0]
    return None
