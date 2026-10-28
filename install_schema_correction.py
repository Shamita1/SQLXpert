from pathlib import Path
import re, shutil, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.') .resolve()
js = root / 'static' / 'app.js'
css = root / 'static' / 'style.css'
if not js.exists() or not css.exists():
    raise SystemExit('Could not find static/app.js and static/style.css. Run this from your SQLXpert project root.')
for p in (js, css):
    backup = p.with_name(p.name + '.schema-correction.bak')
    if not backup.exists(): shutil.copy2(p, backup)
source = js.read_text(encoding='utf-8')
if 'renderSchemaSuggestions' not in source:
    marker = '    showTraceCard("Lexer",'
    idx = source.find(marker)
    if idx < 0: raise SystemExit('Could not locate analyzeQuery() insertion point; no files were changed.')
    source = source[:idx] + '    await renderSchemaSuggestions(currentSQL(), d.schema || {});\n' + source[idx:]
    # add helper functions before showTraceCard
    marker2 = 'function showTraceCard(title, message) {'
    helper = r'''function schemaEditDistance(a, b) {
  a = a.toLowerCase(); b = b.toLowerCase();
  const row = Array.from({length: b.length + 1}, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let prev = row[0]; row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const old = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1));
      prev = old;
    }
  }
  return row[b.length];
}
async function renderSchemaSuggestions(sql, schema) {
  const area = $("diagnostics-area");
  if (!area || !schema || typeof schema !== "object") return;
  const tableNames = Object.keys(schema);
  const columns = [...new Set(Object.values(schema).flatMap(cols => (cols || []).map(c => c.name)))];
  const known = new Set([...tableNames, ...columns].map(x => x.toLowerCase()));
  const reserved = new Set(("SELECT FROM WHERE JOIN ON AS AND OR NOT NULL IS IN LIKE BETWEEN GROUP BY ORDER HAVING LIMIT OFFSET ASC DESC DISTINCT CASE WHEN THEN ELSE END COUNT SUM AVG MIN MAX CAST COALESCE CREATE TABLE INSERT INTO VALUES SET UPDATE DELETE TRUE FALSE INNER LEFT RIGHT OUTER UNION ALL EXPLAIN BY PRAGMA EXISTS WITH RECURSIVE COLLATE NOCASE ISNULL GLOB ESCAPE" ).split(/\s+/));
  // Tokenize identifiers while ignoring quoted strings and SQL comments.
  const cleaned = sql.replace(/--[^\n]*|\/\*[\s\S]*?\*\//g, " ").replace(/'(?:''|[^'])*'/g, " '' ");
  const identifiers = [...cleaned.matchAll(/[A-Za-z_][A-Za-z0-9_]*/g)].map(m => ({word:m[0], index:m.index}));
  const suggestions = [];
  for (const item of identifiers) {
    const word = item.word, lower = word.toLowerCase();
    if (reserved.has(word.toUpperCase()) || known.has(lower) || suggestions.some(s => s.word.toLowerCase() === lower)) continue;
    // Only suggest close schema matches; avoid noisy suggestions for aliases/ordinary expressions.
    const candidates = [...tableNames, ...columns].map(name => ({name, distance:schemaEditDistance(lower, name.toLowerCase())}))
      .filter(c => c.distance > 0 && c.distance <= Math.max(1, Math.floor(lower.length * 0.28)))
      .sort((a,b) => a.distance-b.distance);
    if (candidates.length && (!candidates[1] || candidates[1].distance > candidates[0].distance)) {
      suggestions.push({word, replacement:candidates[0].name, index:item.index});
    }
  }
  const old = document.getElementById("schema-suggestions");
  if (old) old.remove();
  if (!suggestions.length) return;
  const panel = document.createElement("div"); panel.id = "schema-suggestions"; panel.className = "schema-suggestions";
  panel.innerHTML = `<strong>Smart schema correction</strong><div class="schema-suggestion-list">${suggestions.slice(0,5).map((s,i)=>`<button type="button" class="schema-fix-chip" data-fix-index="${i}">Did you mean <code>${esc(s.replacement)}</code> instead of <code>${esc(s.word)}</code>? <span>Apply fix ↗</span></button>`).join("")}</div>`;
  area.appendChild(panel);
  panel.querySelectorAll("[data-fix-index]").forEach(btn => btn.addEventListener("click", () => {
    const s = suggestions[Number(btn.dataset.fixIndex)];
    const editor = $("sql-editor");
    // Replace only the exact identifier token, preserving the rest of the query.
    const re = new RegExp("(^|[^A-Za-z0-9_])" + s.word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "(?=$|[^A-Za-z0-9_])", "i");
    editor.value = editor.value.replace(re, (whole, prefix) => prefix + s.replacement);
    updateLineCount(); editor.focus(); toast(`Replaced ${s.word} with ${s.replacement}. Review and run the query.`);
    panel.remove();
  }));
}
'''
    if marker2 not in source: raise SystemExit('Could not locate helper insertion point; no files were changed.')
    source = source.replace(marker2, helper + marker2, 1)
    js.write_text(source, encoding='utf-8')
css_source = css.read_text(encoding='utf-8')
if '.schema-suggestions{' not in css_source:
    css_source += '''\n/* Smart Schema Correction chips */\n.schema-suggestions{margin:10px 0;padding:12px;border:1px solid #f0d6a8;background:#fffaf0;border-radius:8px;color:#80551c}.schema-suggestions>strong{display:block;font-size:11px;margin-bottom:8px}.schema-suggestion-list{display:flex;flex-wrap:wrap;gap:7px}.schema-fix-chip{border:1px solid #e8c98e;border-radius:7px;background:#fff;color:#73501b;padding:8px 10px;text-align:left;font:11px inherit;cursor:pointer}.schema-fix-chip:hover{background:#fff1d2;border-color:#dcae52}.schema-fix-chip code{font-family:'DM Mono',monospace;font-weight:700}.schema-fix-chip span{display:inline-block;margin-left:6px;color:#4c62d8;font-weight:700}\n'''
    css.write_text(css_source, encoding='utf-8')
print('Smart Schema Correction installed. Backups use *.schema-correction.bak')
