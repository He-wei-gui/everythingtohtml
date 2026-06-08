"""Tests for the optional Office converters (docx, xlsx, pptx).

Fixtures are generated at runtime with the relevant writer libraries; each test
skips cleanly if its dependency is unavailable.
"""

from __future__ import annotations

import io

import pytest

from everythingtohtml import EverythingToHtml, StreamInfo


@pytest.fixture
def eth() -> EverythingToHtml:
    return EverythingToHtml()


def test_docx(eth: EverythingToHtml) -> None:
    pytest.importorskip("mammoth")
    docx = pytest.importorskip("docx")  # python-docx, for building the fixture

    document = docx.Document()
    document.add_heading("Report Title", level=1)
    document.add_paragraph("A paragraph of body text.")
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    result = eth.convert(buffer, stream_info=StreamInfo(extension=".docx"))
    assert "Report Title" in result.html
    assert "A paragraph of body text." in result.html
    assert result.title == "Report Title"


def test_xlsx(eth: EverythingToHtml) -> None:
    openpyxl = pytest.importorskip("openpyxl")

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["Name", "Score"])
    sheet.append(["Alice", 95])
    sheet.append(["Bob", 88])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    result = eth.convert(buffer, stream_info=StreamInfo(extension=".xlsx"))
    assert "<h2>Data</h2>" in result.html
    assert "<th>Name</th>" in result.html
    assert "<td>Alice</td>" in result.html
    assert "95" in result.html


def test_pptx(eth: EverythingToHtml) -> None:
    pptx = pytest.importorskip("pptx")

    presentation = pptx.Presentation()
    layout = presentation.slide_layouts[1]
    slide = presentation.slides.add_slide(layout)
    slide.shapes.title.text = "Slide Title"
    slide.placeholders[1].text = "Bullet point one"
    buffer = io.BytesIO()
    presentation.save(buffer)
    buffer.seek(0)

    result = eth.convert(buffer, stream_info=StreamInfo(extension=".pptx"))
    assert "Slide Title" in result.html
    assert "Bullet point one" in result.html
    assert 'class="slide"' in result.html
