"""A tiny end-to-end demo of everythingtohtml.

Run it from the repo root:

    python examples/convert_demo.py

It converts a few in-memory samples and writes the HTML next to this file.
"""

from __future__ import annotations

from pathlib import Path

from everythingtohtml import EverythingToHtml, StreamInfo

SAMPLES: dict[str, tuple[str, bytes]] = {
    "markdown": (
        ".md",
        b"# Quarterly Report\n\n"
        b"Revenue is **up 20%**. See the [details](https://example.com).\n\n"
        b"| Metric | Q1 | Q2 |\n|---|---|---|\n| Revenue | 100 | 120 |\n",
    ),
    "csv": (".csv", b"name,role\nAda,Engineer\nGrace,Scientist\n"),
    "json": (".json", b'{"project": "everythingtohtml", "stars": 0, "open_source": true}'),
}


def main() -> None:
    eth = EverythingToHtml()
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    for name, (ext, data) in SAMPLES.items():
        result = eth.convert(data, stream_info=StreamInfo(extension=ext))
        out_path = out_dir / f"{name}.html"
        out_path.write_text(result.html, encoding="utf-8")
        print(f"{name:9} -> {out_path}  (title={result.title!r})")


if __name__ == "__main__":
    main()
