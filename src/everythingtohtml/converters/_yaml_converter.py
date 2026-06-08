"""YAML -> HTML by decoding to native objects and reusing the JSON tree renderer."""

from __future__ import annotations

from typing import Any, BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException
from .._html_builder import wrap_document
from .._stream_info import StreamInfo
from .._text_utils import read_text
from ._json_converter import _render

__all__ = ["YamlConverter"]

_ACCEPTED_EXTENSIONS = {".yaml", ".yml"}
_ACCEPTED_MIME_TYPES = {"application/x-yaml", "text/yaml", "application/yaml"}


class YamlConverter(DocumentConverter):
    """Render YAML documents as a navigable tree (requires the ``yaml`` extra)."""

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
        try:
            import yaml
        except ImportError as exc:
            raise MissingDependencyException(
                "YAML support requires the 'yaml' extra. "
                "Install it with: pip install everythingtohtml[yaml]"
            ) from exc

        text = read_text(file_stream, stream_info)
        documents = list(yaml.safe_load_all(text))
        data: Any = documents[0] if len(documents) == 1 else documents

        body = f'<div class="json-tree">{_render(data)}</div>'
        title = stream_info.filename
        html = wrap_document(body, title=title)
        return DocumentConverterResult(html, title=title)
