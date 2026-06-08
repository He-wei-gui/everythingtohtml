"""The converter contract and the result object every converter returns."""

from __future__ import annotations

from typing import Any, BinaryIO

from ._stream_info import StreamInfo

__all__ = ["DocumentConverter", "DocumentConverterResult"]


class DocumentConverterResult:
    """The output of a successful conversion.

    The canonical payload is :attr:`html`. ``text_content`` is provided as an
    alias so code written against markdown-style converters keeps working when
    pointed at this library, and ``str(result)`` yields the HTML directly.
    """

    def __init__(
        self,
        html: str,
        *,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.html = html
        self.title = title
        self.metadata = metadata or {}

    @property
    def text_content(self) -> str:
        """Alias for :attr:`html` (drop-in compatibility with markdown converters)."""
        return self.html

    @text_content.setter
    def text_content(self, value: str) -> None:
        self.html = value

    def __str__(self) -> str:
        return self.html


class DocumentConverter:
    """Base class for all converters.

    A converter answers two questions:

    * :meth:`accepts` — *can* I handle this stream? (cheap, no side effects)
    * :meth:`convert` — *do* the conversion and return HTML.

    ``accepts`` must not consume the stream destructively: read what you need to
    sniff, then ``seek(0)`` back. ``convert`` may read freely; the engine resets
    the stream before handing it to each converter.
    """

    # Higher priority converters are tried first. Specific format converters use
    # low numbers; greedy catch-alls (plain text) use high numbers.
    PRIORITY_SPECIFIC_FILE_FORMAT = 0.0
    PRIORITY_GENERIC_FILE_FORMAT = 10.0

    priority: float = PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        raise NotImplementedError

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        raise NotImplementedError
