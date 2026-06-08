"""Command-line interface for everythingtohtml.

Examples
--------
    everythingtohtml report.docx > report.html
    everythingtohtml data.csv -o data.html
    everythingtohtml https://example.com/feed.rss
    cat notes.md | everythingtohtml --extension .md > notes.html
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .__about__ import __version__
from ._everything_to_html import EverythingToHtml
from ._exceptions import EverythingToHtmlException
from ._stream_info import StreamInfo


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="everythingtohtml",
        description="Convert files, URLs, or stdin into clean, self-contained HTML.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path or URL to convert. Omit (or use '-') to read from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write HTML to this file instead of stdout.",
    )
    parser.add_argument(
        "-e",
        "--extension",
        help="Hint the source extension (e.g. '.md') when reading from stdin.",
    )
    parser.add_argument(
        "-m",
        "--mimetype",
        help="Hint the source mimetype when it cannot be inferred.",
    )
    parser.add_argument(
        "--charset",
        help="Hint the source character encoding (e.g. 'utf-8').",
    )
    parser.add_argument(
        "--use-plugins",
        action="store_true",
        help="Load third-party converter plugins registered via entry points.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"everythingtohtml {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    stream_info = StreamInfo(
        extension=args.extension,
        mimetype=args.mimetype,
        charset=args.charset,
    )

    engine = EverythingToHtml(enable_plugins=args.use_plugins)

    try:
        if args.source and args.source != "-":
            result = engine.convert(args.source, stream_info=stream_info)
        else:
            data = sys.stdin.buffer.read()
            result = engine.convert(data, stream_info=stream_info)
    except EverythingToHtmlException as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result.html)
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stdout.write(result.html)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
