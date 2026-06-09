"""Tests for the legacy ``.doc`` converter.

Building a real binary ``.doc`` fixture requires Word or LibreOffice, so these
tests focus on detection, the pure-Python text-cleaning helpers, and the
error path for non-OLE input. Full conversion is exercised opportunistically only
when LibreOffice is available.
"""

from __future__ import annotations

import io

import pytest

from everythingtohtml import EverythingToHtml, FileConversionException, StreamInfo
from everythingtohtml.converters import DocConverter
from everythingtohtml.converters._doc_converter import (
    _clean_word_text,
    _extract_text_from_worddocument,
    _printable_ratio,
)


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


def test_doc_accepts_by_extension() -> None:
    converter = DocConverter()
    assert converter.accepts(io.BytesIO(b""), StreamInfo(extension=".doc"))
    assert converter.accepts(io.BytesIO(b""), StreamInfo(mimetype="application/msword"))


def test_doc_does_not_accept_docx() -> None:
    converter = DocConverter()
    assert not converter.accepts(io.BytesIO(b""), StreamInfo(extension=".docx"))


def test_doc_invalid_input_raises(eth: EverythingToHtml) -> None:
    # Binary, non-UTF-8 bytes with a .doc extension: DocConverter accepts then
    # fails (not OLE2), and because the bytes are not decodable text the plain-text
    # fallback declines too, so the engine surfaces a FileConversionException.
    garbage = b"\x89\xff\xfe not a real ole document \x00\x01\x02\x80\x81"
    with pytest.raises(FileConversionException):
        eth.convert(garbage, stream_info=StreamInfo(extension=".doc"))


def test_printable_ratio() -> None:
    assert _printable_ratio("hello world") == 1.0
    assert _printable_ratio("") == 0.0
    assert _printable_ratio("a\x00\x01b") == pytest.approx(0.5)


def test_clean_word_text_maps_control_chars() -> None:
    assert _clean_word_text("a\rb\x07c") == "a\nb\nc"
    assert _clean_word_text("keep\tthis") == "keep\tthis"
    # Stray control chars are dropped (no space inserted); blank-line runs collapse
    # to at most a single blank line.
    assert _clean_word_text("x\x01y\r\r\rz") == "xy\n\nz"


def test_doc_text_extraction_stops_at_fc_mac() -> None:
    text = "题目：《现代医养信息系统》课程论文；正文宋体四号"
    encoded = text.encode("utf-16-le")
    fc_min = 0x800
    fc_mac = fc_min + len(encoded)
    raw = bytearray(fc_mac + 80)
    raw[0x18:0x1C] = fc_min.to_bytes(4, "little")
    raw[0x1C:0x20] = fc_mac.to_bytes(4, "little")
    raw[0x4C:0x50] = len(text).to_bytes(4, "little")
    raw[fc_min:fc_mac] = encoded
    raw[fc_mac:] = "ࠀࠂࠈࠊࠌࠎࠐ틗웊웺뻊뫊꿺".encode("utf-16-le")

    extracted = _extract_text_from_worddocument(bytes(raw))

    assert text in extracted
    assert "꿺" not in extracted
