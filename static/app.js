const $ = (id) => document.getElementById(id);
let challenges = [];
let selectedChallenge = null;
let activeImportWorkspaceId = null;
let activeImportTable = null;

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("application/json")) {
    const responseText = await response.text();
    const hint = response.status === 404
      ? "The API route was not found. Stop Flask and restart it from the correct SQLXpert folder."
      : "Flask returned an HTML error page. Check the PowerShell terminal for the backend traceback.";
    throw new Error(`${hint} (HTTP ${response.status}; ${url})`);
  }

  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (HTTP ${response.status})`);
  return data;
}
function post(url, body) { return api(url, { method: "POST", body: JSON.stringify(body) }); }
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}
function toast(message) {
  const el = $("toast"); el.textContent = message; el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}
function currentSQL() { return $("sql-editor").value.trim(); }
function updateLineCount() {
  const n = $("sql-editor").value.split("\n").length;
  $("editor-count").textContent = `${n} line${n === 1 ? "" : "s"}`;
}
$("sql-editor").addEventListener("input", updateLineCount);
document.querySelectorAll(".nav").forEach(btn => btn.addEventListener("click", () => {
  document.querySelectorAll(".nav").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
  $("tab-" + btn.dataset.tab).classList.remove("hidden");
  const titles = {
  workspace: "SQL Workspace",
  compiler: "Compiler Trace",
  challenges: "SQL Challenges",
  "company-questions": "Company Questions",
  history: "Query History"
  };
  $("page-title").textContent = titles[btn.dataset.tab];
  if (btn.dataset.tab === "history") loadHistory();
  if (btn.dataset.tab === "challenges") loadChallenges();
}));




/* Schema panel tabs: Schema, Import, New table */
document.querySelectorAll("[data-schema-tab]").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll("[data-schema-tab]").forEach(tab => {
            tab.classList.remove("active");
        });

        button.classList.add("active");

        document.querySelectorAll(".schema-tab-content").forEach(view => {
            view.classList.add("hidden");
        });

        const selectedView = document.getElementById(
            button.dataset.schemaTab + "-view"
        );

        if (selectedView) {
            selectedView.classList.remove("hidden");
        }
    });
});


document.querySelectorAll("[data-query]").forEach(btn => btn.addEventListener("click", () => {
  $("sql-editor").value = btn.dataset.query; updateLineCount(); toast("Example loaded into editor.");
}));
$("reset-btn").addEventListener("click", () => {
  $("sql-editor").value = "SELECT name, department, marks\nFROM students\nWHERE marks >= 85\nORDER BY marks DESC;";
  updateLineCount(); toast("Editor reset.");
});
$("format-btn")?.addEventListener("click", () => {
  let sql = currentSQL().replace(/\s+/g, " ").replace(/\s*,\s*/g, ", ");
  ["SELECT","FROM","WHERE","JOIN","ON","GROUP BY","HAVING","ORDER BY","LIMIT","AND","OR"].forEach(word => {
    sql = sql.replace(new RegExp("\\\\b" + word.replace(" ","\\\\s+") + "\\\\b", "ig"), word);
  });
  sql = sql.replace(/\b(FROM|WHERE|JOIN|GROUP BY|HAVING|ORDER BY|LIMIT)\b/gi, "\n$1");
  $("sql-editor").value = sql.trim(); updateLineCount();
});
$("run-btn").addEventListener("click", runQuery);
$("analyze-btn")?.addEventListener("click", analyzeQuery);
$("compiler-analyze-btn").addEventListener("click", analyzeQuery);
$("explain-btn")?.addEventListener("click", explainPlan);
$("debug-btn").addEventListener("click", diagnoseQuery);
$("explain-query-btn").addEventListener("click", explainQuery);
$("generate-btn").addEventListener("click", generateSQL);
$("refresh-btn").addEventListener("click", refreshAll);
$("history-refresh-btn").addEventListener("click", loadHistory);
$("submit-challenge-btn").addEventListener("click", submitChallenge);
$("hint-btn").addEventListener("click", showHint);
$("next-challenge-btn").addEventListener("click", nextChallenge);
$("create-table-form").addEventListener("submit", createCustomTable);
$("insert-row-form").addEventListener("submit", insertCustomRow);
$("insert-table-name").addEventListener("change", updateInsertPlaceholder);

async function runQuery() {
  const sql = currentSQL(); if (!sql) return toast("Enter a SQL query first.");
  $("results-area").innerHTML = '<div class="loading">Executing query…</div>';
  try {
    const d = activeImportWorkspaceId
      ? await post("/api/import-workspace/execute", {sql, workspace_id: activeImportWorkspaceId})
      : await post("/api/execute", {sql});
    if (!d.success) throw new Error(d.error || "Query failed");
    const cols = d.columns;
    let html = `<div class="success-banner">✓ ${esc(d.message || "Query executed successfully.")} · ${d.duration_ms} ms${d.command === "SELECT" ? ` · ${d.row_count} row(s) returned` : ""}</div>`;
    if (d.command !== "SELECT") {
      html += `<div class="schema-note"><div><strong>${esc(d.command)} completed</strong><p>Use SELECT to inspect your table data. The schema panel has been refreshed.</p></div></div>`;
    } else if (!cols.length) html += '<div class="empty-state">Query returned no tabular columns.</div>';
    else {
      html += '<table class="data-table"><thead><tr>' + cols.map(c=>`<th>${esc(c)}</th>`).join("") + '</tr></thead><tbody>';
      html += d.rows.map(row=>'<tr>'+cols.map(c=>`<td>${esc(row[c] === null ? "NULL" : row[c])}</td>`).join("")+'</tr>').join("");
      html += '</tbody></table>';
      if (!d.rows.length) html += '<div class="empty-state">Query returned zero rows.</div>';
    }
    $("results-area").classList.remove("empty-state"); $("results-area").innerHTML = html;
    $("result-subtitle").textContent = "Database result";
    $("result-meta").textContent = d.command === "SELECT" ? `${d.row_count} rows · ${d.duration_ms} ms` : `${d.command} · ${d.duration_ms} ms`;
    if (d.command === "CREATE" || d.command === "INSERT") {
      await loadSchema();
      $("trace-area").innerHTML = `<div class="trace-card"><h4>${esc(d.command)} statement</h4><p>${esc(d.message || "Statement completed.")}</p></div><div class="trace-card"><h4>Next step</h4><p>Run a SELECT query to view the data in your table.</p></div>`;
    } else if (activeImportWorkspaceId) { $("trace-area").innerHTML = `<div class="trace-card"><h4>Execution source</h4><p>Temporary imported dataset: ${esc(activeImportTable)}</p></div><div class="trace-card"><h4>Query verified</h4><p>SQLite executed this SELECT against your uploaded data. Results are capped at 200 rows.</p></div>`; } else { await diagnoseQuery(); }
    await loadStats();
  } catch (e) {
    $("results-area").classList.remove("empty-state");
    $("results-area").innerHTML = `<div class="error-banner">✕ ${esc(e.message)}</div>`;
    $("result-subtitle").textContent = "Query failed"; $("result-meta").textContent = "";
    if (activeImportWorkspaceId) { $("trace-area").innerHTML = `<div class="trace-card"><h4>Imported-data query error</h4><p>${esc(e.message)}</p></div><div class="trace-card"><h4>Next step</h4><p>Check the imported table and column names. The regular demo database is not used in this mode.</p></div>`; } else { await diagnoseQuery(); } await loadStats();
  }
}
async function analyzeQuery() {
  try {
    const d = await post("/api/analyze", {sql: currentSQL()});
    const tokens = d.tokens || [];
    $("tokens-area").innerHTML = tokens.length
      ? '<table class="token-table"><thead><tr><th>Token</th><th>Type</th><th>Location</th></tr></thead><tbody>' +
        tokens.map(t=>`<tr><td>${esc(t.value)}</td><td class="token-type">${esc(t.type)}</td><td>${t.line}:${t.column}</td></tr>`).join("") + '</tbody></table>'
      : "No tokens generated.";
    renderAstTree(d.ast);
    $("diagnostics-area").innerHTML = d.diagnostics.length
      ? d.diagnostics.map(e=>`<div class="diagnostic-item"><strong>${esc(e.stage)}</strong> · ${esc(e.message)} <small>(${e.line}:${e.column})</small></div>`).join("")
      : '<div class="success-banner">✓ No errors found by the implemented lexer/parser checks.</div>';
    showTraceCard("Lexer", `${tokens.length} tokens identified. Tokens preserve the source location for each lexeme.`);
    showTraceCard("Parser / AST", d.ast ? `Statement type: ${d.ast.type}. Source table: ${d.ast.from || "not resolved"}. Clauses: ${(d.ast.clauses||[]).join(", ") || "none detected"}.` : "No AST generated.");
    showTraceCard("Diagnostics", d.diagnostics.length ? d.diagnostics[0].message : "No syntax issue detected by the prototype checks.");
    return d;
  } catch (e) { toast(e.message); }
}
function showTraceCard(title, message) {
  const area = $("trace-area");
  if (area.querySelector(".trace-placeholder")) area.innerHTML = "";
  area.insertAdjacentHTML("beforeend", `<div class="trace-card"><h4>${esc(title)}</h4><p>${esc(message)}</p></div>`);
}
async function diagnoseQuery() {
  try {
    const d = await post("/api/debug", {sql: currentSQL()});
    $("trace-area").innerHTML = `
      <div class="trace-card"><h4>Evidence source</h4><p>${esc(d.source)}</p></div>
      <div class="trace-card"><h4>Finding</h4><p>${esc(d.message)}</p></div>
      <div class="trace-card"><h4>Next step</h4><p>${esc(d.suggestion)}<br><br><code>${esc(d.confidence || "")}</code></p></div>`;
  } catch(e) { toast(e.message); }
}
async function explainPlan() {
  try {
    const d = activeImportWorkspaceId ? await post("/api/import-workspace/explain", {sql: currentSQL(), workspace_id: activeImportWorkspaceId}) : await post("/api/explain", {sql: currentSQL()});
    if (d.error) throw new Error(d.error);
    $("results-area").classList.remove("empty-state");
    $("results-area").innerHTML = `<div class="success-banner">Execution plan returned by SQLite.</div>` +
      d.plan.map((p,i)=>`<div class="trace-card" style="margin:10px"><h4>Plan node ${i+1}: ${esc(p.detail)}</h4><p>${esc(p.explanation)}</p></div>`).join("") +
      `<div class="schema-note"><div><strong>Interpretation note</strong><p>${esc(d.note)}</p></div></div>`;
    $("result-subtitle").textContent = "Database execution plan";
  } catch(e) { toast("Could not explain plan: " + e.message); }
}
async function explainQuery() {
  try {
    const d = await post("/api/explain-query", {sql: currentSQL()});
    $("trace-area").innerHTML = `<div class="trace-card"><h4>Query explanation</h4><p>${esc(d.explanation)}</p></div>
      <div class="trace-card"><h4>Structured representation</h4><p><code>${esc(JSON.stringify(d.ast || d.diagnostics || {}, null, 2))}</code></p></div>
      <div class="trace-card"><h4>Scope</h4><p>${esc(d.note || "The explanation is based on recognized SQL clauses.")}</p></div>`;
  } catch(e) { toast(e.message); }
}
async function generateSQL() {
  const prompt = window.prompt("Describe the data you want in plain English:", "Show CSE students and their marks, highest marks first");
  if (!prompt) return;
  try {
    const d = await post("/api/generate", {prompt});
    $("sql-editor").value = d.sql; updateLineCount();
    $("trace-area").innerHTML = `<div class="trace-card"><h4>Generated query</h4><p>${esc(d.sql)}</p></div>
      <div class="trace-card"><h4>Generation mode</h4><p>${esc(d.mode)}</p></div>
      <div class="trace-card"><h4>Important</h4><p>${esc(d.notice)}</p></div>`;
    toast("SQL draft generated. Review it, then run or analyze it.");
  } catch(e) { toast(e.message); }
}
async function loadSchema() {
  const d = await api("/api/schema");
  const schema = d.schema || {};
  const entries = Object.entries(schema);
  $("schema-count").textContent = `${entries.length} tables`;
  $("schema-list").innerHTML = entries.length ? entries.map(([name, cols]) => `
    <div class="schema-table"><div class="schema-table-head">${esc(name)} <span>${cols.length} columns</span></div>
    ${cols.map(c=>`<div class="schema-col"><span class="${c.pk ? "key-icon" : ""}">${c.pk ? "⚿" : "·"}</span>${esc(c.name)}<em>${esc(c.type || "ANY")}</em></div>`).join("")}</div>`).join("") : '<div class="schema-empty">No tables yet. Create your first table above.</div>';
  const select = $("insert-table-name");
  const previous = select.value;
  select.innerHTML = '<option value="">Choose a table…</option>' + entries.map(([name]) => `<option value="${esc(name)}">${esc(name)}</option>`).join("");
  if (entries.some(([name]) => name === previous)) select.value = previous;
  updateInsertPlaceholder();
}


function updateInsertPlaceholder() {
    const table = $("insert-table-name").value;

    $("insert-row-json").placeholder = table
        ? '{"id": 1, "name": "Priya"}'
        : "Choose a table first";
}


function showCustomFeedback(message, good=true) {
  $("custom-data-feedback").innerHTML = `<div class="feedback ${good ? "good" : "bad"}">${esc(message)}</div>`;
}
async function createCustomTable(event) {
  event.preventDefault();
  const table_name = $("new-table-name").value.trim();
  const columns = $("new-table-columns").value.trim();
  try {
    const d = await post("/api/create-table", {table_name, columns});
    if (!d.success) throw new Error(d.error || "Could not create table.");
    showCustomFeedback(d.message);
    $("new-table-name").value = ""; $("new-table-columns").value = "";
    await loadSchema(); $("insert-table-name").value = table_name; updateInsertPlaceholder();
    toast(d.message);
  } catch (e) { showCustomFeedback(e.message, false); }
}
async function insertCustomRow(event) {
  event.preventDefault();
  const table_name = $("insert-table-name").value;
  if (!table_name) return showCustomFeedback("Choose a table first.", false);
  let values;
  try { values = JSON.parse($("insert-row-json").value); }
  catch (_) { return showCustomFeedback('Enter valid JSON, for example: {"id": 1, "name": "Priya"}', false); }
  try {
    const d = await post("/api/insert-row", {table_name, values});
    if (!d.success) throw new Error(d.error || "Could not insert row.");
    showCustomFeedback(d.message); $("insert-row-json").value = "";
    toast(d.message);
    $("sql-editor").value = `SELECT * FROM ${table_name};`; updateLineCount();
    await runQuery(); await loadSchema();
  } catch (e) { showCustomFeedback(e.message, false); }
}
async function loadStats() {
  const d = await api("/api/stats");
  $("stat-queries").textContent = d.queries_run;
  $("stat-success").textContent = d.successful_queries;
  $("stat-solved").textContent = d.challenges_solved;
  $("stat-attempts").textContent = `${d.challenges_attempted} attempts`;
  $("stat-rate").textContent = `${d.query_success_rate}%`;
}
async function loadHistory() {
  const d = await api("/api/history");
  $("history-list").innerHTML = d.history.length ? d.history.map(h=>`
    <div class="history-item"><span class="status-pill ${h.status === "success" ? "success":"error"}">${esc(h.status)}</span>
    <div class="history-query"><code>${esc(h.query_text)}</code><small>${esc(h.created_at)} · ${h.duration_ms} ms ${h.error_text ? "· " + esc(h.error_text) : ""}</small></div>
    <button class="load-btn" data-load-query="${encodeURIComponent(h.query_text)}">Load query</button></div>`).join("") : '<div class="empty-state">No queries recorded yet. Run a query to create history.</div>';
  document.querySelectorAll("[data-load-query]").forEach(btn=>btn.addEventListener("click",()=>{
    $("sql-editor").value=decodeURIComponent(btn.dataset.loadQuery); updateLineCount();
    document.querySelector('[data-tab="workspace"]').click(); toast("Query loaded from history.");
  }));
}
async function loadChallenges() {
    const d = await api("/api/challenges");
    challenges = d.challenges;
    // Show only the current challenge, not the full question list.
    $("challenge-list").innerHTML = "";
    
    if (!challenges.length) {
        $("challenge-title").textContent = "No challenges available";
        $("challenge-description").textContent = "";
        return;
    }
    
    if (!selectedChallenge || !challenges.some(c => c.id === selectedChallenge)) {
        selectChallenge(challenges[0].id, false);
    } else {
        selectChallenge(selectedChallenge, false);
    }
}

function selectChallenge(id, rerender = true) {
  selectedChallenge = id;

  const c = challenges.find(x => x.id === id);
  if (!c) return;

  $("challenge-title").textContent = c.title;
  $("challenge-description").textContent = c.description;
  $("challenge-feedback").innerHTML = "";

  // Start with an empty editor instead of a prefilled answer.
  $("challenge-editor").value = "";

  if (rerender) {
    document.querySelectorAll("[data-challenge]").forEach(el => {
      el.classList.toggle(
        "selected",
        Number(el.dataset.challenge) === id
      );
    });
  }
}


function nextChallenge() {
  if (!challenges.length) return;

  const currentIndex = challenges.findIndex(
    c => c.id === selectedChallenge
  );

  const nextIndex = (currentIndex + 1) % challenges.length;

  selectChallenge(challenges[nextIndex].id);
}


function showHint() {
  const c=challenges.find(x=>x.id===selectedChallenge); if(!c)return;
  $("challenge-feedback").innerHTML=`<div class="feedback bad">Hint: ${esc(c.hint)}</div>`;
}
async function submitChallenge() {
  if (!selectedChallenge) return toast("Choose a challenge first.");
  try {
    const d=await post("/api/challenges/submit",{challenge_id:selectedChallenge,sql:$("challenge-editor").value});
    $("challenge-feedback").innerHTML=`<div class="feedback ${d.correct?"good":"bad"}">${esc(d.message || d.error)}${d.hint?"<br>Hint: "+esc(d.hint):""}</div>`;
    await loadStats();
  } catch(e) { $("challenge-feedback").innerHTML=`<div class="feedback bad">${esc(e.message)}</div>`; }
}
async function refreshAll() {
  try { await Promise.all([loadSchema(),loadStats()]); toast("Dashboard refreshed."); }
  catch(e) { toast("Refresh failed: "+e.message); }
}
// Zero-setup CSV / JSON / Excel data workspace.
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

updateLineCount();
refreshAll().catch(e=>toast("Could not connect to backend. Start the Flask server first."));




function renderAstTree(ast) {
    const container = document.getElementById("ast-area");
    if (!container) return;

    container.replaceChildren();

    if (!ast || typeof ast !== "object") {
        container.textContent = "No AST available. Analyze a SQL query first.";
        return;
    }

    // Build a readable tree node.
    function node(label, children = [], kind = "branch") {
        return { label, children, kind };
    }

    function leaf(label) {
        return node(String(label), [], "leaf");
    }

    // Your backend returns SELECT, FROM and clauses as separate fields.
    let treeData;

    if (ast.type === "SelectStatement") {
        const selectChildren = (ast.select || [])
            .filter(value => value !== ",")
            .map(leaf);

        const fromChildren = (ast.tables || []).length
            ? ast.tables.map(table =>
                node(table.name || String(table), [
                    ...(table.alias && table.alias !== table.name
                        ? [leaf("Alias: " + table.alias)]
                        : [])
                ], "leaf"))
            : [leaf(ast.from || "Unknown table")];

        const clauseChildren = [];

        const clauses = ast.clauses || {};

        if (clauses.WHERE) {
            clauseChildren.push(
                node("WHERE", [
                    node("Condition", clauses.WHERE.map(leaf), "expression")
                ], "clause")
            );
        }

        if (clauses.GROUP) {
            clauseChildren.push(
                node("GROUP BY", clauses.GROUP.filter(v => v !== ",").map(leaf), "clause")
            );
        }

        if (clauses.HAVING) {
            clauseChildren.push(
                node("HAVING", clauses.HAVING.map(leaf), "clause")
            );
        }

        if (clauses.ORDER) {
            clauseChildren.push(
                node("ORDER BY", clauses.ORDER.filter(v => v !== ",").map(leaf), "clause")
            );
        }

        if (clauses.LIMIT) {
            clauseChildren.push(
                node("LIMIT", clauses.LIMIT.map(leaf), "clause")
            );
        }

        if (clauses.OFFSET) {
            clauseChildren.push(
                node("OFFSET", clauses.OFFSET.map(leaf), "clause")
            );
        }

        treeData = node("SELECT Query", [
            node("SELECT", selectChildren, "clause"),
            node("FROM", fromChildren, "clause"),
            ...clauseChildren
        ], "root");
    } else if (ast.type === "CreateTableStatement") {
        treeData = node("CREATE TABLE", [
            leaf(ast.table || "Unknown table"),
            node("Columns", (ast.columns || []).map(column =>
                node(column.name, (column.definition || []).map(leaf), "leaf")
            ))
        ], "root");
    } else if (ast.type === "InsertStatement") {
        treeData = node("INSERT Statement", [
            node("INTO", [leaf(ast.table || "Unknown table")], "clause"),
            node("Columns", (ast.columns || []).map(leaf), "clause"),
            node("VALUES", (ast.values || []).flat().map(leaf), "clause")
        ], "root");
    } else {
        treeData = node(ast.type || "Query", Object.entries(ast).map(([key, value]) =>
            node(key, Array.isArray(value)
                ? value.map(item => typeof item === "object" && item !== null
                    ? node(item.name || item.type || "Item", Object.entries(item).map(([k, v]) =>
                        node(k, Array.isArray(v) ? v.map(leaf) : [leaf(v)])
                    ))
                    : leaf(item))
                : value && typeof value === "object"
                    ? Object.entries(value).map(([k, v]) => node(k, Array.isArray(v) ? v.map(leaf) : [leaf(v)]))
                    : [leaf(value)])
        ), "root");
    }

    // Render the tree using nested lists and connector styling.
    function renderNode(item) {
        const li = document.createElement("li");
        li.className = "ast-item";

        const label = document.createElement("span");
        label.className = "ast-label ast-" + item.kind;
        label.textContent = item.label;
        li.appendChild(label);

        if (item.children && item.children.length) {
            const ul = document.createElement("ul");
            ul.className = "ast-children";

            item.children.forEach(child => ul.appendChild(renderNode(child)));
            li.appendChild(ul);
        }

        return li;
    }

    const tree = document.createElement("ul");
    tree.className = "ast-tree-root";
    tree.appendChild(renderNode(treeData));

    container.classList.add("ast-visual");
    container.appendChild(tree);
}



// Add this to static/app.js
document.addEventListener('DOMContentLoaded', () => {
    const challengesNavBtn = document.querySelector('[data-tab="challenges"]');
    if (challengesNavBtn) {
        challengesNavBtn.addEventListener('click', () => {
            // Call our campaign loader when the tab is opened
            if (typeof loadCampaignData === 'function') {
                loadCampaignData();
            }
        });
    }
});


// --- CAMPAIGN & ARENA MODULE LOGIC ---

// Declare state variables at the very top to prevent temporal dead zone errors
let activeChallengeId = null;
let activeIsPlSql = false;

document.addEventListener('DOMContentLoaded', () => {
    // Auto-load campaign data on startup so it doesn't say "Loading chapters..."
    loadCampaignData();
});

function switchChallengeMode(mode) {
    const classicMode = document.getElementById('mode-classic-challenges');
    const campaignMode = document.getElementById('mode-campaign-arena');
    
    if (mode === 'classic') {
        if (classicMode) classicMode.style.display = 'block';
        if (campaignMode) campaignMode.style.display = 'none';
    } else {
        if (classicMode) classicMode.style.display = 'none';
        if (campaignMode) campaignMode.style.display = 'block';
        switchChallengeTab(mode === 'store' ? 'store' : 'campaign');
    }
}

function switchChallengeTab(tabName) {
    document.querySelectorAll('.challenge-subview').forEach(el => el.style.display = 'none');
    
    const btnCamp = document.getElementById('btn-sub-campaign');
    const btnArena = document.getElementById('btn-sub-arena');
    const btnStore = document.getElementById('btn-sub-store');
    
    if (btnCamp) btnCamp.className = 'btn ' + (tabName === 'campaign' ? 'btn-primary' : 'btn-secondary');
    if (btnArena) btnArena.className = 'btn ' + (tabName === 'arena' ? 'btn-primary' : 'btn-secondary');
    if (btnStore) btnStore.className = 'btn ' + (tabName === 'store' ? 'btn-primary' : 'btn-secondary');

    const targetSubview = document.getElementById('subview-' + tabName);
    if (targetSubview) targetSubview.style.display = 'block';
}

async function loadCampaignData() {
    try {
        const res = await fetch('/api/campaign/data');
        const data = await res.json();
        
        const coinNav = document.getElementById('nav-coins');
        if (coinNav && data.profile) coinNav.textContent = data.profile.coins;
        
        // Render chapters cleanly matching SQLXpert theme
        const container = document.getElementById('campaign-chapters-container');
        if (container && data.chapters) {
            let html = '';
            data.chapters.forEach(chap => {
                html += `
                <div style="background: var(--bg-surface, #ffffff); border: 1px solid var(--border-color, #e2e8f0); padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <h4 style="font-size: 1rem; font-weight: 600; color: var(--text-main, #0f172a);">Chapter ${chap.id}: ${chap.title}</h4>
                        <span style="font-size: 0.75rem; background: #e0e7ff; color: #4338ca; padding: 3px 8px; border-radius: 9999px; font-weight: 600;">Chapter ${chap.id}</span>
                    </div>
                    <p style="color: var(--text-muted, #64748b); font-size: 0.875rem; margin-bottom: 16px;">${chap.description}</p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px;">`;
                
                chap.challenges.forEach(chal => {
                    html += `
                    <button class="btn btn-secondary" style="text-align: left; display: flex; flex-direction: column; align-items: flex-start; padding: 12px; height: auto;" onclick="openArena('${chal.id}', '${chal.title.replace(/'/g, "\\'")}', '${chal.prompt.replace(/'/g, "\\'")}', ${chal.time_limit}, ${chal.is_plsql || false})">
                        <strong style="font-size: 0.85rem; color: var(--text-main, #0f172a);">⚡ ${chal.title}</strong>
                        <small style="color: var(--text-muted, #64748b); margin-top: 2px;">Difficulty: ${chal.difficulty}</small>
                    </button>`;
                });
                
                html += `</div></div>`;
            });
            container.innerHTML = html;
        }

        // Render store items
        const storeContainer = document.getElementById('store-items-container');
        if (storeContainer && data.shop_items) {
            let storeHtml = '';
            data.shop_items.forEach(item => {
                storeHtml += `
                <div style="background: var(--bg-surface, #ffffff); border: 1px solid var(--border-color, #e2e8f0); padding: 20px; border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div>
                        <h4 style="font-size: 1rem; font-weight: 600; color: var(--text-main, #0f172a); margin-bottom: 6px;">${item.name}</h4>
                        <p style="color: var(--text-muted, #64748b); font-size: 0.85rem; line-height: 1.4;">${item.description}</p>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px; border-top: 1px solid var(--border-color, #f1f5f9); pt-3;">
                        <span style="color: #d97706; font-weight: 700; font-size: 0.95rem;">${item.cost} 🪙</span>
                        <button class="btn btn-primary" style="font-size: 0.8rem; padding: 6px 14px;" onclick="buyShopItem('${item.item_id}')">Purchase</button>
                    </div>
                </div>`;
            });
            storeContainer.innerHTML = storeHtml;
        }
    } catch (e) {
        console.error("Failed loading campaign data:", e);
    }
}

