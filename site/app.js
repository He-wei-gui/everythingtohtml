/* everythingtohtml — in-browser universal reader, powered by Pyodide.
 *
 * Everything runs client-side: we load a CPython runtime (Pyodide) in WebAssembly,
 * install the everythingtohtml wheel into it, and call the same conversion
 * engine the CLI uses. No file ever leaves the page.
 */

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

const EXTRA_PACKAGE = {
  docx: "mammoth",
  xlsx: "openpyxl",
  pptx: "python-pptx",
  pdf: "pdfminer.six",
  yaml: "PyYAML",
  rst: "docutils",
  doc: "olefile",
};

const PYODIDE_PACKAGE_DEPS = {
  "python-pptx": ["lxml"],
  "pdfminer.six": ["cryptography"],
};

const SAMPLES = {
  md: {
    name: "sample.md",
    body:
      "# Quarterly Report\n\n" +
      "Revenue is **up 20%** this quarter. See [details](https://example.com).\n\n" +
      "| Metric | Q1 | Q2 |\n|---|---|---|\n| Revenue | 100 | 120 |\n| Users | 5k | 7k |\n\n" +
      "> A structure-preserving conversion — tables and links survive.\n",
  },
  csv: {
    name: "people.csv",
    body: "name,role,city\nAda Lovelace,Engineer,London\nGrace Hopper,Scientist,New York\n",
  },
  json: {
    name: "config.json",
    body: '{"project":"everythingtohtml","stars":0,"open_source":true,"formats":["pdf","docx","md"]}',
  },
  eml: {
    name: "message.eml",
    body:
      "From: alice@example.com\r\nTo: bob@example.com\r\nSubject: Lunch?\r\n" +
      'Date: Mon, 08 Jun 2026 12:00:00 +0000\r\nContent-Type: text/plain; charset="utf-8"\r\n\r\n' +
      "Hi Bob,\r\n\r\nWant to grab lunch tomorrow?\r\n\r\nBest,\r\nAlice\r\n",
  },
};

const els = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("file-input"),
  status: document.getElementById("status"),
  viewer: document.getElementById("viewer"),
  preview: document.getElementById("preview"),
  source: document.getElementById("source"),
  vName: document.getElementById("v-name"),
  vExt: document.getElementById("v-ext"),
  btnPreview: document.getElementById("btn-preview"),
  btnSource: document.getElementById("btn-source"),
  btnFullscreen: document.getElementById("btn-fullscreen"),
  btnDownload: document.getElementById("btn-download"),
  modeAuto: document.getElementById("mode-auto"),
  modeDiff: document.getElementById("mode-diff"),
  progress: document.getElementById("progress"),
  progressBar: document.getElementById("progress-bar"),
};

let pyodide = null;
let micropip = null;
const installed = new Set();
let currentHtml = "";
let currentName = "result";
let currentMode = "auto";

window.__e2h = { ready: false, lastHtml: null, error: null };

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("err", isError);
}

function setProgress(pct) {
  if (els.progressBar) els.progressBar.style.width = `${pct}%`;
}

async function boot() {
  try {
    setProgress(8);
    setStatus("Loading the in-browser Python runtime… / 正在加载浏览器内 Python 运行时…");
    const mod = await import(PYODIDE_URL + "pyodide.mjs");
    setProgress(25);
    pyodide = await mod.loadPyodide({ indexURL: PYODIDE_URL });
    setProgress(60);

    setStatus("Installing the converters… / 正在安装转换器…");
    await pyodide.loadPackage("micropip");
    micropip = pyodide.pyimport("micropip");
    setProgress(75);

    const wheelURL = new URL("wheels/everythingtohtml-0.1.2-py3-none-any.whl", location.href).href;
    await micropip.install(wheelURL);
    setProgress(92);

    await pyodide.runPythonAsync(`
from everythingtohtml import EverythingToHtml
from everythingtohtml._exceptions import MissingDependencyException

_eth = EverythingToHtml()
_EXTRA_PKG = ${JSON.stringify(EXTRA_PACKAGE).replace(/"/g, "'")}

def _missing_package(exc):
    msg = str(exc)
    for extra, pkg in _EXTRA_PKG.items():
        if '[' + extra + ']' in msg:
            return pkg
    return None

def _convert_path(path):
    try:
        return ['ok', _eth.convert(path).html]
    except MissingDependencyException as exc:
        pkg = _missing_package(exc)
        return ['need', pkg] if pkg else ['error', str(exc)]
    except Exception as exc:
        return ['error', f'{type(exc).__name__}: {exc}']

def _convert_paths(paths, mode, labels):
    try:
        if mode == 'diff':
            if len(paths) != 2:
                return ['error', 'Diff mode needs exactly two files. / Diff 模式需要正好两个文件。']
            return ['ok', _eth.diff(paths[0], paths[1], left_label=labels[0], right_label=labels[1]).html]
        if len(paths) > 1:
            return ['ok', _eth.merge(paths, labels=labels, title='Merged files').html]
        return ['ok', _eth.convert(paths[0]).html]
    except MissingDependencyException as exc:
        pkg = _missing_package(exc)
        return ['need', pkg] if pkg else ['error', str(exc)]
    except Exception as exc:
        return ['error', f'{type(exc).__name__}: {exc}']
`);

    setProgress(100);
    if (els.progress) els.progress.classList.add("done");
    setStatus("Ready — drop one or more files to read them. / 已就绪，拖入一个或多个文件即可阅读。");
    window.__e2h.ready = true;
  } catch (err) {
    setStatus("Failed to start the in-browser runtime: " + err.message, true);
    window.__e2h.error = String(err);
    throw err;
  }
}

