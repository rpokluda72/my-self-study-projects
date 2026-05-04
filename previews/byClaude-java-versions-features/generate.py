"""
generate.py — Generates static HTML preview for java-versions-features study project.

Usage:
    cd html_preview
    python generate.py

Output: index.html + one HTML file per Java version package.
Re-run whenever .java source files change.
"""

import html
from pathlib import Path

SRC_ROOT = Path("../src/main/java")
OUT      = Path(".")

PACKAGES = [
    ("java8",  "Java 8",  [
        "LambdaExpressions", "StreamApi", "FunctionalInterfaces",
        "MethodReferences", "DefaultMethods", "OptionalClass",
    ]),
    ("java9",  "Java 9",  [
        "CollectionFactoryMethods", "TryWithResourcesEnhancement",
    ]),
    ("java10", "Java 10", [
        "LocalVariableTypeInference",
    ]),
    ("java11", "Java 11", [
        "StringMethods", "HttpClientApi", "FileMethods",
    ]),
    ("java14", "Java 14", [
        "SwitchExpressions",
    ]),
    ("java15", "Java 15", [
        "TextBlocks",
    ]),
    ("java16", "Java 16", [
        "Records", "PatternMatchingInstanceof", "StreamToList",
    ]),
    ("java17", "Java 17", [
        "SealedClasses",
    ]),
    ("java21", "Java 21", [
        "VirtualThreads", "RecordPatterns", "PatternMatchingSwitch", "SequencedCollections",
    ]),
    ("java23", "Java 23", [
        "UnnamedVariables",
    ]),
    ("java24", "Java 24", [
        "StreamGatherers",
    ]),
]

