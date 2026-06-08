/* everythingtohtml — in-browser universal reader, powered by Pyodide.
 *
 * Everything runs client-side: we load a CPython runtime (Pyodide) in WebAssembly,
 * pip-install the everythingtohtml wheel into it, and call the same conversion
 * engine the CLI uses. No file ever leaves the page.
 */

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

// Optional-dependency extras -> the PyPI package micropip should install on demand.
const EXTRA_PACKAGE = {
  docx: "mammoth",
  xlsx: "openpyxl",
  pptx: "python-pptx",
  pdf: "pdfminer.six",
  yaml: "PyYAML",
  rst: "docutils",
  doc: "olefile",
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
  btnDownload: document.getElementById("btn-download"),
};

let pyodide = null;
let micropip = null;
const installed = new Set();
let currentHtml = "";
let currentName = "result";

// Test/automation hooks.
window.__e2h = { ready: false, lastHtml: null, error: null };

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("err", isError);
}

async function boot() {
  try {
    setStatus("Loading the in-browser Python runtime…");
    const mod = await import(PYODIDE_URL + "pyodide.mjs");
    pyodide = await mod.loadPyodide({ indexURL: PYODIDE_URL });

    setStatus("Installing the converters…");
    await pyodide.loadPackage("micropip");
    micropip = pyodide.pyimport("micropip");

    const wheelURL = new URL("wheels/everythingtohtml-0.1.0-py3-none-any.whl", location.href).href;
    await micropip.install(wheelURL);

    await pyodide.runPythonAsync(`
from everythingtohtml import EverythingToHtml
from everythingtohtml._exceptions import MissingDependencyException

_eth = EverythingToHtml()
_EXTRA_PKG = ${JSON.stringify(EXTRA_PACKAGE).replace(/"/g, "'")}

def _convert_path(path):
    try:
        return ['ok', _eth.convert(path).html]
    except MissingDependencyException as exc:
        msg = str(exc)
        for extra, pkg in _EXTRA_PKG.items():
            if '[' + extra + ']' in msg:
                return ['need', pkg]
        return ['error', msg]
    except Exception as exc:
        return ['error', f'{type(exc).__name__}: {exc}']
`);

    setStatus("Ready — drop a file to read it.");
    window.__e2h.ready = true;
  } catch (err) {
    setStatus("Failed to start the in-browser runtime: " + err.message, true);
    window.__e2h.error = String(err);
    throw err;
  }
}

async function convertBytes(name, bytes) {
  if (!pyodide) {
    setStatus("Still starting up — one moment…");
    return;
  }
  currentName = name;
  const dot = name.lastIndexOf(".");
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  const path = "/tmp/input" + ext;

  setStatus(`Converting ${name}…`);
  pyodide.FS.writeFile(path, bytes);
  pyodide.globals.set("_p", path);

  for (let attempt = 0; attempt < 4; attempt++) {
    const proxy = await pyodide.runPythonAsync("_convert_path(_p)");
    const [kind, payload] = proxy.toJs();
    proxy.destroy();

    if (kind === "ok") {
      showResult(name, ext || "—", payload);
      setStatus(`Converted ${name}.`);
      return;
    }
    if (kind === "need") {
      if (installed.has(payload)) break;
      setStatus(`Loading the ${payload} parser (first use)…`);
      try {
        await micropip.install(payload);
        installed.add(payload);
        continue;
      } catch (err) {
        setStatus(
          `This format needs the “${payload}” parser, which couldn’t load in the ` +
            `browser. It works from the command line — see the GitHub repo.`,
          true,
        );
        return;
      }
    }
    setStatus("Could not convert this file: " + payload, true);
    window.__e2h.error = payload;
    return;
  }
  setStatus("Could not convert this file in the browser.", true);
}

function showResult(name, ext, html) {
  currentHtml = html;
  window.__e2h.lastHtml = html;
  els.vName.textContent = name;
  els.vExt.textContent = ext;
  els.preview.srcdoc = html;
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

async function handleFile(file) {
  const buf = new Uint8Array(await file.arrayBuffer());
  await convertBytes(file.name, buf);
}

// -- wiring ---------------------------------------------------------------

els.dropzone.addEventListener("click", () => els.fileInput.click());
els.dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") els.fileInput.click();
});
els.fileInput.addEventListener("change", () => {
  if (els.fileInput.files[0]) handleFile(els.fileInput.files[0]);
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
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

document.querySelectorAll(".samples button").forEach((btn) =>
  btn.addEventListener("click", () => {
    const sample = SAMPLES[btn.dataset.sample];
    if (sample) convertBytes(sample.name, new TextEncoder().encode(sample.body));
  }),
);

els.btnPreview.addEventListener("click", () => showPreview(true));
els.btnSource.addEventListener("click", () => showPreview(false));
els.btnDownload.addEventListener("click", () => {
  const blob = new Blob([currentHtml], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = currentName.replace(/\.[^.]+$/, "") + ".html";
  a.click();
  URL.revokeObjectURL(a.href);
});

// Expose for automated testing.
window.__e2h.convertSample = (key) => {
  const s = SAMPLES[key];
  return convertBytes(s.name, new TextEncoder().encode(s.body));
};

boot();
