# Writing converters and plugins

everythingtohtml is built around one small contract, so adding a new format —
whether in-tree or as a third-party package — is intentionally easy.

## The converter contract

```python
from everythingtohtml import DocumentConverter, DocumentConverterResult, StreamInfo
from everythingtohtml._html_builder import wrap_document, escape_text


class MyConverter(DocumentConverter):
    # Lower numbers are tried first. Use the defaults unless you have a reason:
    #   PRIORITY_SPECIFIC_FILE_FORMAT (0.0)  -> a real format
    #   PRIORITY_GENERIC_FILE_FORMAT (10.0)  -> a greedy catch-all
    priority = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT

    def accepts(self, file_stream, stream_info: StreamInfo, **kwargs) -> bool:
        # Cheap, side-effect-free. If you read bytes to sniff, seek back to 0.
        return stream_info.normalized_extension() == ".myfmt"

    def convert(self, file_stream, stream_info: StreamInfo, **kwargs) -> DocumentConverterResult:
        raw = file_stream.read().decode("utf-8")
        body = f"<pre>{escape_text(raw)}</pre>"
        return DocumentConverterResult(wrap_document(body, title=stream_info.filename))
```

### `StreamInfo`

An immutable bag of hints. The useful fields:

| field | meaning |
| --- | --- |
| `extension` | e.g. `".pdf"` (use `normalized_extension()` for a lower-cased, dotted form) |
| `mimetype` | e.g. `"text/markdown"` |
| `charset` | declared encoding, if any |
| `filename` | base filename, if known |
| `local_path` / `url` | provenance, if known |

### `DocumentConverterResult`

```python
DocumentConverterResult(html, title=None, metadata=None)
```

`html` should be a **complete** HTML document — use `wrap_document(...)` to get
the standard `<!DOCTYPE html>` shell and stylesheet. `text_content` is an alias
for `html`, and `str(result)` returns the HTML.

## Registering at runtime

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()
eth.register_converter(MyConverter())          # later registrations win ties
```

## Shipping a plugin package

Expose a callable that registers your converter(s), and advertise it under the
`everythingtohtml.converter` entry-point group:

```toml
# pyproject.toml of your plugin package
[project.entry-points."everythingtohtml.converter"]
myfmt = "my_plugin:register"
```

```python
# my_plugin/__init__.py
from .converter import MyConverter

def register(engine):
    engine.register_converter(MyConverter())
```

Users then opt in with:

```python
eth = EverythingToHtml(enable_plugins=True)    # or: eth.load_plugins()
```

or on the CLI:

```console
everythingtohtml --use-plugins document.myfmt
```

## Guidelines

- **Escape everything** that originates from the input (`escape_text`,
  `escape_attr`). Never interpolate raw document text into markup.
- **Preserve structure** — emit real `<table>`, `<section>`, `<h1>`…`<h6>`,
  lists, and links rather than flattening to text.
- **Fail loudly on missing deps** — raise `MissingDependencyException` with the
  exact `pip install everythingtohtml[extra]` command.
- **Don't consume the stream in `accepts()`** without seeking back to `0`.