function openArena(id, title, prompt, timeLimit, isPlSql) {
    activeChallengeId = id;
    activeIsPlSql = isPlSql;
    
    document.getElementById('arena-challenge-title').textContent = title;
    document.getElementById('arena-challenge-prompt').textContent = prompt;
    
    const editor = document.getElementById('arena-editor-textarea');
    if (editor) {
        editor.value = isPlSql ? 
            "DECLARE\nBEGIN\n  -- Write your PL/SQL procedural block here\n  DBMS_OUTPUT.PUT_LINE('Executing PL/SQL...');\nEND;" : 
            "SELECT * FROM students;";
    }
    
    switchChallengeTab('arena');
}

async function runArenaCode() {
    const code = document.getElementById('arena-editor-textarea').value;
    const logBox = document.getElementById('arena-console-log');
    logBox.textContent = "Executing query against engine...";

    try {
        const res = await fetch('/api/campaign/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, is_plsql: activeIsPlSql })
        });
        const data = await res.json();
        
        if (data.success) {
            logBox.style.color = "#4ade80";
            let txt = (data.output || []).join('\n');
            if (data.rows && data.rows.length > 0) {
                txt += `\n\nReturned ${data.rows.length} row(s):\n` + JSON.stringify(data.rows.slice(0, 3), null, 2);
            }
            logBox.textContent = txt;
        } else {
            logBox.style.color = "#f87171";
            logBox.textContent = "Execution Error:\n" + (data.output || []).join('\n');
        }
    } catch (err) {
        logBox.style.color = "#f87171";
        logBox.textContent = "Server communication error: " + err.message;
    }
}

