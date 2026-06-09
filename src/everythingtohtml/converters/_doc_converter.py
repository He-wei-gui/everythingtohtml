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
import unicodedata
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

    return _extract_text_from_worddocument(raw)


def _extract_text_from_worddocument(raw: bytes) -> str:
    """Extract and clean the main text span from a ``WordDocument`` stream."""
    fc_min = int.from_bytes(raw[0x18:0x1C], "little")
    fc_mac = int.from_bytes(raw[0x1C:0x20], "little")
    ccp_text = int.from_bytes(raw[0x4C:0x50], "little") if len(raw) >= 0x50 else 0
    if fc_min <= 0 or fc_min >= len(raw):
        fc_min = 0x800 if len(raw) > 0x800 else 0
    if fc_mac <= fc_min or fc_mac > len(raw):
        fc_mac = len(raw)

    span = raw[fc_min:fc_mac]
    candidates = []
    # 8-bit (cp1252) interpretation.
    eight = span[: min(ccp_text or len(span), len(span))]
    candidates.append(eight.decode("cp1252", errors="ignore"))
    candidates.append(eight.decode("gb18030", errors="ignore"))
    # 16-bit (UTF-16LE) interpretation.
    sixteen_len = min((ccp_text * 2) if ccp_text else len(span), len(span))
    candidates.append(span[:sixteen_len].decode("utf-16-le", errors="ignore"))

    best = max(candidates, key=_text_quality_score)
    return _clean_word_text(best)


def _printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\r\n\t ")
    return printable / len(text)


def _text_quality_score(text: str) -> float:
    """Prefer real prose over binary decoded into printable-looking glyphs."""
    if not text:
        return 0.0
    printable = _printable_ratio(text)
    suspicious = sum(1 for ch in text if _is_suspicious_glyph(ch))
    return printable - (suspicious / len(text))


def _clean_word_text(text: str) -> str:
    text = _trim_garbage_tail(text)
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


def _trim_garbage_tail(text: str) -> str:
    """Drop long decoded-binary tails without touching ordinary prose."""
    run_start: int | None = None
    run_length = 0
    meaningful = 0
    for index, ch in enumerate(text):
        if ch.isspace() or ord(ch) < 0x20:
            run_start = None
            run_length = 0
            continue
        if _is_suspicious_glyph(ch):
            if run_start is None:
                run_start = index
                run_length = 0
            run_length += 1
            if meaningful >= 20 and run_length >= 12:
                return text[:run_start]
        else:
            meaningful += 1
            run_start = None
            run_length = 0
    return text


def _is_suspicious_glyph(ch: str) -> bool:
    code = ord(ch)
    if ch in "\r\n\t ":
        return False
    if code < 0x20:
        return True
    if 0x20 <= code <= 0x007E:
        return False
    if 0x00A0 <= code <= 0x024F:  # Latin supplement/extended.
        return False
    if 0x2000 <= code <= 0x206F:  # General punctuation.
        return False
    if 0x3000 <= code <= 0x30FF:  # CJK punctuation + Japanese kana.
        return False
    if 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF:
        return False
    if 0xFF00 <= code <= 0xFFEF:  # Fullwidth forms.
        return False
    category = unicodedata.category(ch)
    return category.startswith("C") or category.startswith("M") or code > 0x02AF
