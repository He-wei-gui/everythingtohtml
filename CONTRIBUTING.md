# Contributing to everythingtohtml

Thanks for your interest in improving everythingtohtml! New converters, bug fixes,
docs, and tests are all very welcome.

## Development setup

```console
git clone https://github.com/He-wei-gui/everythingtohtml.git
cd everythingtohtml
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e ".[all]" pytest ruff mypy python-docx
```

> `python-docx` is only needed to build the `.docx` test fixture; the library
> itself reads `.docx` with `mammoth`.

## Running the checks

```console
pytest -q                     # tests
ruff check src tests          # lint
ruff format src tests         # format
mypy src                      # type-check
```

All four must pass in CI before a PR can merge.

## Adding a new format converter

Converters are small, focused classes. The full contract lives in
[`docs/PLUGINS.md`](docs/PLUGINS.md), but the short version:

1. Create `src/everythingtohtml/converters/_yourformat_converter.py`.
2. Subclass `DocumentConverter` and implement:
   - `accepts(file_stream, stream_info, **kwargs) -> bool` — a cheap,
     non-destructive check (seek back to 0 if you read to sniff).
   - `convert(file_stream, stream_info, **kwargs) -> DocumentConverterResult` —
     return a complete HTML document via `wrap_document(...)`.
3. Register it in `converters/__init__.py` and `_BUILTIN_CONVERTERS`.
4. If it needs a heavy dependency, add it as an extra in `pyproject.toml` and
   raise `MissingDependencyException` with the exact install command when the
   import fails.
5. Add tests in `tests/`.

Keep output **structure-preserving** (real `<table>`, `<section>`, headings) and
**escaped** (use `escape_text` / `escape_attr`) so untrusted input can never
inject markup.

## Commit and PR conventions

- Keep PRs focused; one converter or fix per PR where possible.
- Describe *what* and *why* in the PR body.
- Add a `CHANGELOG.md` entry under `[Unreleased]`.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating you agree to uphold it.
