"""Jupyter notebook (.ipynb) -> HTML.

Renders markdown cells as prose and code cells as fenced blocks, plus any text or
image outputs, using only the standard library plus the bundled Markdown renderer.
"""

from __future__ import annotations

import json
from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._html_builder import escape_attr, escape_text, wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text

__all__ = ["IpynbConverter"]


class IpynbConverter(DocumentConverter):
    """Convert a Jupyter notebook into a readable HTML transcript."""

    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        return stream_info.normalized_extension() == ".ipynb"

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        from markdown_it import MarkdownIt

        # strict=False tolerates literal control characters that some tools leave
        # inside cell-output strings, which strict JSON would reject.
        notebook = json.loads(read_text(file_stream, stream_info), strict=False)
        md = MarkdownIt("commonmark", {"html": False, "linkify": True})

        parts: list[str] = []
        title = stream_info.filename
        for cell in notebook.get("cells", []):
            source = _join(cell.get("source", ""))
            cell_type = cell.get("cell_type")
            if cell_type == "markdown":
                if title is None or title == stream_info.filename:
                    heading = _first_heading(source)
                    if heading:
                        title = heading
                parts.append(f'<section class="cell md-cell">{md.render(source)}</section>')
            elif cell_type == "code":
                parts.append(
                    '<section class="cell code-cell">'
                    f"<pre><code>{escape_text(source)}</code></pre>"
                    f"{_render_outputs(cell.get('outputs', []))}"
                    "</section>"
                )

        html = wrap_document("\n".join(parts), title=title)
        return DocumentConverterResult(html, title=title)


def _join(source: Any) -> str:
    return "".join(source) if isinstance(source, list) else str(source)


def _first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def _render_outputs(outputs: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for output in outputs:
        data = output.get("data", {})
        if "image/png" in data:
            b64 = _join(data["image/png"]).replace("\n", "")
            rendered.append(f'<img alt="output" src="data:image/png;base64,{escape_attr(b64)}">')
        elif "text/html" in data:
            rendered.append(f'<div class="output">{_join(data["text/html"])}</div>')
        elif "text/plain" in data:
            rendered.append(f'<pre class="output">{escape_text(_join(data["text/plain"]))}</pre>')
        elif output.get("output_type") == "stream":
            rendered.append(
                f'<pre class="output">{escape_text(_join(output.get("text", "")))}</pre>'
            )
    return "".join(rendered)
