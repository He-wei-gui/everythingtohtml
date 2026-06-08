"""everythingtohtml — convert (almost) any file into clean, self-contained HTML.

Quick start
-----------
>>> from everythingtohtml import EverythingToHtml
>>> eth = EverythingToHtml()
>>> result = eth.convert("document.docx")   # doctest: +SKIP
>>> open("document.html", "w", encoding="utf-8").write(result.html)  # doctest: +SKIP
"""

from __future__ import annotations

from .__about__ import __version__
from ._base_converter import DocumentConverter, DocumentConverterResult
from ._everything_to_html import EverythingToHtml
from ._exceptions import (
    EverythingToHtmlException,
    FileConversionException,
    MissingDependencyException,
    UnsupportedFormatException,
)
from ._stream_info import StreamInfo

__all__ = [
    "__version__",
    "EverythingToHtml",
    "DocumentConverter",
    "DocumentConverterResult",
    "StreamInfo",
    "EverythingToHtmlException",
    "FileConversionException",
    "MissingDependencyException",
    "UnsupportedFormatException",
]
