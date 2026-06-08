"""RSS 2.0 and Atom feeds -> HTML, using defusedxml for safe parsing."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_attr, escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["RssConverter"]

_ACCEPTED_EXTENSIONS = {".rss", ".atom"}
_ACCEPTED_MIME_TYPES = {"application/rss+xml", "application/atom+xml"}


class RssConverter(DocumentConverter):
    """Render a news/blog feed as a simple article list."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        if ext in _ACCEPTED_EXTENSIONS or mimetype in _ACCEPTED_MIME_TYPES:
            return True
        # Sniff: XML-ish documents whose root hints at a feed.
        pos = file_stream.tell()
        head = file_stream.read(1024)
        file_stream.seek(pos)
        lowered = head.lower()
        return b"<rss" in lowered or b"<feed" in lowered

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from defusedxml.ElementTree import parse

        tree = parse(file_stream)
        root = tree.getroot()
        tag = _localname(root.tag)

        if tag == "rss":
            return self._convert_rss(root, stream_info)
        if tag == "feed":
            return self._convert_atom(root, stream_info)

        # Fall back to treating any channel-bearing document as RSS-like.
        return self._convert_rss(root, stream_info)

    def _convert_rss(self, root: Any, stream_info: StreamInfo) -> DocumentConverterResult:
        channel = _find(root, "channel")
        if channel is None:
            channel = root
        title = _text(_find(channel, "title")) or stream_info.filename
        parts = [f"<h1>{escape_text(title or 'Feed')}</h1>"]
        description = _text(_find(channel, "description"))
        if description:
            parts.append(f"<p>{escape_text(description)}</p>")

        for item in _findall(channel, "item"):
            parts.append(
                self._render_entry(
                    title=_text(_find(item, "title")),
                    link=_text(_find(item, "link")),
                    date=_text(_find(item, "pubDate")),
                    body=_text(_find(item, "description")),
                )
            )

        html = wrap_document("\n".join(parts), title=title)
        return DocumentConverterResult(html, title=title)

    def _convert_atom(self, root: Any, stream_info: StreamInfo) -> DocumentConverterResult:
        title = _text(_find(root, "title")) or stream_info.filename
        parts = [f"<h1>{escape_text(title or 'Feed')}</h1>"]
        subtitle = _text(_find(root, "subtitle"))
        if subtitle:
            parts.append(f"<p>{escape_text(subtitle)}</p>")

        for entry in _findall(root, "entry"):
            link_el = _find(entry, "link")
            link = link_el.get("href") if link_el is not None else None
            parts.append(
                self._render_entry(
                    title=_text(_find(entry, "title")),
                    link=link,
                    date=_text(_find(entry, "updated")) or _text(_find(entry, "published")),
                    body=_text(_find(entry, "summary")) or _text(_find(entry, "content")),
                )
            )

        html = wrap_document("\n".join(parts), title=title)
        return DocumentConverterResult(html, title=title)

    @staticmethod
    def _render_entry(
        *,
        title: str | None,
        link: str | None,
        date: str | None,
        body: str | None,
    ) -> str:
        heading = escape_text(title or "Untitled")
        if link:
            heading = f'<a href="{escape_attr(link)}">{heading}</a>'
        parts = [f"<article><h2>{heading}</h2>"]
        if date:
            parts.append(f'<p class="meta"><time>{escape_text(date)}</time></p>')
        if body:
            parts.append(f'<div class="entry-body">{escape_text(body)}</div>')
        parts.append("</article>")
        return "".join(parts)


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(element: Any, name: str) -> Any:
    if element is None:
        return None
    for child in element:
        if _localname(child.tag) == name:
            return child
    return None


def _findall(element: Any, name: str) -> list[Any]:
    if element is None:
        return []
    return [child for child in element if _localname(child.tag) == name]


def _text(element: Any) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip()
