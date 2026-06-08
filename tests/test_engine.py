"""Tests for the engine: detection, dispatch, plugins, and error handling."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from everythingtohtml import (
    DocumentConverter,
    DocumentConverterResult,
    EverythingToHtml,
    MissingDependencyException,
    StreamInfo,
    UnsupportedFormatException,
)


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


def test_convert_local_path(eth: EverythingToHtml, write_file) -> None:
    path: Path = write_file("doc.md", "# Local\n")
    result = eth.convert(str(path))
    assert result.title == "Local"
    assert "<h1>Local</h1>" in result.html


def test_convert_pathlib(eth: EverythingToHtml, write_file) -> None:
    path: Path = write_file("doc.csv", "a,b\n1,2\n")
    result = eth.convert(path)
    assert "<th>a</th>" in result.html


def test_detection_by_extension(eth: EverythingToHtml) -> None:
    result = eth.convert(b"# Heading\n", stream_info=StreamInfo(extension=".md"))
    assert "<h1>Heading</h1>" in result.html


def test_data_uri(eth: EverythingToHtml) -> None:
    encoded = base64.b64encode(b"# From Data URI\n").decode()
    uri = f"data:text/markdown;base64,{encoded}"
    result = eth.convert(uri)
    assert "From Data URI" in result.html


def test_data_uri_plain(eth: EverythingToHtml) -> None:
    result = eth.convert("data:text/plain,hello%20world")
    assert "hello world" in result.html


def test_unsupported_scheme(eth: EverythingToHtml) -> None:
    with pytest.raises(UnsupportedFormatException):
        eth.convert("ftp://example.com/file.txt")


def test_non_seekable_stream(eth: EverythingToHtml) -> None:
    import io

    class NonSeekable(io.RawIOBase):
        def __init__(self, data: bytes) -> None:
            self._data = data
            self._read = False

        def readable(self) -> bool:
            return True

        def seekable(self) -> bool:
            return False

        def read(self, size: int = -1) -> bytes:
            if self._read:
                return b""
            self._read = True
            return self._data

    stream = NonSeekable(b"# Streamed\n")
    result = eth.convert(stream, stream_info=StreamInfo(extension=".md"))
    assert "Streamed" in result.html


def test_register_custom_converter() -> None:
    class LoudConverter(DocumentConverter):
        def accepts(self, file_stream, stream_info, **kwargs) -> bool:
            return stream_info.normalized_extension() == ".loud"

        def convert(self, file_stream, stream_info, **kwargs):
            text = file_stream.read().decode("utf-8").upper()
            return DocumentConverterResult(f"<!DOCTYPE html><html><body>{text}</body></html>")

    eth = EverythingToHtml()
    eth.register_converter(LoudConverter())
    result = eth.convert(b"hello", stream_info=StreamInfo(extension=".loud"))
    assert "HELLO" in result.html


def test_custom_converter_overrides_builtin() -> None:
    """A later registration should win ties against built-ins of equal priority."""

    class OverrideMarkdown(DocumentConverter):
        def accepts(self, file_stream, stream_info, **kwargs) -> bool:
            return stream_info.normalized_extension() == ".md"

        def convert(self, file_stream, stream_info, **kwargs):
            return DocumentConverterResult("<!DOCTYPE html><html><body>OVERRIDDEN</body></html>")

    eth = EverythingToHtml()
    eth.register_converter(OverrideMarkdown())
    result = eth.convert(b"# Real Heading\n", stream_info=StreamInfo(extension=".md"))
    assert "OVERRIDDEN" in result.html


def test_failed_converter_falls_through() -> None:
    """If a converter accepts but raises, the engine tries the next candidate."""

    class Bomb(DocumentConverter):
        priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT - 1

        def accepts(self, file_stream, stream_info, **kwargs) -> bool:
            return stream_info.normalized_extension() == ".md"

        def convert(self, file_stream, stream_info, **kwargs):
            raise RuntimeError("boom")

    eth = EverythingToHtml()
    eth.register_converter(Bomb())
    # Markdown converter should still produce output after Bomb fails.
    result = eth.convert(b"# Survived\n", stream_info=StreamInfo(extension=".md"))
    assert "Survived" in result.html


def test_missing_dependency_propagates() -> None:
    """A converter's MissingDependencyException must surface (not be hidden as a
    generic FileConversionException), so callers see the actionable install hint."""

    class NeedsExtra(DocumentConverter):
        def accepts(self, file_stream, stream_info, **kwargs) -> bool:
            return stream_info.normalized_extension() == ".needy"

        def convert(self, file_stream, stream_info, **kwargs):
            raise MissingDependencyException("pip install everythingtohtml[needy]")

    eth = EverythingToHtml()
    eth.register_converter(NeedsExtra())
    # Binary, non-text bytes so the plain-text fallback declines and NeedsExtra is
    # the only converter that accepts.
    with pytest.raises(MissingDependencyException):
        eth.convert(b"\x00\x01\x02\xff", stream_info=StreamInfo(extension=".needy"))


def test_result_text_content_alias(eth: EverythingToHtml) -> None:
    result = eth.convert(b"hello", stream_info=StreamInfo(extension=".txt"))
    assert result.text_content == result.html
    assert str(result) == result.html
