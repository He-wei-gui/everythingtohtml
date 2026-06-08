# Launch kit

Copy-paste posts for sharing everythingtohtml. The single biggest driver of stars
is showing up where developers already discuss tools — so post in a few places,
respond to comments, and link back to the repo.

Repo: https://github.com/He-wei-gui/everythingtohtml

---

## Hacker News (Show HN)

**Title** (HN caps titles ~80 chars; keep it plain, no emoji):

```
Show HN: everythingtohtml – convert PDF, Office, Markdown and data files to HTML
```

**Body:**

```
I built everythingtohtml, a small Python library + CLI that converts a wide range
of formats — PDF, Word (.docx and legacy .doc), Excel, PowerPoint, EPUB, Markdown,
CSV/TSV, JSON, Jupyter notebooks, RSS/Atom, YAML and reStructuredText — into clean,
self-contained HTML.

It's deliberately the structural inverse of Microsoft's markitdown. markitdown
flattens documents down to Markdown; I kept hitting cases where that's lossy —
tables collapse, slide/section structure disappears, nested data gets ambiguous.
HTML preserves that structure, opens in any browser, and (in my experience) LLMs
parse explicit <table>/<section> markup more reliably for RAG ingestion.

Design mirrors markitdown's: a converter registry where each format is one small
class (accepts() + convert()), optional-dependency extras so the core install
stays tiny, and entry-point plugins. There's also a merge() for collating several
documents into one page and a diff() for a highlighted comparison of two.

It's MIT-licensed, typed, tested (multi-OS CI), and pip-installable.
Feedback and new-format PRs very welcome.
```

---

## Reddit — r/Python (and r/coolgithubprojects)

**Title:**

```
everythingtohtml: convert PDF/Word/Excel/Markdown/… into clean self-contained HTML (the inverse of markitdown)
```

**Body:**

```
I wanted markitdown but in reverse — structure-preserving HTML instead of lossy
Markdown — so I built everythingtohtml.

- One API: `EverythingToHtml().convert("file.docx").html`
- 17+ formats: PDF, docx/doc, xlsx, pptx, epub, md, html, csv/tsv, json/jsonl,
  ipynb, rss/atom, yaml, rst, txt
- Tiny core; heavy parsers live behind extras (`[pdf]`, `[docx]`, …)
- merge() multiple docs into one page; diff() two docs side by side
- CLI: `everythingtohtml report.docx -o report.html`
- MIT, typed (py.typed), pytest + ruff + mypy in CI

Repo: https://github.com/He-wei-gui/everythingtohtml
Would love feedback on the converter API and which format to add next.
```

> r/Python tip: posts do best Tue–Thu mornings US time, and the mods like a
> follow-up comment explaining *why* you built it.

---

## 掘金 / V2EX / 中文社区

**标题：**

```
everythingtohtml：把 PDF/Word/Excel/Markdown 等几乎任何文件转成干净的 HTML（markitdown 的反向版）
```

**正文：**

```
微软的 markitdown 是把各种文件转成 Markdown，但 Markdown 会丢结构——表格被压平、
PPT 的分页没了、嵌套数据也变模糊。于是我写了 everythingtohtml，做相反的事：把文件
转成保留结构的、自包含的 HTML，既适合人在浏览器里看，也更适合喂给 LLM 做 RAG。

特点：
- 一个 API：EverythingToHtml().convert("file.docx").html
- 支持 17+ 种格式：PDF、docx/doc、xlsx、pptx、epub、md、csv/tsv、json、ipynb、rss…
- 核心依赖很小，重型解析器放在 extras 里按需安装
- 支持把多个文档合并成一个 HTML，以及两个文档的高亮差异对比
- 命令行：everythingtohtml report.docx -o report.html
- MIT 协议，带类型标注，CI 跑 pytest + ruff + mypy

仓库：https://github.com/He-wei-gui/everythingtohtml
欢迎 star、提 issue、贡献新格式 :)
```

---

## X / Twitter

```
Built everythingtohtml: convert PDF, Word, Excel, PPT, EPUB, Markdown, CSV, JSON &
more into clean, self-contained HTML — the structural inverse of markitdown.

Great for RAG: LLMs parse real <table>/<section> markup far better than flattened
Markdown.

MIT · pip install everythingtohtml
https://github.com/He-wei-gui/everythingtohtml
```

---

## After you post

- Reply to every comment quickly for the first few hours — engagement keeps posts ranked.
- Pin a "good first issue" or two so newcomers can contribute.
- Add the live site link (GitHub Pages) once it's enabled.
- Submit to awesome-lists (e.g. awesome-python, awesome-llm-tools) via PR.
