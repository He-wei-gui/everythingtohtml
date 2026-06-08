# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/everythingtohtml/everythingtohtml/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/everythingtohtml/everythingtohtml/releases/tag/v0.1.0
