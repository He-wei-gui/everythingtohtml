"""EPUB e-books -> HTML.

EPUB is a ZIP container of XHTML content documents described by an OPF package
file. We follow the spine reading order, concatenate each chapter's body, and
strip active content — all with the standard library plus the core dependencies
(``defusedxml`` for safe XML, ``beautifulsoup4`` for the XHTML bodies), so this
converter needs no optional extra.
"""

from __future__ import annotations

import posixpath
import zipfile
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import wrap_document
from .._stream_info import StreamInfo

__all__ = ["EpubConverter"]

_CONTAINER_PATH = "META-INF/container.xml"
_EPUB_MIME = "application/epub+zip"
_STRIP_TAGS = ("script", "style", "noscript", "iframe", "object", "embed")


class EpubConverter(DocumentConverter):
    """Convert an ``.epub`` e-book into a single readable HTML document."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        if ext == ".epub" or mimetype == _EPUB_MIME:
            return True
        # Sniff: a ZIP whose first stored entry is the EPUB "mimetype" file.
        pos = file_stream.tell()
        head = file_stream.read(64)
        file_stream.seek(pos)
        return head[:2] == b"PK" and b"mimetypeapplication/epub+zip" in head

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from bs4 import BeautifulSoup
        from defusedxml.ElementTree import fromstring

        with zipfile.ZipFile(file_stream) as archive:
            opf_path = _find_opf_path(archive, fromstring)
            opf_root = fromstring(archive.read(opf_path))
            opf_dir = posixpath.dirname(opf_path)

            title = _opf_title(opf_root) or stream_info.filename
            hrefs = _spine_hrefs(opf_root, opf_dir)

            sections: list[str] = []
            for href in hrefs:
                try:
                    raw = archive.read(href)
                except KeyError:
                    continue
                soup = BeautifulSoup(raw, "html.parser")
                for tag in soup(list(_STRIP_TAGS)):
                    tag.decompose()
                body_tag = soup.body
                body = body_tag.decode_contents() if body_tag else soup.decode_contents()
                sections.append(f'<section class="chapter">{body}</section>')

        if not sections:
            sections.append("<p><em>(no readable content found)</em></p>")

        html = wrap_document("\n".join(sections), title=title)
        return DocumentConverterResult(html, title=title)


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_opf_path(archive: zipfile.ZipFile, fromstring: Any) -> str:
    """Resolve the OPF package path via META-INF/container.xml."""
    container = fromstring(archive.read(_CONTAINER_PATH))
    for element in container.iter():
        if _localname(element.tag) == "rootfile":
            full_path = element.get("full-path")
            if full_path:
                return full_path
    raise ValueError("EPUB container.xml has no rootfile path")


def _opf_title(opf_root: Any) -> str | None:
    for element in opf_root.iter():
        if _localname(element.tag) == "title" and element.text:
            return element.text.strip()
    return None


def _spine_hrefs(opf_root: Any, opf_dir: str) -> list[str]:
    """Return content-document paths in spine (reading) order."""
    manifest: dict[str, str] = {}
    spine_order: list[str] = []

    for element in opf_root.iter():
        name = _localname(element.tag)
        if name == "item":
            item_id = element.get("id")
            href = element.get("href")
            if item_id and href:
                manifest[item_id] = href
        elif name == "itemref":
            idref = element.get("idref")
            if idref:
                spine_order.append(idref)

    hrefs: list[str] = []
    for idref in spine_order:
        href = manifest.get(idref)
        if not href:
            continue
        full = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
        hrefs.append(full)
    return hrefs
