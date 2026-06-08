"""Robust byte-stream-to-``str`` decoding shared by text-based converters."""

from __future__ import annotations

from typing import BinaryIO

from ._stream_info import StreamInfo

__all__ = ["read_text"]


def read_text(file_stream: BinaryIO, stream_info: StreamInfo) -> str:
    """Decode a binary stream to text.

    Order of preference:

    1. The charset declared on ``stream_info`` (e.g. parsed from an HTTP header).
    2. UTF-8, which is correct the overwhelming majority of the time.
    3. ``charset_normalizer``'s best guess for legacy encodings.
    4. UTF-8 with replacement as a last resort so we never hard-fail.
    """
    raw = file_stream.read()
    if isinstance(raw, str):  # already-decoded stream
        return raw

    if stream_info.charset:
        try:
            return raw.decode(stream_info.charset)
        except (LookupError, UnicodeDecodeError):
            pass

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best is not None:
            return str(best)
    except Exception:  # pragma: no cover - defensive, charset_normalizer is a dep
        pass

    return raw.decode("utf-8", errors="replace")
