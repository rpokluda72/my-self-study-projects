"""Generate static HTML preview pages for Java source files."""
import html
from pathlib import Path

BASE = Path(__file__).parent.parent / "src" / "test"
OUT = Path(__file__).parent

FOLDERS = [
    ("root", "", "Root"),
    ("arrays", "arrays", "Arrays"),
    ("comparator", "comparator", "Comparator"),
    ("employee", "employee", "Employee"),
    ("equals", "equals", "Equals"),
    ("functional_interfaces", "functional_interfaces", "Functional Interfaces"),
    ("hash_set", "hash_set", "Hash Set"),
    ("lambda", "lambda", "Lambda"),
    ("list", "list", "List"),
    ("mkyong", "mkyong", "Mkyong"),
    ("obrazce", "obrazce", "Obrazce"),
    ("optional", "optional", "Optional"),
    ("rozhrani", "rozhrani", "Rozhrani"),
    ("stream", "stream", "Stream"),
]

HLJS_HEAD = """  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>"""

PAGE_CSS = """  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    html, body { height: 100%; overflow: hidden; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f0f2f5;
      display: flex; flex-direction: column;
    }

    /* ── sticky header panel ── */
    #page-header {
      flex-shrink: 0;
      background: #f0f2f5;
      padding: 16px 20px 10px;
      border-bottom: 1px solid #e2e8f0;
      box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    h1 { color: #2d3748; margin-bottom: 10px; font-size: 1.3rem; }

    /* ── toolbar (show/collapse all) ── */
    .toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
    .toolbar button {
      padding: 5px 13px; border: none; border-radius: 5px; cursor: pointer;
      font-size: 0.82rem; font-weight: 600; transition: background 0.15s;
    }
    .btn-show { background: #3182ce; color: #fff; }
    .btn-show:hover { background: #2b6cb0; }
    .btn-hide { background: #718096; color: #fff; }
    .btn-hide:hover { background: #4a5568; }
    .match-info { font-size: 0.82rem; color: #718096; margin-left: 4px; }

    /* ── page search bar ── */
    .page-search-bar {
      display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
      background: #fff; border: 1px solid #cbd5e0; border-radius: 7px;
      padding: 6px 12px;
    }
    .page-search-bar input {
      flex: 1; min-width: 160px; padding: 5px 8px;
      border: 1px solid #cbd5e0; border-radius: 5px;
      font-size: 0.85rem; outline: none; color: #2d3748;
    }
    .page-search-bar input:focus { border-color: #63b3ed; }
    .psb-btn {
      padding: 5px 11px; border: 1px solid #cbd5e0; border-radius: 5px;
      background: #f7fafc; cursor: pointer; font-size: 0.8rem;
      color: #4a5568; transition: background 0.12s;
    }
    .psb-btn:hover { background: #e2e8f0; }
    .psb-btn:disabled { opacity: 0.4; cursor: default; }
    .psb-clear {
      padding: 5px 9px; border: 1px solid #cbd5e0; border-radius: 5px;
      background: #f7fafc; cursor: pointer; font-size: 0.85rem;
      color: #718096; transition: background 0.12s;
    }
    .psb-clear:hover { background: #fed7d7; color: #c53030; border-color: #fc8181; }
    .psb-count { font-size: 0.8rem; color: #718096; white-space: nowrap; min-width: 60px; }

    /* ── highlight marks ── */
    mark.sh { background: #fef08a; color: inherit; border-radius: 2px; padding: 0 1px; }
    mark.sh-current { background: #f97316; color: #fff; border-radius: 2px; padding: 0 1px; }

    /* ── scrollable cards area ── */
    #cards-container {
      flex: 1; overflow-y: auto;
      padding: 20px;
    }

    .card { background: #fff; border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
    .card.hidden-by-search { display: none; }

    .card-header {
      background: #2d3748; color: #e2e8f0;
      padding: 9px 14px;
      display: flex; align-items: center; gap: 10px; cursor: pointer;
      user-select: none;
    }
    .card-header:hover { background: #3a4a5c; }
    .card-header .filename { font-size: 0.9rem; font-weight: 700; flex: 1; }
    .card-header .path { color: #a0aec0; font-size: 0.78rem; }
    .card-header .toggle-btn {
      background: none; border: 1px solid #4a5568; border-radius: 4px;
      color: #a0aec0; font-size: 0.75rem; padding: 2px 8px; cursor: pointer;
      white-space: nowrap; flex-shrink: 0;
    }
    .card-header .toggle-btn:hover { border-color: #63b3ed; color: #63b3ed; }

    .card-body { display: block; }
    .card-body.collapsed { display: none; }

    pre { margin: 0; overflow-x: auto; }
    pre code.hljs { font-size: 13px; line-height: 1.5; padding: 16px !important; }
  </style>"""

