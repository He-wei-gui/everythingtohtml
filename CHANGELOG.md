# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **EPUB** converter (built in, no extra): follows the spine reading order and
  concatenates chapters into one HTML document.
- **Email** (`.eml`) converter (built in): renders headers, body (HTML or plain),
  and an attachment list; HTML bodies are stripped of active content.
- **OpenDocument Text** (`.odt`) converter (built in): maps headings, paragraphs,
  lists, and tables to semantic HTML using only core dependencies.
- **PDF** converter behind the new `pdf` extra (`pdfminer.six`): recovers prose as
  paragraphs, one section per page.
- **Legacy `.doc`** converter behind the new `doc` extra: uses headless
  LibreOffice when available for high-fidelity output, with a pure-Python
  `olefile` text-extraction fallback otherwise.
- **`EverythingToHtml.merge()`**: combine several sources into one HTML document,
  with `layout="stacked"` (table of contents) or `layout="columns"` (side by
  side). Exposed on the CLI by passing two or more sources, plus `--columns`.
- **`EverythingToHtml.diff()`**: render a highlighted, line-by-line comparison of
  two documents. Exposed on the CLI via `--diff`.

## [0.1.0] - 2026-06-08

### Added

- Initial release of **everythingtohtml**.
- `EverythingToHtml` engine with stream detection, priority-based converter
  dispatch, and entry-point plugin support.
- Built-in converters (no extra dependencies): plain text, Markdown, HTML
  normalization, CSV/TSV, JSON/JSONL, Jupyter notebooks, and RSS/Atom feeds.
- Optional converters behind extras: Word (`docx`), Excel (`xlsx`),
  PowerPoint (`pptx`), reStructuredText (`rst`), and YAML (`yaml`).
- `everythingtohtml` / `e2h` command-line interface with stdin support.
- Self-contained, dark-mode-aware HTML output with an overridable stylesheet.

[Unreleased]: https://github.com/He-wei-gui/everythingtohtml/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/He-wei-gui/everythingtohtml/releases/tag/v0.1.0
