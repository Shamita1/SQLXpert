"""Patch an existing SQLXpert folder with the temporary CSV/JSON/Excel workspace.
Run: python install_import_workspace.py C:\\path\\to\\SQLXpert
Creates timestamped .bak files before editing and is safe to re-run.
"""
from pathlib import Path
import shutil, sys, re

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
APP = ROOT / "app.py"
INDEX = ROOT / "templates" / "index.html"
JS = ROOT / "static" / "app.js"
CSS = ROOT / "static" / "style.css"
MODULE = ROOT / "modules" / "import_workspace.py"
for p in (APP, INDEX, JS, CSS):
    if not p.exists():
        raise SystemExit(f"Required SQLXpert file not found: {p}\nPass the root SQLXpert folder as the argument.")
if not MODULE.parent.exists():
    MODULE.parent.mkdir(parents=True)
source_module = Path(__file__).with_name("import_workspace.py")
if not source_module.exists():
    raise SystemExit("import_workspace.py must be beside this installer.")

# Back up each target before making any changes.
for path in (APP, INDEX, JS, CSS):
    backup = path.with_suffix(path.suffix + ".import-workspace.bak")
    if not backup.exists():
        shutil.copy2(path, backup)

app_text = APP.read_text(encoding="utf-8")
if "register_import_workspace" not in app_text:
    anchor = "app = Flask(__name__)"
    if anchor not in app_text:
        raise SystemExit("Could not locate app = Flask(__name__) in app.py; no app.py changes made.")
    app_text = app_text.replace(anchor, anchor + "\n\n# Temporary CSV/JSON/Excel import workspaces (read-only SQL).\nfrom modules.import_workspace import register_import_workspace\nregister_import_workspace(app)", 1)
    APP.write_text(app_text, encoding="utf-8")
