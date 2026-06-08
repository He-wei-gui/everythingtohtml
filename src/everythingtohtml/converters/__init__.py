"""Built-in converters bundled with everythingtohtml.

Each converter is a small, self-contained class implementing the
:class:`~everythingtohtml._base_converter.DocumentConverter` contract.
"""

from __future__ import annotations

from ._csv_converter import CsvConverter
from ._docx_converter import DocxConverter
from ._html_converter import HtmlConverter
from ._ipynb_converter import IpynbConverter
from ._json_converter import JsonConverter
from ._markdown_converter import MarkdownConverter
from ._plain_text_converter import PlainTextConverter
from ._pptx_converter import PptxConverter
from ._rss_converter import RssConverter
from ._rst_converter import RstConverter
from ._xlsx_converter import XlsxConverter
from ._yaml_converter import YamlConverter

__all__ = [
    "CsvConverter",
    "DocxConverter",
    "HtmlConverter",
    "IpynbConverter",
    "JsonConverter",
    "MarkdownConverter",
    "PlainTextConverter",
    "PptxConverter",
    "RssConverter",
    "RstConverter",
    "XlsxConverter",
    "YamlConverter",
]
