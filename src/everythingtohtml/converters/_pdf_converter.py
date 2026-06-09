"""PDF -> HTML via pdfminer.six (requires the ``pdf`` extra).

PDFs describe positioned glyphs rather than semantic structure, so we recover
readable prose: text blocks become paragraphs and each page becomes a section.
This keeps the output clean and model-friendly without pretending to reconstruct
the original layout pixel-for-pixel.
"""

from __future__ import annotations

import base64
from typing import Any, BinaryIO, cast

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import escape_attr, escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["PdfConverter"]

_PDF_STYLE = """
.page img.pdf-image { max-width: 100%; height: auto; display: block; margin: 0.5rem 0; }
"""


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

            if paragraphs:
                body = "".join(paragraphs)
            else:
                # Scanned / image-only page: show the embedded images instead of an
                # unhelpful "no text" note.
                images = _render_page_images(page_layout)
                body = images or "<p><em>(no extractable text)</em></p>"

            sections.append(
                f'<section class="page" id="page-{page_number}">'
                f'<p class="page-number">Page {page_number}</p>{body}</section>'
            )

        if not sections:
            sections.append("<p><em>(empty document)</em></p>")

        title = stream_info.filename
        html = wrap_document(
            "\n".join(sections), title=title, extra_head=f"<style>{_PDF_STYLE}</style>\n"
        )
        return DocumentConverterResult(html, title=title)


def _iter_images(container: Any) -> Any:
    """Yield every LTImage in a layout tree (descending into LTFigure groups)."""
    from pdfminer.layout import LTFigure, LTImage

    for element in container:
        if isinstance(element, LTImage):
            yield element
        elif isinstance(element, LTFigure):
            yield from _iter_images(element)


def _render_page_images(page_layout: Any) -> str:
    parts: list[str] = []
    for index, lt_image in enumerate(_iter_images(page_layout)):
        data_uri = _image_data_uri(lt_image)
        if data_uri:
            parts.append(
                f'<img class="pdf-image" alt="page image {index + 1}" '
                f'src="{escape_attr(data_uri)}">'
            )
    return "".join(parts)


def _filter_names(stream: Any) -> list[str]:
    filt = stream.attrs.get("Filter")
    if filt is None:
        return []
    if not isinstance(filt, list):
        filt = [filt]
    return [getattr(f, "name", None) or str(f) for f in filt]


def _image_data_uri(lt_image: Any) -> str | None:
    """Best-effort conversion of an LTImage to an embeddable data URI."""
    stream = getattr(lt_image, "stream", None)
    if stream is None:
        return None

    names = _filter_names(stream)
    try:
        rawdata = stream.get_rawdata()
    except Exception:
        rawdata = None

    # JPEG and JPEG2000 are stored verbatim and embed directly.
    if rawdata and any("DCTDecode" in n for n in names):
        return "data:image/jpeg;base64," + base64.b64encode(rawdata).decode("ascii")
    if rawdata and any("JPXDecode" in n for n in names):
        return "data:image/jp2;base64," + base64.b64encode(rawdata).decode("ascii")

    # Everything else: reconstruct a PNG with Pillow if it is available.
    return _pillow_png_data_uri(lt_image)


def _pillow_png_data_uri(lt_image: Any) -> str | None:
    try:
        import io

        from PIL import Image
    except Exception:
        return None

    stream = lt_image.stream
    try:
        data = stream.get_data()
    except Exception:
        return None

    width, height = lt_image.srcsize
    bits = getattr(lt_image, "bits", 8) or 8
    components = _color_components(getattr(lt_image, "colorspace", None))
    if bits == 1:
        mode = "1"
    else:
        mode = {1: "L", 3: "RGB", 4: "CMYK"}.get(components or 0, "")
    if not mode:
        return None

    try:
        image = Image.frombytes(mode, (width, height), data)
    except Exception:
        return None
    if mode == "CMYK":
        image = image.convert("RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _color_components(colorspace: Any) -> int | None:
    """Number of colour components implied by an LTImage colorspace value."""
    name = ""
    if isinstance(colorspace, list) and colorspace:
        first = colorspace[0]
        name = getattr(first, "name", None) or str(first)
    else:
        name = getattr(colorspace, "name", None) or str(colorspace)
    name = name.lower()
    if "rgb" in name:
        return 3
    if "cmyk" in name:
        return 4
    if "gray" in name or "g" == name:
        return 1
    return None
