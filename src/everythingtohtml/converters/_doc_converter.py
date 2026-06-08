"""Legacy ``.doc`` (Word 97-2003 binary) -> HTML.

The old binary ``.doc`` format is an OLE2 compound file and is far harder to read
than ``.docx``. This converter therefore uses the best tool available:

1. **LibreOffice** (``soffice``/``libreoffice`` on ``PATH``) — high-fidelity
   conversion to HTML. This is the recommended path; install LibreOffice for the
   best results.
2. **Pure-Python fallback** via ``olefile`` — a best-effort text extraction from
   the ``WordDocument`` stream. It recovers the prose but not rich formatting, and
   is clearly labelled as such in the output.

Requires the ``doc`` extra (``pip install everythingtohtml[doc]``) for the
fallback; LibreOffice, if present, is detected automatically.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["DocConverter"]

# Legacy .doc shares the OLE2 magic signature with .xls/.ppt, so we accept it
# only by extension/mimetype, never by magic bytes alone.
_DOC_MIME = "application/msword"
_SOFFICE_CANDIDATES = ("soffice", "libreoffice")


class DocConverter(DocumentConverter):
    """Convert legacy ``.doc`` files, preferring LibreOffice when available."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return ext == ".doc" or mimetype == _DOC_MIME

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        data = file_stream.read()

        soffice = _find_soffice()
        if soffice:
            body = _convert_with_libreoffice(soffice, data)
            if body is not None:
                title = stream_info.filename
                return DocumentConverterResult(
                    wrap_document(body, title=title),
                    title=title,
                    metadata={"engine": "libreoffice"},
                )

        # Fall back to a pure-Python best-effort extraction.
        return self._convert_with_olefile(data, stream_info)

    def _convert_with_olefile(
        self, data: bytes, stream_info: StreamInfo
    ) -> DocumentConverterResult:
        try:
            import olefile
        except ImportError as exc:
            raise MissingDependencyException(
                "Legacy .doc support requires the 'doc' extra "
                "(pip install everythingtohtml[doc]), and LibreOffice is "
                "recommended for full-fidelity conversion."
            ) from exc

        import io

        if not olefile.isOleFile(io.BytesIO(data)):
            raise ValueError("Not a valid OLE2 (.doc) document.")

        text = _extract_doc_text(io.BytesIO(data), olefile)
        paragraphs = [f"<p>{escape_text(block)}</p>" for block in text.split("\n") if block.strip()]
        note = (
            '<p class="conversion-note"><em>Extracted with the pure-Python '
            "fallback; install LibreOffice for full-fidelity .doc conversion."
            "</em></p>"
        )
        body = note + ("".join(paragraphs) or "<p><em>(no extractable text)</em></p>")
        title = stream_info.filename
        return DocumentConverterResult(
            wrap_document(body, title=title),
            title=title,
            metadata={"engine": "olefile-fallback"},
        )


def _find_soffice() -> str | None:
    for candidate in _SOFFICE_CANDIDATES:
        path = shutil.which(candidate)
        if path:
            return path
    return None


def _convert_with_libreoffice(soffice: str, data: bytes) -> str | None:
    """Convert .doc bytes to an HTML body fragment via headless LibreOffice."""
    from bs4 import BeautifulSoup

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "input.doc")
        with open(src, "wb") as handle:
            handle.write(data)
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "html", "--outdir", tmp, src],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except (subprocess.SubprocessError, OSError):
            return None

        out = os.path.join(tmp, "input.html")
        if not os.path.exists(out):
            return None
        with open(out, "rb") as handle:
            soup = BeautifulSoup(handle.read(), "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body_tag = soup.body
    return body_tag.decode_contents() if body_tag else soup.decode_contents()


def _extract_doc_text(stream: BinaryIO, olefile: Any) -> str:
    """Best-effort plain-text extraction from a Word ``WordDocument`` stream.

    Reads the FIB to locate the main text span, then decodes it as either 8-bit
    (cp1252) or 16-bit (UTF-16LE) characters — whichever yields more printable
    content — and maps Word's control characters to whitespace/newlines.
    """
    ole = olefile.OleFileIO(stream)
    try:
        if not ole.exists("WordDocument"):
            return ""
        raw = ole.openstream("WordDocument").read()
    finally:
        ole.close()

    if len(raw) < 0x20:
        return ""

    fc_min = int.from_bytes(raw[0x18:0x1C], "little")
    ccp_text = int.from_bytes(raw[0x4C:0x50], "little") if len(raw) >= 0x50 else 0
    if fc_min <= 0 or fc_min >= len(raw):
        fc_min = 0x800 if len(raw) > 0x800 else 0

    span = raw[fc_min:]
    candidates = []
    # 8-bit (cp1252) interpretation.
    eight = span[: ccp_text or len(span)]
    candidates.append(eight.decode("cp1252", errors="ignore"))
    # 16-bit (UTF-16LE) interpretation.
    sixteen_len = (ccp_text * 2) if ccp_text else len(span)
    candidates.append(span[:sixteen_len].decode("utf-16-le", errors="ignore"))

    best = max(candidates, key=_printable_ratio)
    return _clean_word_text(best)


def _printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\r\n\t ")
    return printable / len(text)


def _clean_word_text(text: str) -> str:
    out_chars: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch in ("\r", "\x07", "\x0b", "\x0c"):  # paragraph/cell/line breaks
            out_chars.append("\n")
        elif ch == "\t" or ch == "\n":
            out_chars.append(ch)
        elif code < 0x20:  # drop other control characters
            continue
        elif code in (0xFEFF,):  # BOM / zero-width
            continue
        else:
            out_chars.append(ch)
    # Collapse runs of blank lines.
    lines = [line.rstrip() for line in "".join(out_chars).split("\n")]
    cleaned: list[str] = []
    for line in lines:
        if line or (cleaned and cleaned[-1]):
            cleaned.append(line)
    return "\n".join(cleaned).strip()
