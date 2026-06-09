# everythingtohtml

> 把（几乎）任何文件转成干净、自包含的 HTML —— 一个浏览器里的「万能文件阅读器」，也是 Python 包和 CLI。

[![CI](https://github.com/He-wei-gui/everythingtohtml/actions/workflows/ci.yml/badge.svg)](https://github.com/He-wei-gui/everythingtohtml/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/everythingtohtml?color=brightgreen)](https://pypi.org/project/everythingtohtml/)
[![Python versions](https://img.shields.io/pypi/pyversions/everythingtohtml?color=blue)](https://pypi.org/project/everythingtohtml/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README.md) | 中文 | **[▶ 在线 Demo —— 拖个文件，秒变 HTML](https://he-wei-gui.github.io/everythingtohtml/)**

<p align="center">
  <a href="https://he-wei-gui.github.io/everythingtohtml/">
    <img src="site/demo.gif" alt="everythingtohtml —— 拖个文件，秒变干净 HTML" width="760">
  </a>
</p>

**everythingtohtml** 是 [markitdown](https://github.com/microsoft/markitdown) 的"反向版"：markitdown 把富文档**拍平成 Markdown**，而它把各种文件**抬升成**干净、带样式、自包含的 HTML——你可以直接在浏览器里打开、嵌进网页，或交给需要结构化标记的流程处理。

一个简洁的 API，一个 CLI，一套可插拔的转换器注册表。处理本地文件时不需要浏览器、也不需要联网。

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()
result = eth.convert("quarterly-report.docx")
print(result.html)        # 一份完整的 <!DOCTYPE html> 文档
print(result.title)       # 尽力识别出的文档标题
```

```console
$ everythingtohtml notes.md -o notes.html
$ everythingtohtml data.csv > data.html
$ everythingtohtml https://example.com/feed.rss > feed.html
```

## 为什么是 HTML，而不是 Markdown？

Markdown 是有损的：表格被压平、样式消失、幻灯片版式不见了、嵌套数据变得模糊。HTML 能保留真正重要的结构——标题、表格、列表、章节、链接、图片，同时还做到：

- **方便人看** —— 任何浏览器都能直接打开，无需任何工具链。
- **可重新换肤** —— 每份文档都带一份小巧、可覆盖的样式表。
- **保留结构** —— 显式的 `<table>` / `<section>` 标记，让表格、章节、嵌套内容易于检视和处理。
- **自包含** —— 单文件、合法的 HTML5、支持暗色模式。

## 支持的格式

| 格式 | 扩展名 | 需要的额外依赖 |
| --- | --- | --- |
| 纯文本 | `.txt`，以及任何文本 | —（内置） |
| Markdown | `.md`、`.markdown`、`.mkd` | —（内置） |
| HTML（清洗 / 规范化） | `.html`、`.htm`、`.xhtml` | —（内置） |
| CSV / TSV | `.csv`、`.tsv` | —（内置） |
| JSON / JSONL | `.json`、`.jsonl`、`.ndjson` | —（内置） |
| Jupyter Notebook | `.ipynb` | —（内置） |
| RSS / Atom 订阅 | `.rss`、`.atom` | —（内置） |
| EPUB 电子书 | `.epub` | —（内置） |
| 邮件 | `.eml` | —（内置） |
| OpenDocument 文本 | `.odt` | —（内置） |
| YAML | `.yaml`、`.yml` | `pip install everythingtohtml[yaml]` |
| reStructuredText | `.rst` | `pip install everythingtohtml[rst]` |
| Word | `.docx` | `pip install everythingtohtml[docx]` |
| Word（老版二进制） | `.doc` | `pip install everythingtohtml[doc]`（推荐装 LibreOffice） |
| Excel | `.xlsx`、`.xlsm` | `pip install everythingtohtml[xlsx]` |
| PowerPoint | `.pptx` | `pip install everythingtohtml[pptx]` |
| PDF | `.pdf` | `pip install everythingtohtml[pdf]` |

> **老版 `.doc`**：装了 [LibreOffice](https://www.libreoffice.org/) 效果最好（无头模式高保真转换）。没装时会用纯 Python 的 `olefile` 兜底提取正文（已正确处理中文，不再乱码）。扫描版 / 纯图片 PDF 会直接显示页面图片。

> 想要全部格式？ `pip install everythingtohtml[all]`

加新格式只需要写一个小类 —— 见 [编写转换器](#编写一个转换器)。

## 安装

```console
# 只装核心格式（依赖极少）
pip install everythingtohtml

# 拉上 Office + 数据等全部格式
pip install "everythingtohtml[all]"

# 或者按需选
pip install "everythingtohtml[docx,xlsx]"
```

需要 Python 3.10+。

## 使用

### 作为库

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()

# 从路径
result = eth.convert("slides.pptx")

# 从 bytes 或已打开的流
with open("data.csv", "rb") as f:
    result = eth.convert(f)

# 从 URL（http/https/file/data 协议）
result = eth.convert("https://example.com/posts.atom")

# 来源不明确时（比如 stdin）给点提示
from everythingtohtml import StreamInfo
result = eth.convert(raw_bytes, stream_info=StreamInfo(extension=".md"))

result.html          # 完整的 HTML 文档（str）
result.title         # 识别到的标题，或 None
result.text_content  # .html 的别名（兼容 markdown 风格的代码）
```

### 命令行

```console
everythingtohtml 来源 [-o 输出] [--extension .md] [--mimetype text/markdown]

# 文件转文件
everythingtohtml report.docx -o report.html

# 用管道走 stdin（给个扩展名提示）
cat notes.md | everythingtohtml --extension .md > notes.html

# 抓取并转换远程订阅
everythingtohtml https://hnrss.org/frontpage > hn.html
```

嫌长可以用别名 `e2h`。

## 合并与对比多个文档

想把一摞 Word 拼成一页，或者看清两个版本之间到底改了什么？everythingtohtml 两样都能做——而且对**任何**支持的格式都管用。

```python
eth = EverythingToHtml()

# 把多个文档合并成一个 HTML 页面（每个变成一个章节，带目录）
merged = eth.merge(["intro.docx", "chapter1.doc", "appendix.pdf"])

# 并排放置，方便肉眼对比
columns = eth.merge(["draft-v1.docx", "draft-v2.docx"], layout="columns")

# 对两个文档的文本做逐行高亮差异
changes = eth.diff("spec-old.docx", "spec-new.docx")
open("changes.html", "w", encoding="utf-8").write(changes.html)
```

命令行：

```console
# 传入两个及以上来源会自动合并
everythingtohtml intro.docx chapter1.doc appendix.pdf -o handbook.html

# 并排布局
everythingtohtml old.docx new.docx --columns -o compare.html

# 恰好两个文档的高亮差异
everythingtohtml spec-old.docx spec-new.docx --diff -o changes.html
```

## 架构

everythingtohtml 借用了 markitdown 久经验证的结构：

```
EverythingToHtml            # 引擎：检测 + 分发 + 插件
 ├─ StreamInfo              # 不可变的线索集合（扩展名、mime、charset…）
 ├─ DocumentConverter       # 基类：accepts() + convert()
 │   ├─ MarkdownConverter
 │   ├─ CsvConverter
 │   ├─ DocxConverter (mammoth)
 │   └─ … 每种格式一个小类
 └─ DocumentConverterResult # { html, title, metadata }
```

当你调用 `convert()` 时，引擎会：

1. **检测**流 —— 扩展名、mimetype、声明的 charset，以及通过 `puremagic` 做的魔术字节嗅探，一起填进 `StreamInfo`。
2. **分发** —— 按优先级依次尝试各转换器；每个 `accepts()` 都是廉价、无副作用的判断。专用格式优先于纯文本兜底。
3. **转换** —— 胜出的转换器返回 `DocumentConverterResult`。如果某个转换器接受了却抛错，引擎会记录并尝试下一个，避免一个贪心的转换器拖垮整次转换。

### 编写一个转换器

```python
from everythingtohtml import DocumentConverter, DocumentConverterResult, StreamInfo
from everythingtohtml._html_builder import wrap_document, escape_text

class UpperTextConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info: StreamInfo, **kwargs) -> bool:
        return stream_info.normalized_extension() == ".loud"

    def convert(self, file_stream, stream_info: StreamInfo, **kwargs):
        text = file_stream.read().decode("utf-8").upper()
        return DocumentConverterResult(wrap_document(f"<pre>{escape_text(text)}</pre>"))

eth = EverythingToHtml()
eth.register_converter(UpperTextConverter())
```

把它做成一个包、通过 entry points 暴露成插件，任何用户就能用 `EverythingToHtml(enable_plugins=True)` 自动加载它 —— 见 [`docs/PLUGINS.md`](docs/PLUGINS.md)。

## 参与贡献

非常欢迎贡献，尤其是新格式的转换器。请看 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [行为准则](CODE_OF_CONDUCT.md)。发现安全问题？见 [SECURITY.md](SECURITY.md)。

## 致谢

转换器注册表的设计直接受到微软优秀项目 [markitdown](https://github.com/microsoft/markitdown) 的启发。everythingtohtml 的目标是做它的镜像版，服务于那些想要"保留结构的 HTML"而非 Markdown 的团队。

## 许可证

[MIT](LICENSE) © everythingtohtml contributors