async function submitArenaCode() {
    if (!activeChallengeId) {
        alert("Please select a challenge from the Campaign Map first.");
        return;
    }
    
    try {
        const res = await fetch('/api/campaign/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ challenge_id: activeChallengeId, time_remaining: 120, total_time: 300 })
        });
        const data = await res.json();
        if (data.success) {
            alert("🎉 " + data.message);
            loadCampaignData();
            switchChallengeTab('campaign');
        }
    } catch (err) {
        alert("Submission failed: " + err.message);
    }
}

async function buyShopItem(itemId) {
    try {
        const res = await fetch('/api/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            alert("🛍️ " + data.message);
            loadCampaignData();
        } else {
            alert("❌ " + (data.error || "Purchase failed"));
        }
    } catch (err) {
        alert("Transaction error: " + err.message);
    }
}


/* =========================================
   COMPANY QUESTIONS
   ========================================= */

function initCompanyQuestions() {
    const list = document.getElementById("company-question-list");

    // Do not initialize twice.
    if (!list || list.dataset.ready === "true") return;
    list.dataset.ready = "true";

    const search = document.getElementById("company-search");
    const company = document.getElementById("company-filter");
    const difficulty = document.getElementById("difficulty-filter");
    const topic = document.getElementById("topic-filter");
    const detail = document.getElementById("company-question-detail");
    const count = document.getElementById("company-question-count");

    const detailTitle = document.getElementById("company-detail-title");
    const detailMeta = document.getElementById("company-detail-meta");
    const detailDescription = document.getElementById("company-detail-description");
    const detailSchema = document.getElementById("company-detail-schema");
    const solutionCode = document.getElementById("company-solution-code");
    const answerInput = document.getElementById("company-sql-answer");
    const answerFeedback = document.getElementById("company-answer-feedback");

    // Check that the question data file loaded.
    if (typeof companyQuestions === "undefined") {
        list.innerHTML = `
            <div class="panel company-no-results">
                Question data did not load. Check the company_questions_data.js
                file and the script paths in index.html.
            </div>`;
        console.error("companyQuestions is not defined.");
        return;
    }

    const escapeHTML = value =>
        String(value ?? "").replace(/[&<>"']/g, ch => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[ch]);

    // Populate topics from the question data.
    const topics = [...new Set(companyQuestions.map(q => q.topic))].sort();

    topic.innerHTML = '<option value="">All topics</option>';

    topics.forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        topic.appendChild(option);
    });

    function renderQuestions() {
        const query = search.value.trim().toLowerCase();

        const filtered = companyQuestions.filter(q => {
            const searchableText =
                `${q.title} ${q.company} ${q.topic} ${q.description}`.toLowerCase();

            return searchableText.includes(query)
                && (!company.value || q.company === company.value)
                && (!difficulty.value || q.difficulty === difficulty.value)
                && (!topic.value || q.topic === topic.value);
        });

        count.textContent = filtered.length;

        if (filtered.length === 0) {
            list.innerHTML = `
                <div class="panel company-no-results">
                    No questions match these filters. Try changing your filters.
                </div>`;
            return;
        }

        list.innerHTML = filtered.map(q => `
            <article class="panel company-question-card">
                <div class="company-card-tags">
                    <span class="company-tag">${escapeHTML(q.company)}</span>
                    <span class="difficulty-tag ${escapeHTML(q.difficulty.toLowerCase())}">
                        ${escapeHTML(q.difficulty)}
                    </span>
                </div>

                <h3>${escapeHTML(q.title)}</h3>
                <p>${escapeHTML(q.description)}</p>

                <div class="company-card-bottom">
                    <span>${escapeHTML(q.topic)}</span>
                    <button
                        type="button"
                        class="btn btn-secondary"
                        data-open-question="${q.id}">
                        View question →
                    </button>
                </div>
            </article>
        `).join("");
    }

    // Open a question. Event delegation keeps working after filtering.
    list.addEventListener("click", event => {
        const button = event.target.closest("[data-open-question]");
        if (!button) return;

        const question = companyQuestions.find(
            q => q.id === Number(button.dataset.openQuestion)
        );

        if (!question) return;

        detailTitle.textContent = question.title;
        detailTitle.dataset.questionId = question.id;
        detailMeta.textContent =
            `${question.company} · ${question.difficulty} · ${question.topic}`;
        detailDescription.textContent = question.description;
        detailSchema.textContent = question.schema;
        solutionCode.textContent = question.solution;

        answerInput.value = "";
        answerFeedback.textContent = "";
        answerFeedback.className = "hidden";
        solutionCode.classList.add("hidden");

        detail.classList.remove("hidden");
        list.classList.add("hidden");
    });

    // Search and filter controls.
    [search, company, difficulty, topic].forEach(control => {
        control.addEventListener("input", renderQuestions);
        control.addEventListener("change", renderQuestions);
    });

    // Return to the question list.
    document.getElementById("company-detail-close").addEventListener("click", () => {
        detail.classList.add("hidden");
        list.classList.remove("hidden");
    });

    // Reveal or hide the sample solution.
    document.getElementById("company-show-solution").addEventListener("click", () => {
        solutionCode.classList.toggle("hidden");
    });

    // Check the submitted SQL against the sample solution.
    document.getElementById("company-check-answer").addEventListener("click", () => {
        const answer = answerInput.value.trim();
        const questionId = Number(detailTitle.dataset.questionId);
        const question = companyQuestions.find(q => q.id === questionId);

        answerFeedback.className = "";

        if (!answer) {
            answerFeedback.classList.add("answer-incorrect");
            answerFeedback.textContent = "Write your SQL query before checking your answer.";
            return;
        }

        if (!question) {
            answerFeedback.classList.add("answer-incorrect");
            answerFeedback.textContent = "Could not find this question. Please reopen it.";
            return;
        }

        const normalizeSQL = sql =>
            sql.trim().replace(/;+$/, "").replace(/\s+/g, " ").toLowerCase();

        if (normalizeSQL(answer) === normalizeSQL(question.solution)) {
            answerFeedback.classList.add("answer-correct");
            answerFeedback.textContent =
                "Correct! Your query matches the sample solution.";
        } else {
            answerFeedback.classList.add("answer-incorrect");
            answerFeedback.textContent =
                "Your query does not exactly match the sample solution. " +
                "Equivalent SQL can be written in different ways, so compare the logic too.";
        }
    });

    // Clear the answer field.
    document.getElementById("company-clear-answer").addEventListener("click", () => {
        answerInput.value = "";
        answerFeedback.className = "hidden";
        answerFeedback.textContent = "";
    });

    // Display all questions initially.
    renderQuestions();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCompanyQuestions);
} else {
    initCompanyQuestions();
}




