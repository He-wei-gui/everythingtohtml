# everythingtohtml 中文发布稿

> 在线 Demo：https://he-wei-gui.github.io/everythingtohtml/ ·
> GitHub：https://github.com/He-wei-gui/everythingtohtml ·
> PyPI：`pip install everythingtohtml`

---

## 长文版：掘金 / 开源中国 / 知乎

# 我做了一个浏览器里的「万能文件阅读器」：拖个文件进去，秒变干净 HTML

大家好，我最近开源了一个小工具：**everythingtohtml**。

一句话介绍：把各种文件转换成干净、自包含、能直接在浏览器里打开的 HTML。你可以把它理解成 [markitdown](https://github.com/microsoft/markitdown) 的反向版——markitdown 把文件转成 Markdown，而 everythingtohtml 把文件转成 HTML。

做它的原因很朴素：很多时候我只是想**快速打开一个文件、看看里面是什么、再分享一个不依赖原始软件的版本**。HTML 在这件事上很合适——浏览器都能打开，而且表格、标题层级、列表、链接、代码块这些结构都能保留下来，不会像 Markdown 那样被拍平。

### 两种用法

1. **在线 Demo（最推荐）**：打开网页，把文件拖进去就行。转换**全程在你本地浏览器里完成（基于 Pyodide / WebAssembly），文件不上传到任何服务器**。还内置了「Word 表格 / 扫描 PDF / Excel」等一键示例，点一下就能看到效果。
2. **Python 包 / CLI**：适合批量转换、脚本处理、自动化流水线。

### 支持 20+ 种格式

- **文档**：PDF、Word（.docx / .doc）、PowerPoint、EPUB、OpenDocument（.odt）、Markdown、HTML、reStructuredText
- **数据**：CSV / TSV、JSON / JSONL、YAML、Excel
- **开发者常见**：Jupyter Notebook、RSS / Atom、邮件 .eml、纯文本
- **进阶能力**：把多个文件 **合并** 成一个 HTML、两个文件生成 **diff 对比页**

### 一些我比较满意的细节

- **扫描版 PDF**（纯图片、没有文字层）会直接把页面图片显示出来，而不是甩你一句"无文本"。
- **表格渲染**做了打磨：表头、斑马纹、宽表横向滚动，docx 表格也会自动识别表头。
- **老版 .doc 中文不乱码**：解析了 Word 的 piece table，按每段各自的编码（UTF-16 / GBK 等）正确解码。
- **安全**：XML 用 defusedxml 防 XXE，HTML 会剥掉脚本，所有文本都转义。

### 上手

```bash
pip install "everythingtohtml[all]"
everythingtohtml report.docx -o report.html
e2h data.xlsx -o data.html

# 多文件合并 / 两文件对比
everythingtohtml a.docx b.docx c.pdf -o 合集.html
everythingtohtml 旧版.docx 新版.docx --diff -o 差异.html
```

```python
from everythingtohtml import EverythingToHtml

eth = EverythingToHtml()
result = eth.convert("report.docx")
print(result.html)
```

项目是 **MIT 协议**，带完整的 pytest 测试、ruff + mypy、多系统 CI，已发布到 PyPI，浏览器版用 GitHub Pages 自动部署。

- 在线 Demo：https://he-wei-gui.github.io/everythingtohtml/
- GitHub：https://github.com/He-wei-gui/everythingtohtml

欢迎试用、star、提 issue。也很想听听：**你最希望它支持哪种格式？**

---

## 短文版：V2EX / 社群

# 做了个浏览器里的万能文件阅读器：拖文件转成自包含 HTML（已上 PyPI）

开源工具 **everythingtohtml**：把 PDF、Word、Excel、PowerPoint、Markdown、CSV、JSON、EPUB、邮件等 20+ 种文件转成干净、自包含的 HTML。

核心是**在线 Demo**：打开网页拖文件进去，转换全程在本地浏览器里跑（Pyodide / WASM），**文件不上传**。扫描版 PDF 会显示原图，docx 表格会渲染成正常表格。

也提供 Python 包和 CLI：

```bash
pip install "everythingtohtml[all]"
everythingtohtml report.docx -o report.html
```

还支持把多个文件合并成一个 HTML、两个文件生成 diff 对比页。

- 在线 Demo：https://he-wei-gui.github.io/everythingtohtml/
- GitHub：https://github.com/He-wei-gui/everythingtohtml

欢迎试用和 star。有特别想支持的格式也欢迎告诉我。

---

## 朋友圈 / 微信群版

我开源了一个小工具 **everythingtohtml**：浏览器里的万能文件阅读器。

打开网页，把 PDF / Word / Excel / PPT / Markdown / CSV 等文件拖进去，就能转成干净、自包含的 HTML，直接阅读或分享。**转换在本地浏览器完成，文件不上传**。

在线试：https://he-wei-gui.github.io/everythingtohtml/
GitHub：https://github.com/He-wei-gui/everythingtohtml

觉得有用的话，帮我点个 star 🙏

---

## 常见问题回复

### 和 markitdown 有什么区别？

markitdown 把各种文件转成 **Markdown**；everythingtohtml 做的是反方向，转成 **HTML**。

我更关注"能直接打开阅读"和"尽量保留原始结构"：表格、标题层级、链接、代码块、邮件头、Notebook 单元格、幻灯片版式等。HTML 文件也能直接丢给别人用浏览器打开，不用装原始软件。

### 在线 Demo 会上传文件吗？

**不会。** 在线 Demo 的转换全程在你的浏览器本地完成（用 Pyodide 在浏览器里跑 Python），文件不会上传到服务器。公司内部或敏感文件，也可以直接用 CLI 在本地跑。

### 为什么是 HTML 而不是 Markdown？

Markdown 会丢结构：表格被压平、样式没了、PPT 版式消失、嵌套数据变模糊。HTML 能把这些结构留住，而且任何浏览器都能直接打开。

### 后续路线图

近期想做：PDF 多栏阅读顺序优化、扫描件 OCR（可选）、Excel 日期/数字格式化、PPT 演讲者备注，以及更多格式（LaTeX、字幕等）。欢迎来 issue 区点单。
