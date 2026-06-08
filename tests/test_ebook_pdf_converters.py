"""Tests for the EPUB (built-in) and PDF (extra) converters."""

from __future__ import annotations

import io
import zipfile

import pytest

from everythingtohtml import EverythingToHtml, StreamInfo


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


_CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

_OPF = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>My Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c1"/>
    <itemref idref="c2"/>
  </spine>
</package>
"""

_CH1 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Ch1</title></head>
<body><h1>Chapter One</h1><p>First chapter text.</p><script>bad()</script></body></html>
"""

_CH2 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Ch2</title></head>
<body><h1>Chapter Two</h1><p>Second chapter text.</p></body></html>
"""


def _build_epub() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        # The EPUB spec requires the mimetype entry first and stored (uncompressed).
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", _CONTAINER)
        archive.writestr("OEBPS/content.opf", _OPF)
        archive.writestr("OEBPS/ch1.xhtml", _CH1)
        archive.writestr("OEBPS/ch2.xhtml", _CH2)
    return buffer.getvalue()


def test_epub_reading_order(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_epub(), stream_info=StreamInfo(extension=".epub"))
    assert result.title == "My Test Book"
    assert "Chapter One" in result.html
    assert "Chapter Two" in result.html
    # Spine order must be preserved.
    assert result.html.index("Chapter One") < result.html.index("Chapter Two")


def test_epub_strips_scripts(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_epub(), stream_info=StreamInfo(extension=".epub"))
    assert "bad()" not in result.html


def test_epub_detected_by_sniffing(eth: EverythingToHtml) -> None:
    # No extension hint: rely on the magic "mimetype" entry.
    result = eth.convert(_build_epub())
    assert "Chapter One" in result.html


def test_pdf(eth: EverythingToHtml) -> None:
    pytest.importorskip("pdfminer")
    fpdf = pytest.importorskip("fpdf")  # fpdf2, for building the fixture

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=14)
    try:
        pdf.cell(0, 10, text="Hello PDF World")
    except TypeError:  # older fpdf2 used the 'txt' keyword
        pdf.cell(0, 10, txt="Hello PDF World")
    data = bytes(pdf.output())

    result = eth.convert(data, stream_info=StreamInfo(extension=".pdf"))
    assert "Hello PDF World" in result.html
    assert 'class="page"' in result.html


def test_pdf_detected_by_magic_bytes(eth: EverythingToHtml) -> None:
    pytest.importorskip("pdfminer")
    fpdf = pytest.importorskip("fpdf")

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=14)
    try:
        pdf.cell(0, 10, text="Magic Sniff")
    except TypeError:
        pdf.cell(0, 10, txt="Magic Sniff")
    data = bytes(pdf.output())

    # No extension hint -> must be recognised by the %PDF- header.
    result = eth.convert(data)
    assert "Magic Sniff" in result.html
