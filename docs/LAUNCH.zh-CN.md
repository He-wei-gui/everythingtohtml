# everythingtohtml 中文发布文案

用于在中文社区发布 everythingtohtml。核心卖点建议聚焦在「浏览器拖拽式万能文件阅读器」：不用上传文件、不用装办公软件、直接把常见文件转成干净自包含的 HTML。

仓库：https://github.com/He-wei-gui/everythingtohtml  
在线 Demo：https://he-wei-gui.github.io/everythingtohtml/

---

## 掘金 / V2EX / 开源中国

**标题：**

```text
我做了一个浏览器里的万能文件阅读器：PDF、Office、Markdown、数据文件都能转 HTML
```

**正文：**

```markdown
大家好，我最近做了一个开源小工具：everythingtohtml。

它的目标很简单：把各种文件转换成干净、自包含、能直接在浏览器里打开的 HTML。你可以把它理解成 markitdown 的反向版：markitdown 把文件转成 Markdown，而 everythingtohtml 把文件转成 HTML。

我做它的原因也很朴素：很多时候我只是想快速打开一个文件、检查里面的内容、分享一个不依赖原始软件的版本。HTML 在这件事上很适合：浏览器都能打开，表格、标题、列表、链接、代码块这些结构也能保留下来。

项目现在有两个用法：

1. 在线 Demo：直接把文件拖进浏览器，转换过程完全在本地浏览器里完成，不上传文件。
2. Python 包 / CLI：适合批量转换、脚本处理、自动化流水线。

支持的格式包括：

- 文档：PDF、Word（.docx / .doc）、PowerPoint、EPUB、Markdown、HTML、reStructuredText
- 数据：CSV / TSV、JSON / JSONL、YAML、Excel
- 开发者常见文件：Jupyter Notebook、RSS / Atom、纯文本
- 其他能力：多个文件 merge 成一个 HTML、两个文件 diff 成对比页面

命令行示例：

```bash
pip install "everythingtohtml[all]"
everythingtohtml report.docx -o report.html
e2h data.xlsx -o data.html
```

Python API 示例：

```python
from everythingtohtml import EverythingToHtml

converter = EverythingToHtml()
result = converter.convert("report.docx")
print(result.html)
```

我现在最想把它打磨成一个好用的「万能文件阅读器」：打开网页，拖文件，看结果。后面会继续增强浏览器版，比如多文件自动合并、两文件差异对比、更多格式支持。

项目是 MIT 协议，已经配置了 pytest、ruff、mypy、多系统 CI 和 PyPI 自动发布。

在线 Demo：https://he-wei-gui.github.io/everythingtohtml/  
GitHub：https://github.com/He-wei-gui/everythingtohtml

欢迎试用、star、提 issue。也很想知道：你最希望它支持哪种格式？
```

---

## V2EX 更短版

**标题：**

```text
做了个浏览器里的万能文件阅读器：拖文件转成自包含 HTML
```

**正文：**

```markdown
我做了一个开源工具 everythingtohtml：把 PDF、Word、Excel、PowerPoint、Markdown、CSV、JSON、EPUB 等文件转成干净、自包含的 HTML。

现在最核心的是在线 Demo：打开网页，把文件拖进去，转换过程完全在本地浏览器里跑，不上传文件。

它也提供 Python 包和 CLI：

```bash
pip install "everythingtohtml[all]"
everythingtohtml report.docx -o report.html
```

目前支持 20+ 种格式，还支持把多个文件合并成一个 HTML，以及两个文件生成 diff 对比页。

在线 Demo：https://he-wei-gui.github.io/everythingtohtml/  
GitHub：https://github.com/He-wei-gui/everythingtohtml

欢迎试用和 star。如果你有特别想支持的文件格式，也欢迎告诉我。
```

---

## 微信群 / 朋友圈

```text
我做了一个开源小工具 everythingtohtml：浏览器里的万能文件阅读器。

打开网页，把 PDF / Word / Excel / Markdown / CSV / JSON 等文件拖进去，就能转成干净、自包含的 HTML。转换过程在本地浏览器里完成，不上传文件。

在线 Demo：https://he-wei-gui.github.io/everythingtohtml/
GitHub：https://github.com/He-wei-gui/everythingtohtml

如果你觉得有用，欢迎帮忙点个 star 🙏
```

---

## 中文社区回复模板

**有人问“和 markitdown 有什么区别？”**

```text
markitdown 主要是把各种文件转成 Markdown；everythingtohtml 做的是反方向，把各种文件转成 HTML。

我更关注“能直接打开阅读”和“尽量保留原始结构”：比如表格、标题层级、链接、代码块、邮件头、Notebook 单元格等。HTML 文件也可以直接丢给别人用浏览器打开，不需要安装原始软件。
```

**有人担心隐私**

```text
在线 Demo 的转换过程是在浏览器本地完成的，文件不会上传到服务器。它用 Pyodide 在浏览器里跑 Python 转换器。

如果是公司内部或敏感文件，也可以直接用 CLI 在本地跑。
```

**有人问后续计划**

```text
短期会优先增强在线 Demo：多文件自动合并、两文件 diff 入口、更多格式在浏览器里直接转换。也会继续补格式支持和测试。
```

---

## 发布小贴士

- 标题别太像广告，强调“我做了一个”“欢迎试用”更自然。
- 中文社区优先放在线 Demo，再放 GitHub；降低试用门槛。
- 第一条评论可以补充技术实现：Pyodide、Python 包、转换器注册机制。
- 发帖后前几个小时尽量及时回复，尤其是格式需求和 bug 反馈。
