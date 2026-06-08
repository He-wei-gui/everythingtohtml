"""The :class:`EverythingToHtml` engine: detection, dispatch, and plugins."""

from __future__ import annotations

import io
import mimetypes
import os
import sys
from typing import Any, BinaryIO
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from ._base_converter import DocumentConverter, DocumentConverterResult
from ._exceptions import (
    FailedConversionAttempt,
    FileConversionException,
    UnsupportedFormatException,
)
from ._stream_info import StreamInfo
from .converters import (
    CsvConverter,
    DocxConverter,
    EpubConverter,
    HtmlConverter,
    IpynbConverter,
    JsonConverter,
    MarkdownConverter,
    PdfConverter,
    PlainTextConverter,
    PptxConverter,
    RssConverter,
    RstConverter,
    XlsxConverter,
    YamlConverter,
)

__all__ = ["EverythingToHtml"]

_PLUGIN_ENTRY_POINT_GROUP = "everythingtohtml.converter"

# Built-in converters, registered in dependency-light first order. Specific
# formats are registered after the catch-all so that, on ties, they win.
_BUILTIN_CONVERTERS: tuple[type[DocumentConverter], ...] = (
    PlainTextConverter,
    HtmlConverter,
    MarkdownConverter,
    CsvConverter,
    JsonConverter,
    YamlConverter,
    IpynbConverter,
    RssConverter,
    RstConverter,
    EpubConverter,
    DocxConverter,
    XlsxConverter,
    PptxConverter,
    PdfConverter,
)


class _Registration:
    __slots__ = ("converter", "priority", "index")

    def __init__(self, converter: DocumentConverter, index: int) -> None:
        self.converter = converter
        self.priority = converter.priority
        self.index = index


