"""Helpers for assembling clean, self-contained HTML documents.

Every converter produces an HTML *fragment* (the meaningful body markup). This
module wraps fragments into a full document with a small, readable default
stylesheet so the output looks decent on its own while staying easy to restyle.
"""

from __future__ import annotations

from html import escape as _escape

__all__ = ["escape_text", "escape_attr", "wrap_document", "DEFAULT_STYLESHEET"]


DEFAULT_STYLESHEET = """\
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica,
    Arial, sans-serif;
  line-height: 1.6;
  max-width: 50rem;
  margin: 2rem auto;
  padding: 0 1rem;
  color: #1a1a1a;
  background: #ffffff;
}
@media (prefers-color-scheme: dark) {
  body { color: #e6e6e6; background: #121212; }
  a { color: #6ea8fe; }
  table th { background: #1e1e1e; }
  table td, table th { border-color: #333; }
  pre, code { background: #1e1e1e; }
}
h1, h2, h3 { line-height: 1.25; }
a { color: #0b5cff; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
table td, table th { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; }
table th { background: #f5f5f5; }
pre {
  background: #f5f5f5; padding: 1rem; overflow-x: auto; border-radius: 6px;
}
code { background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 4px; }
pre code { padding: 0; background: none; }
blockquote {
  border-left: 4px solid #ddd; margin: 1rem 0; padding: 0.2rem 1rem; color: #666;
}
img { max-width: 100%; height: auto; }
"""


def escape_text(text: str) -> str:
    """Escape text for safe inclusion in HTML element content."""
    return _escape(text, quote=False)


def escape_attr(text: str) -> str:
    """Escape text for safe inclusion in a double-quoted HTML attribute."""
    return _escape(text, quote=True)


def wrap_document(
    body: str,
    *,
    title: str | None = None,
    lang: str = "en",
    include_style: bool = True,
    extra_head: str = "",
) -> str:
    """Wrap an HTML *fragment* into a complete, standalone HTML5 document."""
    safe_title = escape_text(title) if title else "Converted Document"
    style = f"<style>\n{DEFAULT_STYLESHEET}</style>\n" if include_style else ""
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{escape_attr(lang)}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="generator" content="everythingtohtml">\n'
        f"<title>{safe_title}</title>\n"
        f"{style}"
        f"{extra_head}"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )
