# everythingtohtml

> Convert (almost) any file into clean, self-contained HTML — a universal file reader for your browser and scripts.

[![CI](https://github.com/He-wei-gui/everythingtohtml/actions/workflows/ci.yml/badge.svg)](https://github.com/He-wei-gui/everythingtohtml/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/everythingtohtml?color=brightgreen)](https://pypi.org/project/everythingtohtml/)
[![Python versions](https://img.shields.io/pypi/pyversions/everythingtohtml.svg)](https://pypi.org/project/everythingtohtml/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [中文](README.zh-CN.md) | **[▶ Live demo — drag a file, read it as HTML](https://he-wei-gui.github.io/everythingtohtml/)**

<p align="center">
  <a href="https://he-wei-gui.github.io/everythingtohtml/">
    <img src="site/demo.gif" alt="everythingtohtml — drag a file, read it as clean HTML" width="760">
  </a>
</p>

**everythingtohtml** is the spiritual inverse of tools like
[markitdown](https://github.com/microsoft/markitdown): instead of flattening rich
documents *down* to Markdown, it lifts a wide range of formats *up* into clean,
styled, standalone HTML you can open in a browser, embed in a page, or feed to a
workflow that wants structured markup.

One small API. One CLI. A pluggable converter registry. No browser, no network
required for local files.

**中文简介**：everythingtohtml 是一个浏览器里的万能文件阅读器，也是一个 Python 包和 CLI。它可以把 PDF、Office、Markdown、CSV、JSON、EPUB 等常见文件转换成干净、自包含的 HTML，方便直接阅读、分享和自动化处理。

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()
result = eth.convert("quarterly-report.docx")
print(result.html)        # a complete <!DOCTYPE html> document
print(result.title)       # best-effort document title
```

```console
$ everythingtohtml notes.md -o notes.html
$ everythingtohtml data.csv > data.html
$ everythingtohtml https://example.com/feed.rss > feed.html
```

## Why HTML (and not Markdown)?

Markdown is lossy: tables get flattened, styling vanishes, slide structure
disappears, and nested data becomes ambiguous. HTML keeps the structure that
matters — headings, tables, lists, sections, links, images — while staying:

- **Human-friendly** — open the output in any browser, no toolchain needed.
- **Restyleable** — every document ships with a small, overridable stylesheet.
- **Structure-preserving** — explicit `<table>`/`<section>` markup keeps tables,
  sections, and nested content easy to inspect and process.
- **Self-contained** — one file, valid HTML5, dark-mode aware.

## Supported formats

| Format | Extensions | Extra needed |
| --- | --- | --- |
| Plain text | `.txt`, anything textual | — (built in) |
| Markdown | `.md`, `.markdown`, `.mkd` | — (built in) |
| HTML (clean/normalize) | `.html`, `.htm`, `.xhtml` | — (built in) |
| CSV / TSV | `.csv`, `.tsv` | — (built in) |
| JSON / JSONL | `.json`, `.jsonl`, `.ndjson` | — (built in) |
| Jupyter notebook | `.ipynb` | — (built in) |
| RSS / Atom feeds | `.rss`, `.atom` | — (built in) |
| EPUB e-books | `.epub` | — (built in) |
| Email | `.eml` | — (built in) |
| OpenDocument Text | `.odt` | — (built in) |
| YAML | `.yaml`, `.yml` | `pip install everythingtohtml[yaml]` |
| reStructuredText | `.rst` | `pip install everythingtohtml[rst]` |
| Word | `.docx` | `pip install everythingtohtml[docx]` |
| Word (legacy) | `.doc` | `pip install everythingtohtml[doc]` (LibreOffice recommended) |
| Excel | `.xlsx`, `.xlsm` | `pip install everythingtohtml[xlsx]` |
| PowerPoint | `.pptx` | `pip install everythingtohtml[pptx]` |
| PDF | `.pdf` | `pip install everythingtohtml[pdf]` |

> **Legacy `.doc`**: best results come from having [LibreOffice](https://www.libreoffice.org/)
> installed (used headlessly for high-fidelity conversion). Without it, a
> pure-Python `olefile` fallback recovers the text content.

> Want everything? `pip install everythingtohtml[all]`

New formats are just a small class away — see [Writing a converter](#writing-a-converter).

## Installation

```console
# core formats only (tiny dependency footprint)
pip install everythingtohtml

# pull in Office + data formats
pip install "everythingtohtml[all]"

# or cherry-pick
pip install "everythingtohtml[docx,xlsx]"
```

Requires Python 3.10+.

## Usage

### Library

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()

# From a path
result = eth.convert("slides.pptx")

# From bytes or an open stream
with open("data.csv", "rb") as f:
    result = eth.convert(f)

# From a URL (http/https/file/data URIs)
result = eth.convert("https://example.com/posts.atom")

# Give hints when the source is ambiguous (e.g. stdin)
from everythingtohtml import StreamInfo
result = eth.convert(raw_bytes, stream_info=StreamInfo(extension=".md"))

result.html          # the full HTML document (str)
result.title         # detected title, or None
result.text_content  # alias for .html (drop-in for markdown-style code)
```

### Command line

```console
everythingtohtml SOURCE [-o OUTPUT] [--extension .md] [--mimetype text/markdown]

# convert a file to a file
everythingtohtml report.docx -o report.html

# pipe through stdin (give it a hint)
cat notes.md | everythingtohtml --extension .md > notes.html

# fetch and convert a remote feed
everythingtohtml https://hnrss.org/frontpage > hn.html
```

The CLI is also available as `e2h` for the impatient.

## Merging and comparing documents

Need to collate a stack of Word files into one page, or see exactly what changed
between two revisions? everythingtohtml does both — for **any** supported format.

```python
eth = EverythingToHtml()

# Merge several documents into one HTML page (each becomes a section, with a TOC)
merged = eth.merge(["intro.docx", "chapter1.doc", "appendix.pdf"])

# Place them side by side for visual comparison
columns = eth.merge(["draft-v1.docx", "draft-v2.docx"], layout="columns")

# Produce a highlighted, line-by-line diff of two documents' text
changes = eth.diff("spec-old.docx", "spec-new.docx")
open("changes.html", "w", encoding="utf-8").write(changes.html)
```

From the CLI:

```console
# two or more sources are merged automatically
everythingtohtml intro.docx chapter1.doc appendix.pdf -o handbook.html

# side-by-side layout
everythingtohtml old.docx new.docx --columns -o compare.html

# highlighted diff of exactly two documents
everythingtohtml spec-old.docx spec-new.docx --diff -o changes.html
```

## Architecture

everythingtohtml borrows the proven shape of markitdown:

```
EverythingToHtml            # engine: detection + dispatch + plugins
 ├─ StreamInfo              # immutable bag of hints (ext, mime, charset, …)
 ├─ DocumentConverter       # base class: accepts() + convert()
 │   ├─ MarkdownConverter
 │   ├─ CsvConverter
 │   ├─ DocxConverter (mammoth)
 │   └─ … one small class per format
 └─ DocumentConverterResult # { html, title, metadata }
```

When you call `convert()`, the engine:

1. **Detects** the stream — extension, mimetype, declared charset, and magic-byte
   sniffing via `puremagic` fill in a `StreamInfo`.
2. **Dispatches** — converters are tried in priority order; each `accepts()` is a
   cheap, non-destructive check. Specific formats win over the plain-text
   catch-all.
3. **Converts** — the winning converter returns a `DocumentConverterResult`. If a
   converter accepts but raises, the engine records it and tries the next one, so
   one greedy converter can't sink the whole conversion.

### Writing a converter

```python
from everythingtohtml import DocumentConverter, DocumentConverterResult, StreamInfo
from everythingtohtml._html_builder import wrap_document, escape_text

class UpperTextConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info: StreamInfo, **kwargs) -> bool:
        return stream_info.normalized_extension() == ".loud"

    def convert(self, file_stream, stream_info: StreamInfo, **kwargs):
        text = file_stream.read().decode("utf-8").upper()
        return DocumentConverterResult(wrap_document(f"<pre>{escape_text(text)}</pre>"))

eth = EverythingToHtml()
eth.register_converter(UpperTextConverter())
```

Ship it as a package and expose it as a plugin via entry points so any user can
`EverythingToHtml(enable_plugins=True)` and pick it up automatically — see
[`docs/PLUGINS.md`](docs/PLUGINS.md).

## Contributing

Contributions are very welcome — new converters especially. See
[CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).
Found a security issue? See [SECURITY.md](SECURITY.md).

## Acknowledgements

The converter-registry design is directly inspired by Microsoft's excellent
[markitdown](https://github.com/microsoft/markitdown). everythingtohtml aims to be
its mirror image for teams that want structure-preserving HTML instead of Markdown.

## License

[MIT](LICENSE) © everythingtohtml contributors