class EverythingToHtml:
    """Convert files, streams, and URIs into clean, self-contained HTML.

    Example
    -------
    >>> from everythingtohtml import EverythingToHtml
    >>> eth = EverythingToHtml()
    >>> result = eth.convert("README.md")
    >>> result.html.startswith("<!DOCTYPE html>")
    True
    """

    def __init__(
        self,
        *,
        enable_builtins: bool = True,
        enable_plugins: bool = False,
    ) -> None:
        self._registrations: list[_Registration] = []
        self._next_index = 0
        if enable_builtins:
            for converter_cls in _BUILTIN_CONVERTERS:
                self.register_converter(converter_cls())
        if enable_plugins:
            self.load_plugins()

    # -- registration ------------------------------------------------------

    def register_converter(self, converter: DocumentConverter) -> None:
        """Add a converter. Later registrations win ties against earlier ones."""
        self._registrations.append(_Registration(converter, self._next_index))
        self._next_index += 1

    def load_plugins(self) -> None:
        """Discover and register third-party converters via entry points.

        A plugin advertises a callable under the ``everythingtohtml.converter``
        entry-point group; the callable receives this engine and registers its
        own converters. See ``docs/PLUGINS.md``.
        """
        from importlib.metadata import entry_points

        for ep in entry_points(group=_PLUGIN_ENTRY_POINT_GROUP):
            register = ep.load()
            register(self)

    @property
    def _ordered(self) -> list[DocumentConverter]:
        # Lowest priority number first; for equal priority, most-recently
        # registered first (so plugins and later converters can override).
        ordered = sorted(self._registrations, key=lambda r: (r.priority, -r.index))
        return [r.converter for r in ordered]

    # -- public conversion API --------------------------------------------

    def convert(
        self,
        source: str | os.PathLike[str] | bytes | BinaryIO,
        *,
        stream_info: StreamInfo | None = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert ``source`` to HTML.

        ``source`` may be a local path, a URI (``http``, ``https``, ``file``,
        ``data``), raw ``bytes``, or an already-open binary stream.
        """
        if isinstance(source, (str, os.PathLike)):
            text = os.fspath(source)
            if _looks_like_uri(text):
                return self.convert_uri(text, stream_info=stream_info, **kwargs)
            return self.convert_local(text, stream_info=stream_info, **kwargs)
        if isinstance(source, (bytes, bytearray)):
            return self.convert_stream(io.BytesIO(bytes(source)), stream_info=stream_info, **kwargs)
        return self.convert_stream(source, stream_info=stream_info, **kwargs)

    def convert_local(
        self,
        path: str | os.PathLike[str],
        *,
        stream_info: StreamInfo | None = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert a file on the local filesystem."""
        path = os.fspath(path)
        base = StreamInfo(
            local_path=path,
            filename=os.path.basename(path),
            extension=_ext(path),
            mimetype=mimetypes.guess_type(path)[0],
        )
        guessed = base.copy_and_update(stream_info)
        with open(path, "rb") as stream:
            return self._convert(stream, guessed, **kwargs)

    def convert_stream(
        self,
        stream: BinaryIO,
        *,
        stream_info: StreamInfo | None = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert an open binary stream.

        The stream must be seekable; if it is not, it is buffered into memory.
        """
        if not stream.seekable():
            stream = io.BytesIO(stream.read())
        guessed = stream_info or StreamInfo()
        return self._convert(stream, guessed, **kwargs)

    def convert_uri(
        self,
        uri: str,
        *,
        stream_info: StreamInfo | None = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert content addressed by a URI (``http(s)``, ``file``, ``data``)."""
        uri = uri.strip()
        parsed = urlparse(uri)
        scheme = parsed.scheme.lower()

        if scheme == "file":
            local = url2pathname(parsed.path)
            return self.convert_local(local, stream_info=stream_info, **kwargs)
        if scheme == "data":
            stream, info = _read_data_uri(uri)
            return self._convert(stream, info.copy_and_update(stream_info), **kwargs)
        if scheme in ("http", "https"):
            stream, info = _fetch_http(uri)
            return self._convert(stream, info.copy_and_update(stream_info), **kwargs)
        raise UnsupportedFormatException(f"Unsupported URI scheme: {scheme!r}")

    # -- internals ---------------------------------------------------------

    def _convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        enriched = self._sniff(stream, stream_info)

        attempts: list[FailedConversionAttempt] = []
        for converter in self._ordered:
            stream.seek(0)
            try:
                if not converter.accepts(stream, enriched, **kwargs):
                    continue
            except Exception:  # a misbehaving accepts() should not abort dispatch
                continue

            stream.seek(0)
            try:
                return converter.convert(stream, enriched, **kwargs)
            except Exception:
                attempts.append(FailedConversionAttempt(converter, sys.exc_info()))

        if attempts:
            raise FileConversionException(attempts=attempts)
        raise UnsupportedFormatException(
            "No converter could handle this input "
            f"(extension={enriched.extension!r}, mimetype={enriched.mimetype!r}). "
            "It may need an optional extra; see 'pip install everythingtohtml[all]'."
        )

    @staticmethod
    def _sniff(stream: BinaryIO, stream_info: StreamInfo) -> StreamInfo:
        """Fill in missing extension/mimetype hints from magic bytes."""
        if stream_info.extension and stream_info.mimetype:
            return stream_info

        pos = stream.tell()
        header = stream.read(2048)
        stream.seek(pos)
        if not header:
            return stream_info

        try:
            import puremagic

            matches = puremagic.magic_string(header)
        except Exception:
            return stream_info

        if not matches:
            return stream_info

        best = matches[0]
        updates: dict[str, object] = {}
        if not stream_info.extension and getattr(best, "extension", None):
            updates["extension"] = best.extension
        if not stream_info.mimetype and getattr(best, "mime_type", None):
            updates["mimetype"] = best.mime_type
        return stream_info.copy_and_update(**updates) if updates else stream_info


# -- module-level helpers --------------------------------------------------


def _ext(path: str) -> str | None:
    ext = os.path.splitext(path)[1]
    return ext or None


def _looks_like_uri(text: str) -> bool:
    """True if ``text`` has a URI scheme rather than being a local path.

    A single-character "scheme" is treated as a Windows drive letter (``C:\\...``)
    and therefore *not* a URI. Recognised URI schemes are dispatched by
    :meth:`EverythingToHtml.convert_uri`, which rejects unsupported ones.
    """
    scheme = urlparse(text).scheme.lower()
    return bool(scheme) and len(scheme) > 1


def _read_data_uri(uri: str) -> tuple[BinaryIO, StreamInfo]:
    import base64

    header, _, data = uri[len("data:") :].partition(",")
    is_base64 = header.endswith(";base64")
    mimetype = header.split(";", 1)[0] or None
    charset = None
    for part in header.split(";"):
        if part.startswith("charset="):
            charset = part[len("charset=") :]
    raw = base64.b64decode(data) if is_base64 else unquote(data).encode("utf-8")
    ext = mimetypes.guess_extension(mimetype) if mimetype else None
    return io.BytesIO(raw), StreamInfo(mimetype=mimetype, charset=charset, extension=ext)


def _fetch_http(uri: str) -> tuple[BinaryIO, StreamInfo]:
    from urllib.request import Request, urlopen

    request = Request(uri, headers={"User-Agent": "everythingtohtml"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - scheme checked by caller
        raw = response.read()
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset()
        final_url = response.geturl()

    path = urlparse(final_url).path
    filename = os.path.basename(path) or None
    return io.BytesIO(raw), StreamInfo(
        mimetype=content_type or None,
        charset=charset,
        extension=_ext(path),
        filename=filename,
        url=final_url,
    )