async function loadSampleFile(url) {
  const name = url.split("/").pop() || "sample";
  if (!pyodide) {
    setStatus("Still starting up — one moment… / 还在启动，请稍等…");
    return;
  }
  setStatus(`Loading sample ${name}… / 正在加载示例 ${name}…`);
  try {
    const resp = await fetch(url);
    const bytes = new Uint8Array(await resp.arrayBuffer());
    await convertBytes(name, bytes);
  } catch (err) {
    setStatus("Could not load the sample file. / 无法加载示例文件。", true);
  }
}

async function convertBytes(name, bytes) {
  if (!pyodide) {
    setStatus("Still starting up — one moment… / 还在启动，请稍等…");
    return;
  }
  currentName = name;
  const dot = name.lastIndexOf(".");
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  const path = "/tmp/input" + ext;

  setStatus(`Converting ${name}… / 正在转换 ${name}…`);
  pyodide.FS.writeFile(path, bytes);
  pyodide.globals.set("_p", path);

  for (let attempt = 0; attempt < 6; attempt++) {
    const proxy = await pyodide.runPythonAsync("_convert_path(_p)");
    const [kind, payload] = proxy.toJs();
    proxy.destroy();

    if (kind === "ok") {
      showResult(name, ext || "—", payload);
      setStatus(`Converted ${name}. / 已转换 ${name}。`);
      return;
    }
    if (kind === "need") {
      setStatus(`Loading the ${payload} parser… / 正在加载 ${payload} 解析器…`);
      try {
        await installParser(payload);
        continue;
      } catch (err) {
        setStatus(parserLoadError(payload), true);
        return;
      }
    }
    setStatus("Could not convert this file: " + payload, true);
    window.__e2h.error = payload;
    return;
  }
  setStatus("Could not convert this file in the browser. / 浏览器里暂时无法转换这个文件。", true);
}

async function convertFiles(files, mode = currentMode) {
  const list = Array.from(files);
  if (list.length === 0) return;
  if (list.length === 1) {
    const buf = new Uint8Array(await list[0].arrayBuffer());
    await convertBytes(list[0].name, buf);
    return;
  }
  if (mode === "diff" && list.length !== 2) {
    setStatus("Diff mode needs exactly two files. / Diff 模式需要正好两个文件。", true);
    return;
  }
  if (!pyodide) {
    setStatus("Still starting up — one moment… / 还在启动，请稍等…");
    return;
  }

  const paths = [];
  const labels = [];
  for (const [index, file] of list.entries()) {
    const dot = file.name.lastIndexOf(".");
    const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
    const path = `/tmp/input-${index}${ext}`;
    pyodide.FS.writeFile(path, new Uint8Array(await file.arrayBuffer()));
    paths.push(path);
    labels.push(file.name);
  }

  const action = mode === "diff" ? "Comparing" : "Merging";
  const actionZh = mode === "diff" ? "正在对比" : "正在合并";
  setStatus(`${action} ${list.length} files… / ${actionZh} ${list.length} 个文件…`);
  pyodide.globals.set("_paths_json", JSON.stringify(paths));
  pyodide.globals.set("_labels_json", JSON.stringify(labels));
  pyodide.globals.set("_mode", mode);

  for (let attempt = 0; attempt < 6; attempt++) {
    const proxy = await pyodide.runPythonAsync(`
import json
_convert_paths(json.loads(_paths_json), _mode, json.loads(_labels_json))
`);
    const [kind, payload] = proxy.toJs();
    proxy.destroy();

    if (kind === "ok") {
      const name = mode === "diff" ? "comparison.html" : "merged.html";
      showResult(name, mode === "diff" ? "diff" : "merge", payload);
      setStatus(
        `${mode === "diff" ? "Compared" : "Merged"} ${list.length} files. / ` +
          `已${mode === "diff" ? "对比" : "合并"} ${list.length} 个文件。`,
      );
      return;
    }
    if (kind === "need") {
      setStatus(`Loading the ${payload} parser… / 正在加载 ${payload} 解析器…`);
      try {
        await installParser(payload);
        continue;
      } catch (err) {
        setStatus(parserLoadError(payload), true);
        return;
      }
    }
    setStatus("Could not convert these files: " + payload, true);
    window.__e2h.error = payload;
    return;
  }
  setStatus("Could not convert these files in the browser. / 浏览器里暂时无法转换这些文件。", true);
}