# ─── Templates ───────────────────────────────────────────────────────────────

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; background: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', system-ui, sans-serif; }}
  body {{ display: flex; flex-direction: column; overflow: hidden; }}

  /* ── Page header ── */
  #page-header {{
    flex-shrink: 0;
    background: #181825;
    padding: 12px 16px 10px;
    border-bottom: 1px solid #313244;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    z-index: 10;
  }}
  #page-header h1 {{
    font-size: 18px; font-weight: 700; color: #cba6f7; margin-bottom: 8px;
    letter-spacing: 0.03em;
  }}
  .toolbar {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;
  }}
  .btn {{ padding: 4px 12px; border: none; border-radius: 4px; cursor: pointer;
          font-size: 12px; font-weight: 600; transition: background .15s; }}
  .btn-show  {{ background: #89b4fa; color: #1e1e2e; }}
  .btn-show:hover  {{ background: #74c7ec; }}
  .btn-hide  {{ background: #585b70; color: #cdd6f4; }}
  .btn-hide:hover  {{ background: #6c7086; }}
  #match-info {{ font-size: 12px; color: #a6adc8; margin-left: 4px; }}

  /* ── Page search bar ── */
  .page-search-bar {{
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  }}
  #psb-input {{
    flex: 1; min-width: 180px; max-width: 320px;
    background: #313244; border: 1px solid #45475a; color: #cdd6f4;
    border-radius: 4px; padding: 5px 10px; font-size: 13px; outline: none;
  }}
  #psb-input:focus {{ border-color: #89b4fa; box-shadow: 0 0 0 2px rgba(137,180,250,.2); }}
  #psb-input::placeholder {{ color: #6c7086; }}
  .psb-btn {{
    padding: 4px 10px; border: 1px solid #45475a; border-radius: 4px;
    background: #313244; color: #cdd6f4; cursor: pointer; font-size: 12px;
    transition: background .15s;
  }}
  .psb-btn:hover {{ background: #45475a; }}
  .psb-btn:disabled {{ opacity: .4; cursor: default; }}
  .psb-clear {{
    padding: 4px 10px; border: none; border-radius: 4px;
    background: #f38ba8; color: #1e1e2e; cursor: pointer; font-size: 12px;
    font-weight: 600; transition: background .15s;
  }}
  .psb-clear:hover {{ background: #eba0ac; }}
  #psb-count {{ font-size: 12px; color: #a6adc8; min-width: 60px; }}

  /* ── Cards container ── */
  #cards-container {{
    flex: 1; overflow-y: auto; padding: 12px 16px 20px;
  }}
  .card {{
    margin-bottom: 12px; border-radius: 8px; overflow: hidden;
    border: 1px solid #313244; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }}
  .card.hidden-by-search {{ display: none; }}

  /* ── Card header ── */
  .card-header {{
    display: flex; align-items: center; justify-content: space-between;
    background: #2a2a3d; padding: 8px 14px; cursor: pointer;
    user-select: none; transition: background .15s;
    border-bottom: 1px solid #313244;
  }}
  .card-header:hover {{ background: #313244; }}
  .filename {{ font-size: 14px; font-weight: 600; color: #89dceb; font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
  .toggle-btn {{
    background: none; border: 1px solid #45475a; color: #a6adc8;
    border-radius: 4px; padding: 2px 8px; cursor: pointer; font-size: 11px;
    transition: all .15s; white-space: nowrap;
  }}
  .toggle-btn:hover {{ background: #45475a; color: #cdd6f4; }}

  /* ── Card body ── */
  .card-body {{ overflow: hidden; }}
  .card-body.collapsed {{ display: none; }}
  .card-body pre {{ margin: 0; }}
  .card-body pre code.hljs {{
    font-size: 13px; line-height: 1.55; padding: 14px 16px !important;
    background: #282c34 !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  }}

  /* ── Search highlights ── */
  mark.sh         {{ background: #f9e2af; color: #1e1e2e; border-radius: 2px; }}
  mark.sh-current {{ background: #fab387; color: #1e1e2e; border-radius: 2px; outline: 2px solid #f38ba8; }}
</style>
</head>
<body>
<div id="page-header">
  <h1>{title}</h1>
  <div class="toolbar">
    <button class="btn btn-show" onclick="showAll()">&#9660; Show all</button>
    <button class="btn btn-hide" onclick="collapseAll()">&#9654; Collapse all</button>
    <span id="match-info"></span>
  </div>
  <div class="page-search-bar">
    <input id="psb-input" placeholder="Search in code…" autocomplete="off" spellcheck="false" />
    <button class="psb-btn" id="psb-prev" onclick="prevMatch()">&#8593; Prev</button>
    <button class="psb-btn" id="psb-next" onclick="nextMatch()">&#8595; Next</button>
    <button class="psb-clear" onclick="clearPageSearch()">&#10005; Clear</button>
    <span id="psb-count"></span>
  </div>
</div>
<div id="cards-container">
{cards}
</div>
<script>
// ── Card toggle ──────────────────────────────────────────────────────────────
function toggleCard(header) {{
  const body = header.nextElementSibling;
  const btn  = header.querySelector('.toggle-btn');
  const c    = body.classList.toggle('collapsed');
  btn.textContent = c ? '\\u25b6 Show' : '\\u25bc Hide';
}}
function showAll() {{
  document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {{
    b.classList.remove('collapsed');
    b.closest('.card').querySelector('.toggle-btn').textContent = '\\u25bc Hide';
  }});
}}
function collapseAll() {{
  document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {{
    b.classList.add('collapsed');
    b.closest('.card').querySelector('.toggle-btn').textContent = '\\u25b6 Show';
  }});
}}

// ── Card filter ──────────────────────────────────────────────────────────────
function applyCardFilter(term) {{
  const lower = term.trim().toLowerCase();
  let shown = 0;
  document.querySelectorAll('.card').forEach(card => {{
    const has = !lower || card.querySelector('code').textContent.toLowerCase().includes(lower);
    card.classList.toggle('hidden-by-search', !has);
    if (has) shown++;
  }});
  document.getElementById('match-info').textContent = lower
    ? (shown === 0 ? 'No files match' : shown + ' file' + (shown > 1 ? 's' : '') + ' match')
    : '';
}}

// ── In-page text search ──────────────────────────────────────────────────────
const psbInput = document.getElementById('psb-input');
const psbCount = document.getElementById('psb-count');
let marks = [], currentIdx = -1;

function clearMarks() {{
  document.querySelectorAll('mark.sh, mark.sh-current').forEach(m => {{
    const t = document.createTextNode(
      m.textContent.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    );
    // actually just replace with text node directly:
    m.parentNode.replaceChild(document.createTextNode(m.textContent), m);
  }});
  document.querySelectorAll('.card-body code').forEach(c => c.normalize());
  marks = []; currentIdx = -1;
}}

function findAll(term) {{
  clearMarks();
  if (!term.trim()) {{ updateCount(); return; }}
  const lower = term.toLowerCase();
  document.querySelectorAll('.card-body code').forEach(code => {{
    const walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(node => {{
      const text = node.textContent, ltxt = text.toLowerCase();
      let pos = 0, start;
      const frags = [];
      while ((start = ltxt.indexOf(lower, pos)) !== -1) {{
        if (start > pos) frags.push(document.createTextNode(text.slice(pos, start)));
        const m = document.createElement('mark');
        m.className = 'sh';
        m.textContent = text.slice(start, start + term.length);
        frags.push(m); marks.push(m);
        pos = start + term.length;
      }}
      if (frags.length) {{
        if (pos < text.length) frags.push(document.createTextNode(text.slice(pos)));
        node.replaceWith(...frags);
      }}
    }});
  }});
  updateCount();
}}

function goTo(idx) {{
  if (!marks.length) return;
  if (currentIdx >= 0) marks[currentIdx].className = 'sh';
  currentIdx = ((idx % marks.length) + marks.length) % marks.length;
  const m = marks[currentIdx];
  m.className = 'sh-current';
  // auto-expand card if collapsed
  const body = m.closest('.card-body');
  if (body && body.classList.contains('collapsed')) {{
    body.classList.remove('collapsed');
    body.closest('.card').querySelector('.toggle-btn').textContent = '\\u25bc Hide';
  }}
  m.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  updateCount();
}}

function updateCount() {{
  const v = psbInput.value.trim();
  if (!v) {{ psbCount.textContent = ''; return; }}
  psbCount.textContent = marks.length === 0
    ? '0 matches'
    : (currentIdx + 1) + ' / ' + marks.length;
  document.getElementById('psb-prev').disabled = marks.length === 0;
  document.getElementById('psb-next').disabled = marks.length === 0;
}}

function runPageSearch() {{
  const term = psbInput.value;
  applyCardFilter(term);
  findAll(term);
  if (marks.length) goTo(0);
}}
function prevMatch() {{ if (marks.length) goTo(currentIdx - 1); }}
function nextMatch() {{ if (marks.length) goTo(currentIdx + 1); }}
function clearPageSearch() {{
  psbInput.value = ''; clearMarks(); applyCardFilter(''); updateCount();
}}

psbInput.addEventListener('input', runPageSearch);
psbInput.addEventListener('keydown', function(e) {{
  if (e.key === 'Enter') {{ e.shiftKey ? prevMatch() : nextMatch(); }}
  if (e.key === 'Escape') clearPageSearch();
}});

window.addEventListener('message', function(e) {{
  if (!e.data || e.data.type !== 'page-search') return;
  psbInput.value = e.data.term || '';
  runPageSearch();
}});

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {{
  hljs.highlightAll();
  // Hash-based scroll: navigate to specific card when loaded via #CardName
  if (location.hash) {{
    const target = document.querySelector(location.hash);
    if (target) {{
      const body = target.querySelector('.card-body');
      if (body) body.classList.remove('collapsed');
      setTimeout(() => target.scrollIntoView({{ behavior: 'smooth', block: 'start' }}), 120);
    }}
  }}
}});
</script>
</body>
</html>
"""

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Java Versions Features</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; overflow: hidden; background: #1e1e2e;
                font-family: 'Segoe UI', system-ui, sans-serif; color: #cdd6f4; }}

  /* ── Layout ── */
  #layout {{ display: flex; height: 100vh; }}
  #sidebar {{
    width: 270px; min-width: 270px;
    background: #181825;
    border-right: 1px solid #313244;
    display: flex; flex-direction: column;
    overflow: hidden;
  }}
  #content-area {{ flex: 1; display: flex; overflow: hidden; }}
  #frame {{ flex: 1; border: none; width: 100%; height: 100%; }}

  /* ── Sidebar header ── */
  #sidebar h2 {{
    padding: 16px 14px 10px;
    font-size: 15px; font-weight: 700; color: #cba6f7;
    letter-spacing: 0.04em; text-transform: uppercase;
    border-bottom: 1px solid #313244; flex-shrink: 0;
  }}

  /* ── Search ── */
  .search-wrap {{
    padding: 10px 10px 4px; flex-shrink: 0; position: relative;
  }}
  #search {{
    width: 100%; background: #313244; border: 1px solid #45475a;
    color: #cdd6f4; border-radius: 5px; padding: 6px 28px 6px 10px;
    font-size: 13px; outline: none;
  }}
  #search:focus {{ border-color: #89b4fa; box-shadow: 0 0 0 2px rgba(137,180,250,.2); }}
  #search::placeholder {{ color: #6c7086; }}
  .search-clear {{
    position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: #6c7086; cursor: pointer;
    font-size: 14px; line-height: 1; display: none; padding: 2px 4px;
  }}
  .search-clear:hover {{ color: #f38ba8; }}
  #search:not(:placeholder-shown) + .search-clear {{ display: block; }}

  /* ── Show All / Collapse All buttons ── */
  .menu-btn-row {{
    display: flex; gap: 6px; padding: 6px 10px 4px; flex-shrink: 0;
  }}
  .menu-btn {{
    flex: 1; padding: 5px 6px;
    background: #313244; border: 1px solid #45475a; border-radius: 5px;
    color: #a6adc8; font-size: 12px; cursor: pointer;
    text-align: center; transition: background .15s;
  }}
  .menu-btn:hover {{ background: #45475a; color: #cdd6f4; }}

  /* ── Version list (scrollable) ── */
  #version-list {{
    flex: 1; overflow-y: auto; list-style: none;
    padding: 4px 0 12px; margin: 0;
    scrollbar-width: thin; scrollbar-color: #45475a #181825;
  }}
  #version-list::-webkit-scrollbar {{ width: 6px; }}
  #version-list::-webkit-scrollbar-track {{ background: #181825; }}
  #version-list::-webkit-scrollbar-thumb {{ background: #45475a; border-radius: 3px; }}

  /* ── Version group ── */
  .version-group {{ border-bottom: 1px solid #232336; }}
  .version-group.no-match {{ display: none; }}
  .version-group.collapsed .class-list {{ display: none; }}

  .version-header {{
    display: flex; align-items: center; gap: 7px;
    padding: 8px 12px; cursor: pointer; user-select: none;
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #89b4fa;
    transition: background .15s;
  }}
  .version-header:hover {{ background: #232336; color: #b4d0ff; }}
  .chevron {{ font-size: 9px; color: #585b70; transition: color .15s; }}
  .version-header:hover .chevron {{ color: #89b4fa; }}

  /* ── Class list ── */
  .class-list {{ list-style: none; padding: 0 0 4px 0; margin: 0; }}
  .class-list li.no-match {{ display: none; }}
  .class-list li.has-match > a {{ color: #cdd6f4 !important; }}
  .class-list a {{
    display: block; padding: 5px 12px 5px 26px;
    color: #9399b2; text-decoration: none; font-size: 13px;
    transition: background .1s, color .1s; border-left: 2px solid transparent;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .class-list a:hover {{
    background: #232336; color: #cdd6f4; border-left-color: #585b70;
  }}
  .class-list a.active {{
    background: #2a2a40; color: #89b4fa; border-left-color: #89b4fa;
    font-weight: 600;
  }}

  /* ── No-match message ── */
  #no-match-msg {{
    padding: 10px 14px; font-size: 12px; color: #6c7086;
    display: none; flex-shrink: 0;
  }}
  #no-match-msg.visible {{ display: block; }}

  /* ── Footer ── */
  #sidebar-footer {{
    padding: 8px 14px; font-size: 11px; color: #45475a;
    border-top: 1px solid #313244; flex-shrink: 0;
  }}
</style>
</head>
<body>
<div id="layout">
  <nav id="sidebar">
    <h2>&#9749; Java Features</h2>
    <div class="search-wrap">
      <input id="search" type="search" placeholder="Search in code&#x2026;" autocomplete="off" spellcheck="false" />
      <button class="search-clear" title="Clear search">&#10005;</button>
    </div>
    <div class="menu-btn-row">
      <button class="menu-btn" id="show-all-btn">&#9660; Show All</button>
      <button class="menu-btn" id="collapse-all-btn">&#9654; Collapse All</button>
    </div>
    <ul id="version-list">
{menu}
    </ul>
    <p id="no-match-msg">No results match</p>
    <div id="sidebar-footer">src/main/java/ &mdash; Java 8&ndash;24</div>
  </nav>
  <div id="content-area">
    <iframe id="frame" name="content" src="java8.html"></iframe>
  </div>
</div>
<script>
{pkg_code_js}

const searchInput = document.getElementById('search');
const clearBtn    = document.querySelector('.search-clear');

function setActive(el) {{
  document.querySelectorAll('#version-list a').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
  const group = el.closest('.version-group');
  group.classList.remove('collapsed');
  group.querySelector('.chevron').textContent = '\\u25bc';
}}

function toggleVersion(pkg) {{
  const group = document.querySelector(`.version-group[data-pkg="${{pkg}}"]`);
  const c = group.classList.toggle('collapsed');
  group.querySelector('.chevron').textContent = c ? '\\u25b6' : '\\u25bc';
}}

document.getElementById('show-all-btn').addEventListener('click', function() {{
  document.querySelectorAll('.version-group').forEach(g => {{
    g.classList.remove('collapsed');
    g.querySelector('.chevron').textContent = '\\u25bc';
  }});
}});
document.getElementById('collapse-all-btn').addEventListener('click', function() {{
  document.querySelectorAll('.version-group').forEach(g => {{
    g.classList.add('collapsed');
    g.querySelector('.chevron').textContent = '\\u25b6';
  }});
}});

function filterMenu(term) {{
  const lower = term.trim().toLowerCase();
  let anyVisible = false;
  document.querySelectorAll('.version-group').forEach(function(group) {{
    const pkg = group.dataset.pkg;
    let anyClassMatch = false;
    group.querySelectorAll('.class-list li').forEach(function(li) {{
      const cls   = (li.dataset.cls || '').toLowerCase();
      const match = !lower || cls.includes(lower) || (PKG_CODE[pkg] && PKG_CODE[pkg].includes(lower));
      li.classList.toggle('no-match',   !match);
      li.classList.toggle('has-match',  !!lower && match);
      if (match) anyClassMatch = true;
    }});
    group.classList.toggle('no-match', !anyClassMatch);
    if (anyClassMatch) {{
      anyVisible = true;
      if (lower) {{
        group.classList.remove('collapsed');
        group.querySelector('.chevron').textContent = '\\u25bc';
      }}
    }}
  }});
  document.getElementById('no-match-msg').classList.toggle('visible', !!lower && !anyVisible);
}}

function sendSearch(term) {{
  const frame = document.getElementById('frame');
  if (frame.contentWindow) {{
    frame.contentWindow.postMessage({{ type: 'page-search', term: term }}, '*');
  }}
}}

searchInput.addEventListener('input', function() {{
  filterMenu(this.value);
  sendSearch(this.value);
}});
clearBtn.addEventListener('click', function() {{
  searchInput.value = ''; filterMenu(''); sendSearch(''); searchInput.focus();
}});
document.getElementById('frame').addEventListener('load', function() {{
  if (searchInput.value) sendSearch(searchInput.value);
}});
</script>
</body>
</html>
"""

# ─── Helper functions ─────────────────────────────────────────────────────────

def read_java(pkg, cls):
    path = SRC_ROOT / pkg / f"{cls}.java"
    return html.escape(path.read_text(encoding="utf-8"))

def pkg_code_for_search(pkg, classes):
    parts = []
    for cls in classes:
        path = SRC_ROOT / pkg / f"{cls}.java"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").lower())
    return " ".join(parts)

# ─── Page generator ───────────────────────────────────────────────────────────

def make_pkg_page(pkg, title, classes):
    cards = []
    for cls in classes:
        code = read_java(pkg, cls)
        cards.append(f'''\
  <div class="card" id="{cls}">
    <div class="card-header" onclick="toggleCard(this)">
      <span class="filename">{cls}.java</span>
      <button class="toggle-btn">&#x25bc; Hide</button>
    </div>
    <div class="card-body">
      <pre><code class="language-java">{code}</code></pre>
    </div>
  </div>''')
    return PAGE_TEMPLATE.format(title=title, cards="\n".join(cards))

# ─── Index generator ──────────────────────────────────────────────────────────

def make_index():
    # PKG_CODE JS object — lowercased source for sidebar search
    entries = []
    for pkg, title, classes in PACKAGES:
        code = pkg_code_for_search(pkg, classes)
        escaped = code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        entries.append(f"  {pkg}: `{escaped}`")
    pkg_code_js = "const PKG_CODE = {{\n" + ",\n".join(entries) + "\n}};"
    # Note: double braces {{ }} are literal braces in Python f-strings

    # Actually we're not using f-string for pkg_code_js, it's a plain string
    pkg_code_js = "const PKG_CODE = {\n" + ",\n".join(entries) + "\n};"

    # Two-level menu HTML
    menu_items = []
    for pkg, title, classes in PACKAGES:
        class_items = []
        for cls in classes:
            class_items.append(
                f'      <li data-pkg="{pkg}" data-cls="{cls}">\n'
                f'        <a href="{pkg}.html#{cls}" target="content"'
                f' onclick="setActive(this)">{cls}</a>\n'
                f'      </li>'
            )
        menu_items.append(
            f'    <li class="version-group" data-pkg="{pkg}">\n'
            f'      <div class="version-header" onclick="toggleVersion(\'{pkg}\')">\n'
            f'        <span class="chevron">&#x25bc;</span> {title}\n'
            f'      </div>\n'
            f'      <ul class="class-list">\n'
            + "\n".join(class_items) + "\n"
            f'      </ul>\n'
            f'    </li>'
        )
    menu = "\n".join(menu_items)

    return INDEX_TEMPLATE.format(pkg_code_js=pkg_code_js, menu=menu)

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    generated = 0
    for pkg, title, classes in PACKAGES:
        page = make_pkg_page(pkg, title, classes)
        out  = OUT / f"{pkg}.html"
        out.write_text(page, encoding="utf-8")
        print(f"  OK {out.name}")
        generated += 1

    index = make_index()
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print(f"  OK index.html")
    generated += 1

    print(f"\nGenerated {generated} files in '{OUT.resolve()}'")
