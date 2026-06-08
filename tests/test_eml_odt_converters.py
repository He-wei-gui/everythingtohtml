"""Tests for the email (.eml) and OpenDocument Text (.odt) converters."""

from __future__ import annotations

import io
import zipfile
from email.message import EmailMessage

import pytest

from everythingtohtml import EverythingToHtml, StreamInfo


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


# -- email ----------------------------------------------------------------


def _build_plain_email() -> bytes:
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.com"
    msg["Subject"] = "Project update"
    msg["Date"] = "Mon, 08 Jun 2026 10:00:00 +0000"
    msg.set_content("First paragraph.\n\nSecond paragraph.")
    return msg.as_bytes()


def _build_html_email_with_attachment() -> bytes:
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["Subject"] = "Rich message"
    msg.set_content("plain fallback")
    msg.add_alternative(
        "<html><body><h1>Hello</h1><script>evil()</script></body></html>",
        subtype="html",
    )
    msg.add_attachment(
        b"data", maintype="application", subtype="octet-stream", filename="report.bin"
    )
    return msg.as_bytes()


def test_eml_plain(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_plain_email(), stream_info=StreamInfo(extension=".eml"))
    assert result.title == "Project update"
    assert "alice@example.com" in result.html
    assert "bob@example.com" in result.html
    assert "First paragraph." in result.html
    assert "Second paragraph." in result.html
    assert "email-headers" in result.html


def test_eml_html_body_and_attachment(eth: EverythingToHtml) -> None:
    result = eth.convert(
        _build_html_email_with_attachment(), stream_info=StreamInfo(extension=".eml")
    )
    assert "<h1>Hello</h1>" in result.html
    assert "evil()" not in result.html  # script stripped
    assert "report.bin" in result.html
    assert "Attachments" in result.html


# -- ODT ------------------------------------------------------------------


_CONTENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">
  <office:body>
    <office:text>
      <text:h text:outline-level="1">Document Title</text:h>
      <text:p>A paragraph of body text.</text:p>
      <text:h text:outline-level="2">Subsection</text:h>
      <text:list>
        <text:list-item><text:p>First item</text:p></text:list-item>
        <text:list-item><text:p>Second item</text:p></text:list-item>
      </text:list>
      <table:table>
        <table:table-row>
          <table:table-cell><text:p>R1C1</text:p></table:table-cell>
          <table:table-cell><text:p>R1C2</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:text>
  </office:body>
</office:document-content>
"""

_META_XML = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
  <office:meta><dc:title>Meta Title</dc:title></office:meta>
</office:document-meta>
"""


def _build_odt() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.text",
            compress_type=zipfile.ZIP_STORED,
        )
        archive.writestr("content.xml", _CONTENT_XML)
        archive.writestr("meta.xml", _META_XML)
    return buffer.getvalue()


def test_odt_structure(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_odt(), stream_info=StreamInfo(extension=".odt"))
    assert "<h1>Document Title</h1>" in result.html
    assert "<h2>Subsection</h2>" in result.html
    assert "<p>A paragraph of body text.</p>" in result.html
    assert "<ul>" in result.html
    assert "First item" in result.html and "Second item" in result.html
    assert "<table>" in result.html
    assert "R1C1" in result.html and "R1C2" in result.html


def test_odt_meta_title(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_odt(), stream_info=StreamInfo(extension=".odt"))
    assert result.title == "Meta Title"


def test_odt_detected_by_sniffing(eth: EverythingToHtml) -> None:
    result = eth.convert(_build_odt())  # no extension hint
    assert "Document Title" in result.html