PAGE_JS = """  <script>
    document.addEventListener('DOMContentLoaded', function () {
      hljs.highlightAll();
    });

    // ── per-card toggle ──────────────────────────────────────────────
    function toggleCard(header) {
      const body = header.nextElementSibling;
      const btn  = header.querySelector('.toggle-btn');
      const collapsed = body.classList.toggle('collapsed');
      btn.textContent = collapsed ? '\\u25b6 Show' : '\\u25bc Hide';
    }

    // ── show / collapse all ──────────────────────────────────────────
    function showAll() {
      document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {
        b.classList.remove('collapsed');
        b.closest('.card').querySelector('.toggle-btn').textContent = '\\u25bc Hide';
      });
    }
    function collapseAll() {
      document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {
        b.classList.add('collapsed');
        b.closest('.card').querySelector('.toggle-btn').textContent = '\\u25b6 Show';
      });
    }

    // ── card-level filter (show/hide cards by match) ─────────────────
    function applyCardFilter(term) {
      const lower = term.trim().toLowerCase();
      let shown = 0;
      document.querySelectorAll('.card').forEach(card => {
        const has = !lower || card.querySelector('code').textContent.toLowerCase().includes(lower);
        card.classList.toggle('hidden-by-search', !has);
        if (has) shown++;
      });
      const info = document.getElementById('match-info');
      info.textContent = lower
        ? (shown === 0 ? 'No files match' : shown + ' file' + (shown > 1 ? 's' : '') + ' match')
        : '';
    }

    // ── in-page text search ──────────────────────────────────────────
    let marks = [];
    let currentIdx = -1;
    const psbInput = document.getElementById('psb-input');
    const psbCount = document.getElementById('psb-count');

    function clearMarks() {
      document.querySelectorAll('mark.sh, mark.sh-current').forEach(m => {
        m.outerHTML = m.textContent
          .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      });
      // normalize() re-merges adjacent text nodes
      document.querySelectorAll('.card-body code').forEach(c => c.normalize());
      marks = [];
      currentIdx = -1;
    }

    function findAll(term) {
      clearMarks();
      if (!term) { updateCount(); return; }
      const lower = term.toLowerCase();

      document.querySelectorAll('.card-body code').forEach(code => {
        const walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT);
        const nodes = [];
        let n;
        while ((n = walker.nextNode())) nodes.push(n);

        nodes.forEach(node => {
          const text = node.textContent;
          const ltxt = text.toLowerCase();
          let pos = 0, start;
          const frags = [];
          while ((start = ltxt.indexOf(lower, pos)) !== -1) {
            if (start > pos) frags.push(document.createTextNode(text.slice(pos, start)));
            const m = document.createElement('mark');
            m.className = 'sh';
            m.textContent = text.slice(start, start + term.length);
            frags.push(m);
            marks.push(m);
            pos = start + term.length;
          }
          if (frags.length) {
            if (pos < text.length) frags.push(document.createTextNode(text.slice(pos)));
            node.replaceWith(...frags);
          }
        });
      });
      updateCount();
    }

    function goTo(idx) {
      if (!marks.length) return;
      if (currentIdx >= 0) {
        marks[currentIdx].className = 'sh';
      }
      currentIdx = ((idx % marks.length) + marks.length) % marks.length;
      const m = marks[currentIdx];
      m.className = 'sh-current';
      // expand card if collapsed
      const body = m.closest('.card-body');
      if (body && body.classList.contains('collapsed')) {
        body.classList.remove('collapsed');
        body.closest('.card').querySelector('.toggle-btn').textContent = '\\u25bc Hide';
      }
      m.scrollIntoView({ behavior: 'smooth', block: 'center' });
      updateCount();
    }

    function updateCount() {
      if (!psbInput.value.trim()) { psbCount.textContent = ''; return; }
      psbCount.textContent = marks.length === 0
        ? '0 matches'
        : (currentIdx + 1) + ' / ' + marks.length;
      document.getElementById('psb-prev').disabled = marks.length === 0;
      document.getElementById('psb-next').disabled = marks.length === 0;
    }

    function runPageSearch() {
      const term = psbInput.value;
      applyCardFilter(term);
      findAll(term);
      if (marks.length) goTo(0);
    }

    function prevMatch() { if (marks.length) goTo(currentIdx - 1); }
    function nextMatch() { if (marks.length) goTo(currentIdx + 1); }

    function clearPageSearch() {
      psbInput.value = '';
      clearMarks();
      applyCardFilter('');
      updateCount();
    }

    psbInput.addEventListener('input', runPageSearch);
    psbInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') { e.shiftKey ? prevMatch() : nextMatch(); }
      if (e.key === 'Escape') clearPageSearch();
    });

    // ── messages from sidebar ────────────────────────────────────────
    window.addEventListener('message', function (e) {
      if (!e.data) return;
      if (e.data.type === 'page-search') {
        psbInput.value = e.data.term || '';
        runPageSearch();
      }
    });
  </script>"""


