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
    _extract_text_via_piece_table,
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


def test_doc_piece_table_mixed_encoding() -> None:
    """The piece-table parser decodes each piece with its own encoding (16-bit
    UTF-16 for the Chinese run, 8-bit for the ASCII run) and produces no mojibake."""
    unicode_text = "题目：《现代医养信息系统》课程论文"
    ascii_text = "Summary ABC"
    u16 = unicode_text.encode("utf-16-le")
    a8 = ascii_text.encode("cp1252")

    offset_u = 0x500
    offset_c = 0x700
    word_doc = bytearray(0x900)
    word_doc[0x06:0x08] = (0x0409).to_bytes(2, "little")  # English lid -> cp1252
    word_doc[offset_u : offset_u + len(u16)] = u16
    word_doc[offset_c : offset_c + len(a8)] = a8

    n, m = len(unicode_text), len(ascii_text)
    cps = [0, n, n + m]
    plc = b"".join(cp.to_bytes(4, "little") for cp in cps)
    # PCD0: 16-bit Unicode piece (fCompressed=0), fc = offset.
    plc += (0).to_bytes(2, "little") + offset_u.to_bytes(4, "little") + (0).to_bytes(2, "little")
    # PCD1: 8-bit compressed piece (fCompressed bit 30 set), stored fc = offset*2.
    fc1 = (offset_c * 2) | 0x40000000
    plc += (0).to_bytes(2, "little") + fc1.to_bytes(4, "little") + (0).to_bytes(2, "little")

    clx = b"\x02" + len(plc).to_bytes(4, "little") + plc
    word_doc[0x1A2:0x1A6] = (0).to_bytes(4, "little")  # fcClx = start of table
    word_doc[0x1A6:0x1AA] = len(clx).to_bytes(4, "little")

    out = _extract_text_via_piece_table(bytes(word_doc), clx)

    assert out is not None
    assert "现代医养信息系统" in out
    assert "ABC" in out
    assert "�" not in out and "꿺" not in out
