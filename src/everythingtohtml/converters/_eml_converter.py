"""Email messages (``.eml`` / RFC 822) -> HTML, using only the standard library."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_text, wrap_document
from .._stream_info import StreamInfo

__all__ = ["EmlConverter"]

_ACCEPTED_EXTENSIONS = {".eml"}
_ACCEPTED_MIME_TYPES = {"message/rfc822"}
_HEADER_FIELDS = ("From", "To", "Cc", "Date", "Subject")


class EmlConverter(DocumentConverter):
    """Render an email — headers, body, and attachment list — as HTML."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ext = stream_info.normalized_extension()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return ext in _ACCEPTED_EXTENSIONS or mimetype in _ACCEPTED_MIME_TYPES

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from email import message_from_bytes
        from email.policy import default as default_policy

        message = message_from_bytes(file_stream.read(), policy=default_policy)

        rows: list[str] = []
        for field in _HEADER_FIELDS:
            value = message[field]
            if value:
                rows.append(
                    f"<tr><th>{escape_text(field)}</th><td>{escape_text(str(value))}</td></tr>"
                )
        header_table = f'<table class="email-headers"><tbody>{"".join(rows)}</tbody></table>'

        body_html = _render_body(message)
        attachments = _render_attachments(message)

        title = str(message["Subject"]) if message["Subject"] else stream_info.filename
        body = f"<header>{header_table}</header>{body_html}{attachments}"
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)


def _render_body(message: Any) -> str:
    try:
        part = message.get_body(preferencelist=("html", "plain"))
    except Exception:
        part = None

    if part is None:
        return "<p><em>(no readable body)</em></p>"

    content_type = part.get_content_type()
    content = part.get_content()

    if content_type == "text/html":
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        body_tag = soup.body
        inner = body_tag.decode_contents() if body_tag else soup.decode_contents()
        return f'<section class="email-body">{inner}</section>'

    # Plain text: preserve line structure as paragraphs.
    paragraphs = [
        f"<p>{escape_text(block)}</p>" for block in str(content).split("\n\n") if block.strip()
    ]
    return f'<section class="email-body">{"".join(paragraphs)}</section>'


def _render_attachments(message: Any) -> str:
    names: list[str] = []
    try:
        iterator = message.iter_attachments()
    except Exception:
        return ""
    for attachment in iterator:
        filename = attachment.get_filename()
        if filename:
            names.append(filename)
    if not names:
        return ""
    items = "".join(f"<li>{escape_text(name)}</li>" for name in names)
    return f'<section class="email-attachments"><h2>Attachments</h2><ul>{items}</ul></section>'