async function installParser(name) {
  if (installed.has(name)) return;
  for (const dep of PYODIDE_PACKAGE_DEPS[name] || []) {
    await pyodide.loadPackage(dep);
  }
  await micropip.install(name);
  installed.add(name);
}

function parserLoadError(name) {
  return (
    `This format needs the ${name} parser, which could not load in the browser. ` +
    `It works from the command line — see the GitHub repo. / ` +
    `此格式需要 ${name} 解析器，但浏览器里加载失败；CLI 版本可以处理。`
  );
}

function showResult(name, ext, html) {
  currentHtml = html;
  currentName = name;
  window.__e2h.lastHtml = html;
  window.__e2h.error = null;
  els.vName.textContent = name;
  els.vExt.textContent = ext;
  // Render defensively: a pathological document must never break the viewer.
  try {
    els.preview.removeAttribute("srcdoc");
    els.preview.srcdoc = html;
  } catch (err) {
    setStatus("Rendered as source (preview unavailable for this file).", true);
  }
  els.source.textContent = html;
  els.viewer.classList.add("show");
  showPreview(true);
}

function showPreview(preview) {
  els.preview.style.display = preview ? "block" : "none";
  els.source.style.display = preview ? "none" : "block";
  els.btnPreview.setAttribute("aria-pressed", String(preview));
  els.btnSource.setAttribute("aria-pressed", String(!preview));
}

async function handleFiles(files) {
  await convertFiles(files, currentMode);
}

function setMode(mode) {
  currentMode = mode;
  els.modeAuto.setAttribute("aria-pressed", String(mode === "auto"));
  els.modeDiff.setAttribute("aria-pressed", String(mode === "diff"));
}

els.dropzone.addEventListener("click", () => els.fileInput.click());
els.dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") els.fileInput.click();
});
els.fileInput.addEventListener("change", () => {
  if (els.fileInput.files.length) handleFiles(els.fileInput.files);
});

["dragenter", "dragover"].forEach((ev) =>
  els.dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    els.dropzone.classList.add("drag");
  }),
);
["dragleave", "drop"].forEach((ev) =>
  els.dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    els.dropzone.classList.remove("drag");
  }),
);
els.dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
});

document.querySelectorAll(".samples button").forEach((btn) =>
  btn.addEventListener("click", () => {
    if (btn.dataset.file) {
      loadSampleFile(btn.dataset.file);
      return;
    }
    const sample = SAMPLES[btn.dataset.sample];
    if (sample) convertBytes(sample.name, new TextEncoder().encode(sample.body));
  }),
);

els.modeAuto.addEventListener("click", () => setMode("auto"));
els.modeDiff.addEventListener("click", () => setMode("diff"));
els.btnPreview.addEventListener("click", () => showPreview(true));
els.btnSource.addEventListener("click", () => showPreview(false));

// Fullscreen the whole viewer (toolbar stays, so Esc/Exit/Preview all work).
els.btnFullscreen.addEventListener("click", () => {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else if (els.viewer.requestFullscreen) {
    showPreview(true);
    els.viewer.requestFullscreen().catch(() => {
      // Fallback: open the rendered HTML in a new tab.
      const blob = new Blob([currentHtml], { type: "text/html" });
      window.open(URL.createObjectURL(blob), "_blank");
    });
  } else {
    const blob = new Blob([currentHtml], { type: "text/html" });
    window.open(URL.createObjectURL(blob), "_blank");
  }
});
document.addEventListener("fullscreenchange", () => {
  const on = document.fullscreenElement === els.viewer;
  els.btnFullscreen.textContent = on ? "✕ Exit / 退出全屏" : "⛶ Fullscreen / 全屏";
});

els.btnDownload.addEventListener("click", () => {
  const blob = new Blob([currentHtml], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = currentName.replace(/\.[^.]+$/, "") + ".html";
  a.click();
  URL.revokeObjectURL(a.href);
});

window.__e2h.convertSample = (key) => {
  const sample = SAMPLES[key];
  return convertBytes(sample.name, new TextEncoder().encode(sample.body));
};
window.__e2h.convertFiles = convertFiles;
window.__e2h.setMode = setMode;

boot();
