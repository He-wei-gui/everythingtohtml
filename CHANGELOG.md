# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-07-04

### Added

- **LaTeX math in Markdown.** `$…$` and `$$…$$` are parsed with the `dollarmath`
  plugin (so `_`, `\`, and `&` survive Markdown) and rendered with MathJax, which
  is injected into the document `<head>` only when a document actually contains
  math. Matrices, `\underbrace`, `\text{…}` (incl. CJK), etc. all render.
- The in-browser demo preview now allows scripts, so MathJax renders live there
  too (and the "Edit text" preview mode keeps working).

## [0.1.2] - 2026-06-09

### Changed

- **Tables render much better.** The default stylesheet now gives every table a
  shaded header row, zebra striping, compact cells, and horizontal scrolling for
  wide tables (so they no longer overflow the page). This applies to DOCX, XLSX,
  legacy DOC (via LibreOffice), CSV, and Markdown output alike.
- **DOCX tables**: mammoth's bare tables are post-processed to promote the first
  row to a real `<thead>`/`<th>` header and to unwrap single-paragraph cells, so
  they read as proper tables instead of an unstyled grid.
- Version bump also refreshes the in-browser demo wheel (cache-bust).

## [0.1.1] - 2026-06-09

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
  fallback otherwise.
- **`EverythingToHtml.merge()`**: combine several sources into one HTML document,
  with `layout="stacked"` (table of contents) or `layout="columns"` (side by
  side). Exposed on the CLI by passing two or more sources, plus `--columns`.
- **`EverythingToHtml.diff()`**: render a highlighted, line-by-line comparison of
  two documents. Exposed on the CLI via `--diff`.
- **In-browser "universal reader" demo** (GitHub Pages + Pyodide): drag in a file
  and read it as HTML entirely client-side, with multi-file merge and two-file
  diff. PPTX shapes are positioned by their slide coordinates.

### Fixed

- **Legacy `.doc` mojibake**: the pure-Python fallback now parses the Word piece
  table (CLX) from the table stream and decodes each text piece with its own
  8-bit/16-bit encoding (UTF-16LE or the language-appropriate code page). This
  fixes garbled output — Chinese especially — that the earlier single-span
  heuristic produced. The heuristic remains as a last-resort fallback.
- Optional-dependency errors now surface as `MissingDependencyException` with the
  exact install hint, instead of being hidden inside a generic
  `FileConversionException`.

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
