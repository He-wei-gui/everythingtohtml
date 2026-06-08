"""Carries everything we know about an input stream as it flows through converters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

__all__ = ["StreamInfo"]


@dataclass(frozen=True, kw_only=True)
class StreamInfo:
    """Immutable bag of hints describing a binary stream.

    Every field is optional. Converters use whichever signals are available
    (extension, mimetype, magic bytes, declared charset) to decide whether they
    can handle the stream. Because it is frozen, passing it between converters is
    safe; use :meth:`copy_and_update` to derive a refined copy.
    """

    mimetype: str | None = None
    extension: str | None = None
    charset: str | None = None
    filename: str | None = None
    local_path: str | None = None
    url: str | None = None

    def copy_and_update(self, *args: StreamInfo | None, **kwargs: object) -> StreamInfo:
        """Return a new ``StreamInfo`` with non-``None`` values layered on top.

        Accepts other ``StreamInfo`` instances (applied in order) and/or keyword
        overrides. ``None`` values never overwrite an existing value.
        """
        updates: dict[str, object] = {}
        for arg in args:
            if arg is None:
                continue
            updates.update({k: v for k, v in asdict(arg).items() if v is not None})
        updates.update({k: v for k, v in kwargs.items() if v is not None})
        return replace(self, **updates)  # type: ignore[arg-type]

    def normalized_extension(self) -> str | None:
        """Lower-cased extension with a leading dot, or ``None``."""
        if not self.extension:
            return None
        ext = self.extension.lower()
        return ext if ext.startswith(".") else f".{ext}"