def collect_java_files(rel_path):
    folder = BASE / rel_path if rel_path else BASE
    files = []
    if rel_path == "functional_interfaces":
        for sub in sorted(folder.iterdir()):
            if sub.is_dir():
                for f in sorted(sub.glob("*.java")):
                    files.append((f, f"{rel_path}/{sub.name}/{f.name}"))
    else:
        for f in sorted(folder.glob("*.java")):
            files.append((f, f.name))
    return files


def make_folder_page(slug, rel_path, title):
    files = collect_java_files(rel_path)
    cards = []
    for filepath, display in files:
        try:
            code = filepath.read_text(encoding="utf-8")
        except Exception as e:
            code = f"// Could not read file: {e}"
        escaped = html.escape(code)
        cards.append(f"""    <div class="card">
      <div class="card-header" onclick="toggleCard(this)">
        <span class="filename">{html.escape(filepath.name)}</span>
        <span class="path">{html.escape(display)}</span>
        <button class="toggle-btn" onclick="event.stopPropagation();toggleCard(this.closest('.card-header'))">&#9660; Hide</button>
      </div>
      <div class="card-body">
        <pre><code class="language-java">{escaped}</code></pre>
      </div>
    </div>""")

    body = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)} - Java Preview</title>
{HLJS_HEAD}
{PAGE_CSS}
</head>
<body>
  <div id="page-header">
    <h1>{html.escape(title)}</h1>
    <div class="toolbar">
      <button class="btn-show" onclick="showAll()">&#9660; Show all</button>
      <button class="btn-hide" onclick="collapseAll()">&#9654; Collapse all</button>
      <span class="match-info" id="match-info"></span>
    </div>
    <div class="page-search-bar">
      <input id="psb-input" type="text" placeholder="&#128269; Search in code&hellip;" autocomplete="off">
      <button class="psb-btn" id="psb-prev" onclick="prevMatch()" disabled title="Previous (Shift+Enter)">&#9650; Prev</button>
      <button class="psb-btn" id="psb-next" onclick="nextMatch()" disabled title="Next (Enter)">&#9660; Next</button>
      <button class="psb-clear" onclick="clearPageSearch()" title="Clear (Esc)">&#x2715;</button>
      <span class="psb-count" id="psb-count"></span>
    </div>
  </div>
  <div id="cards-container">
{body}
  </div>
{PAGE_JS}
</body>
</html>
"""


def build_folder_index():
    """Return a dict: slug -> lowercased concatenation of all Java source in that folder."""
    index = {}
    for slug, rel_path, title in FOLDERS:
        files = collect_java_files(rel_path)
        parts = []
        for filepath, _ in files:
            try:
                parts.append(filepath.read_text(encoding="utf-8").lower())
            except Exception:
                pass
        index[slug] = "\n".join(parts)
    return index


def make_index():
    folder_index = build_folder_index()

    # Embed as JS object literal with escaped string values
    js_entries = []
    for slug, content in folder_index.items():
        # escape backslash and backtick so we can use template literals safely
        safe = content.replace("\\", "\\\\").replace("`", "\\`")
        js_entries.append(f'  "{slug}": `{safe}`')
    folder_code_js = "const FOLDER_CODE = {\n" + ",\n".join(js_entries) + "\n};"

    links = []
    for slug, rel_path, title in FOLDERS:
        links.append(
            f'      <li data-slug="{slug}"><a href="{slug}.html" target="content" '
            f'onclick="setActive(this)">{html.escape(title)}</a></li>'
        )
    links_html = "\n".join(links)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Java Code Preview</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ height: 100%; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; }}
    #layout {{ display: flex; height: 100vh; }}

    #sidebar {{
      width: 230px; min-width: 230px;
      background: #1a202c; color: #e2e8f0;
      display: flex; flex-direction: column;
      overflow-y: auto;
    }}
    #sidebar h2 {{
      padding: 18px 16px 12px;
      font-size: 0.85rem; font-weight: 700;
      color: #63b3ed; letter-spacing: 0.08em; text-transform: uppercase;
      border-bottom: 1px solid #2d3748;
    }}

    /* search box */
    .search-wrap {{
      padding: 10px 12px;
      border-bottom: 1px solid #2d3748;
    }}
    .search-wrap input {{
      width: 100%; padding: 7px 10px;
      background: #2d3748; border: 1px solid #4a5568;
      border-radius: 5px; color: #e2e8f0; font-size: 0.85rem; outline: none;
    }}
    .search-wrap input::placeholder {{ color: #718096; }}
    .search-wrap input:focus {{ border-color: #63b3ed; }}
    .search-clear {{
      display: none; position: absolute; right: 22px;
      top: 50%; transform: translateY(-50%);
      background: none; border: none; color: #718096;
      cursor: pointer; font-size: 1rem; padding: 0 4px;
    }}
    .search-wrap {{ position: relative; }}
    .search-wrap input:not(:placeholder-shown) + .search-clear {{ display: block; }}

    #sidebar ul {{ list-style: none; padding: 6px 0; flex: 1; }}
    #sidebar li a {{
      display: block; padding: 9px 20px;
      color: #a0aec0; text-decoration: none; font-size: 0.88rem;
      border-left: 3px solid transparent;
      transition: background 0.12s, color 0.12s;
    }}
    #sidebar li a:hover  {{ background: #2d3748; color: #e2e8f0; }}
    #sidebar li a.active {{ background: #2d3748; color: #63b3ed; border-left-color: #63b3ed; }}
    #sidebar li.no-match {{ display: none; }}
    #sidebar li.has-match > a {{ color: #e2e8f0; }}
    .no-match-msg {{ display: none; padding: 10px 20px; color: #718096; font-size: 0.82rem; font-style: italic; }}
    .no-match-msg.visible {{ display: block; }}

    #sidebar footer {{
      padding: 10px 16px; font-size: 0.72rem;
      color: #4a5568; border-top: 1px solid #2d3748;
    }}

    #content {{ flex: 1; overflow: hidden; }}
    #content iframe {{ width: 100%; height: 100%; border: none; }}
  </style>
</head>
<body>
<div id="layout">
  <nav id="sidebar">
    <h2>Java Preview</h2>
    <div class="search-wrap">
      <input type="text" id="search" placeholder="&#128269; Search in code..." autocomplete="off">
      <button class="search-clear" id="search-clear" title="Clear">&#x2715;</button>
    </div>
    <ul id="folder-list">
{links_html}
    </ul>
    <p class="no-match-msg" id="no-match-msg">No folders match</p>
    <footer>src/test/</footer>
  </nav>
  <div id="content">
    <iframe name="content" id="frame" src="root.html"></iframe>
  </div>
</div>
<script>
  {folder_code_js}

  function setActive(el) {{
    document.querySelectorAll('#sidebar a').forEach(a => a.classList.remove('active'));
    el.classList.add('active');
  }}
  document.querySelector('#sidebar a[href="root.html"]').classList.add('active');

  // send search term to iframe via postMessage
  function sendSearch(term) {{
    const frame = document.getElementById('frame');
    try {{
      frame.contentWindow.postMessage({{ type: 'page-search', term: term }}, '*');
    }} catch(e) {{}}
  }}

  // filter sidebar links by whether the folder's code contains the term
  function filterMenu(term) {{
    const lower = term.trim().toLowerCase();
    let anyVisible = false;
    document.querySelectorAll('#folder-list li').forEach(li => {{
      const slug = li.dataset.slug;
      const matches = !lower || (FOLDER_CODE[slug] && FOLDER_CODE[slug].includes(lower));
      li.classList.toggle('no-match', !matches);
      li.classList.toggle('has-match', !!lower && matches);
      if (matches) anyVisible = true;
    }});
    document.getElementById('no-match-msg').classList.toggle('visible', !!lower && !anyVisible);
  }}

  const searchInput = document.getElementById('search');
  const clearBtn    = document.getElementById('search-clear');

  searchInput.addEventListener('input', function () {{
    filterMenu(this.value);
    sendSearch(this.value);
  }});

  clearBtn.addEventListener('click', function () {{
    searchInput.value = '';
    filterMenu('');
    sendSearch('');
    searchInput.focus();
  }});

  // re-send search after iframe loads a new page
  document.getElementById('frame').addEventListener('load', function () {{
    if (searchInput.value) sendSearch(searchInput.value);
  }});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print(f"Generating HTML pages in: {OUT}")
    for slug, rel_path, title in FOLDERS:
        page = make_folder_page(slug, rel_path, title)
        out_file = OUT / f"{slug}.html"
        out_file.write_text(page, encoding="utf-8")
        print(f"  Created: {out_file.name}")
    index = make_index()
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print("  Created: index.html")
    print("Done! Open html_preview/index.html in your browser.")
