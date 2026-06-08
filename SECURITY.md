# Security Policy

## Supported versions

everythingtohtml is pre-1.0; security fixes are applied to the latest released
version on PyPI and the `main` branch.

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, use GitHub's private vulnerability reporting:
**Security → Report a vulnerability** on the repository, or email the maintainers
listed in the repository profile.

We aim to acknowledge reports within 72 hours and to ship a fix or mitigation as
quickly as the severity warrants.

## Security model and hardening

everythingtohtml processes untrusted documents, so it is built defensively:

- **XML is parsed with `defusedxml`** to neutralise entity-expansion ("billion
  laughs") and external-entity (XXE) attacks in RSS/Atom inputs.
- **Text content is HTML-escaped** (`escape_text` / `escape_attr`) before being
  written into output markup, preventing injection from CSV/JSON/notebook data.
- **HTML normalization strips active content** — `<script>`, `<style>`,
  `<iframe>`, `<object>`, and `<embed>` are removed during `.html` conversion.
- **Network access is opt-in**: only `convert_uri` with an `http(s)` URL performs
  a request, and only the `http`, `https`, `file`, and `data` schemes are
  accepted. Local-file conversion never touches the network.

When embedding everythingtohtml output in a larger page, treat the *original
document's* HTML/Markdown as untrusted: the normalizer reduces risk but is not a
full HTML sanitizer. For hostile inputs rendered in a browser context, pass the
output through a dedicated sanitizer (e.g. `bleach`) as well.