shutil.copy2(source_module, MODULE)
requirements = ROOT / "requirements.txt"
if requirements.exists():
    req_text = requirements.read_text(encoding="utf-8")
    if not re.search(r"(?im)^openpyxl(?:[<=>~!].*)?$", req_text):
        requirements.write_text(req_text.rstrip() + "\nopenpyxl>=3.1\n", encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")
if 'id="import-dropzone"' not in html:
    anchor = '<section id="tab-workspace" class="tab-panel">'
    panel = '''<section id="tab-workspace" class="tab-panel">
        <div class="panel import-panel">
          <div class="panel-head"><div><span class="step-chip purple">NEW</span><strong>Zero-setup data workspace</strong><small>Drop a CSV, JSON, or Excel file and query it immediately—no CREATE TABLE scripts needed.</small></div><span class="tiny-badge">Temporary · read-only</span></div>
          <div id="import-dropzone" class="import-dropzone" tabindex="0" role="button" aria-label="Choose or drop a CSV, JSON, or Excel file">
            <input id="import-file-input" type="file" accept=".csv,.json,.xlsx,.xlsm" hidden>
            <div class="import-icon">⇧</div><strong>Drop your data file here</strong><p>or <span>browse files</span> · CSV, JSON, XLSX, XLSM · up to 15 MB</p>
          </div>
          <div id="import-feedback" class="import-feedback" aria-live="polite">Your uploaded file stays in a temporary workspace and is not added to sqlxpert.db.</div>
          <div id="import-schema" class="import-schema hidden"></div>
          <div id="import-actions" class="import-actions hidden"><button class="btn btn-primary" id="import-use-btn">Use this dataset in the SQL editor</button><button class="btn btn-secondary" id="import-clear-btn">Clear imported data</button><span class="import-mode-note">Run button targets the imported dataset while it is active.</span></div>
        </div>'''
    html = html.replace(anchor, panel, 1)
    INDEX.write_text(html, encoding="utf-8")

js = JS.read_text(encoding="utf-8")
if "let activeImportWorkspaceId" not in js:
    js = js.replace("let selectedChallenge = null;", "let selectedChallenge = null;\nlet activeImportWorkspaceId = null;\nlet activeImportTable = null;", 1)
    js = js.replace('''    const d = await post("/api/execute", {sql});''', '''    const d = activeImportWorkspaceId
      ? await post("/api/import-workspace/execute", {sql, workspace_id: activeImportWorkspaceId})
      : await post("/api/execute", {sql});''', 1)
    # The regular execute handler throws on API errors. Handle imported mode's {error} response consistently.
    js = js.replace('''    if (!d.success) throw new Error(d.error || "Query failed");''', '''    if (!d.success) throw new Error(d.error || "Query failed");''', 1)
    # Append feature wiring before initial startup calls.
    anchor = "updateLineCount();\nrefreshAll().catch"
    feature_js = r'''// Zero-setup CSV / JSON / Excel data workspace.
const importDropzone = $("import-dropzone");
const importInput = $("import-file-input");
if (importDropzone && importInput) {
  importDropzone.addEventListener("click", () => importInput.click());
  importDropzone.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); importInput.click(); }
  });
  importInput.addEventListener("change", () => { if (importInput.files[0]) uploadImportFile(importInput.files[0]); });
  ["dragenter", "dragover"].forEach(type => importDropzone.addEventListener(type, event => {
    event.preventDefault(); importDropzone.classList.add("drag-over");
  }));
  ["dragleave", "drop"].forEach(type => importDropzone.addEventListener(type, event => {
    event.preventDefault(); importDropzone.classList.remove("drag-over");
  }));
  importDropzone.addEventListener("drop", event => {
    const file = event.dataTransfer?.files?.[0];
    if (file) uploadImportFile(file);
  });
}

async function uploadImportFile(file) {
  const allowed = /\.(csv|json|xlsx|xlsm)$/i.test(file.name);
  if (!allowed) return showImportFeedback("Unsupported file type. Choose CSV, JSON, XLSX, or XLSM.", true);
  if (file.size > 15 * 1024 * 1024) return showImportFeedback("Maximum upload size is 15 MB.", true);
  showImportFeedback(`Importing ${file.name}…`, false);
  const form = new FormData(); form.append("file", file);
  try {
    const response = await fetch("/api/import-workspace/upload", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Import failed.");
    if (activeImportWorkspaceId) {
      post("/api/import-workspace/close", {workspace_id: activeImportWorkspaceId}).catch(() => {});
    }
    activeImportWorkspaceId = data.workspace_id;
    activeImportTable = data.table;
    $("import-actions").classList.remove("hidden");
    $("import-schema").classList.remove("hidden");
    $("import-schema").innerHTML = `<div class="import-schema-heading"><strong>${esc(data.table)}</strong><span>${Number(data.row_count).toLocaleString()} rows · ${data.column_count} columns</span></div>` +
      `<div class="import-column-list">${data.tables[0].columns.map(col => `<div><code>${esc(col.name)}</code><span>${esc(col.type)}</span></div>`).join("")}</div>`;
    showImportFeedback(`✓ ${data.filename} imported. ${data.message} Data is temporary and read-only.`, false);
    toast("Dataset ready to query.");
  } catch (error) {
    showImportFeedback(error.message, true);
  } finally {
    importInput.value = "";
  }
}

function showImportFeedback(message, bad) {
  const feedback = $("import-feedback");
  if (!feedback) return;
  feedback.className = "import-feedback" + (bad ? " import-error" : "");
  feedback.textContent = message;
}

$("import-use-btn")?.addEventListener("click", () => {
  if (!activeImportWorkspaceId || !activeImportTable) return;
  $("sql-editor").value = `SELECT *\nFROM "${activeImportTable}"\nLIMIT 100;`;
  updateLineCount();
  document.querySelector('[data-tab="workspace"]')?.click();
  toast("Editor is ready for your imported dataset.");
});

$("import-clear-btn")?.addEventListener("click", async () => {
  if (activeImportWorkspaceId) {
    try { await post("/api/import-workspace/close", {workspace_id: activeImportWorkspaceId}); } catch (_) {}
  }
  activeImportWorkspaceId = null;
  activeImportTable = null;
  $("import-actions").classList.add("hidden");
  $("import-schema").classList.add("hidden");
  $("import-schema").replaceChildren();
  showImportFeedback("Imported dataset cleared. Run now uses the normal SQLXpert demo database.", false);
  toast("Temporary dataset cleared.");
});

'''
    if anchor not in js:
        raise SystemExit("Could not find JavaScript startup anchor; app.js changes incomplete.")
    js = js.replace(anchor, feature_js + anchor, 1)
    # Keep diagnostics and query plans pointed at the active imported database.
    old_success = "    } else { await diagnoseQuery(); }\n    await loadStats();"
    new_success = "    } else if (activeImportWorkspaceId) { $(\"trace-area\").innerHTML = `<div class=\"trace-card\"><h4>Execution source</h4><p>Temporary imported dataset: ${esc(activeImportTable)}</p></div><div class=\"trace-card\"><h4>Query verified</h4><p>SQLite executed this SELECT against your uploaded data. Results are capped at 200 rows.</p></div>`; } else { await diagnoseQuery(); }\n    await loadStats();"
    js = js.replace(old_success, new_success, 1)
    old_error = '    await diagnoseQuery(); await loadStats();\n  }\n}\nasync function analyzeQuery()'
    new_error = '    if (activeImportWorkspaceId) { $("trace-area").innerHTML = `<div class="trace-card"><h4>Imported-data query error</h4><p>${esc(e.message)}</p></div><div class="trace-card"><h4>Next step</h4><p>Check the imported table and column names. The regular demo database is not used in this mode.</p></div>`; } else { await diagnoseQuery(); } await loadStats();\n  }\n}\nasync function analyzeQuery()'
    js = js.replace(old_error, new_error, 1)
    old_plan = '    const d = await post("/api/explain", {sql: currentSQL()});'
    new_plan = '    const d = activeImportWorkspaceId ? await post("/api/import-workspace/explain", {sql: currentSQL(), workspace_id: activeImportWorkspaceId}) : await post("/api/explain", {sql: currentSQL()});'
    js = js.replace(old_plan, new_plan, 1)
    JS.write_text(js, encoding="utf-8")

css = CSS.read_text(encoding="utf-8")
if ".import-dropzone" not in css:
    css += r'''

/* Zero-setup imported-data workspace */
.import-panel{margin-bottom:17px}.import-dropzone{margin:18px 18px 0;border:2px dashed #c8d2e7;border-radius:12px;background:linear-gradient(135deg,#fafbff,#f5f7ff);min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center;cursor:pointer;transition:border-color .15s,background .15s;outline:none}.import-dropzone:hover,.import-dropzone:focus,.import-dropzone.drag-over{border-color:#6678ec;background:#eef1ff}.import-dropzone strong{font-size:13px;color:#25304a}.import-dropzone p{font-size:11px;color:#8a94aa;margin:0}.import-dropzone p span{color:#5268e8;font-weight:700;text-decoration:underline}.import-icon{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;background:#e7eaff;color:#5268e8;font-size:24px}.import-feedback{margin:12px 18px;color:#718098;font-size:11px;line-height:1.6;overflow-wrap:anywhere}.import-feedback.import-error{color:#b84545;background:#fff0ef;padding:10px 12px;border-radius:7px}.import-schema{margin:0 18px 12px;border:1px solid #e4e9f3;border-radius:9px;overflow:hidden}.import-schema-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#f8f9fd;padding:11px 13px;font-size:11px}.import-schema-heading span{color:#8b95aa;font-size:10px}.import-column-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0}.import-column-list>div{display:flex;justify-content:space-between;gap:10px;padding:9px 12px;border-top:1px solid #edf0f5;font-size:10px}.import-column-list code{font-family:'DM Mono',monospace;color:#44516d;overflow-wrap:anywhere}.import-column-list span{color:#7e8a9f}.import-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:0 18px 17px}.import-mode-note{font-size:10px;color:#8b95aa}.hidden{display:none!important}@media(max-width:720px){.import-dropzone{margin:14px 14px 0;padding:16px}.import-schema-heading{align-items:flex-start;flex-direction:column}.import-actions{padding:0 14px 14px}}
'''
    CSS.write_text(css, encoding="utf-8")
print("SQLXpert import workspace installed.")
print(f"Project: {ROOT}")
print("Backups use the suffix .import-workspace.bak")
print("Install Excel support if needed: python -m pip install openpyxl")
