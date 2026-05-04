"""Generate static HTML preview pages for RxJava tutorial Java sources.

Reads every _NN_ClassName.java from src/main/java/tutorial/ and writes:
  - one  html_preview/NN_class_name.html  per Java file
  - html_preview/index.html               (sidebar + iframe shell)

Each Java file is split into per-method cards so the sidebar sub-menu can
link directly to a method section via a hash anchor (e.g. #card-democreate).

Run from the html_preview folder:
    python generate.py

Or from the project root:
    python html_preview/generate.py
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).parent                           # html_preview/
SRC  = HERE.parent / "src" / "main" / "java" / "tutorial"

# ── CDN links ─────────────────────────────────────────────────────────────────

HLJS_CSS  = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css'
HLJS_JS   = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js'
HLJS_JAVA = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js'

# ── Shared CSS (dark Catppuccin theme) ────────────────────────────────────────
# body uses window scrolling so that hash anchors (#card-democreate) work
# natively when the sidebar links to a method section.

PAGE_CSS = """\
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#1e1e2e;--surface:#24273a;--text:#cdd6f4;--subtext:#a6adc8;
  --accent:#89b4fa;--accent2:#cba6f7;--border:#313244;--hover:#45475a;
  --mark-y:#f9e2af;--mark-o:#fab387;--red:#f38ba8;
}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}
#header{position:sticky;top:0;z-index:100;background:var(--bg);border-bottom:1px solid var(--border);padding:10px 16px 8px}
.header-top{display:flex;align-items:center;gap:12px;margin-bottom:8px}
h1{font-size:16px;font-weight:600;color:var(--accent2);white-space:nowrap}
h1 .num{color:var(--accent);margin-right:6px}
.toolbar{display:flex;align-items:center;gap:6px}
.toolbar button{background:var(--hover);border:1px solid var(--border);color:var(--text);
                border-radius:5px;padding:3px 10px;font-size:12px;cursor:pointer}
.toolbar button:hover{background:var(--accent);color:#1e1e2e}
.match-info{font-size:12px;color:var(--subtext);margin-left:4px}
.search-bar{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.search-input-wrap{position:relative;display:flex;align-items:center}
#psb-input{background:#313244;border:1px solid var(--border);color:var(--text);
           border-radius:6px;padding:4px 28px 4px 10px;font-size:13px;width:220px;outline:none}
#psb-input:focus{border-color:var(--accent)}
.search-clear{position:absolute;right:6px;background:none;border:none;
              color:var(--subtext);cursor:pointer;font-size:14px}
.search-clear:hover{color:var(--red)}
.search-bar button{background:var(--hover);border:1px solid var(--border);color:var(--text);
                   border-radius:5px;padding:3px 9px;font-size:12px;cursor:pointer}
.search-bar button:hover:not(:disabled){background:var(--accent);color:#1e1e2e}
.search-bar button:disabled{opacity:.4;cursor:default}
#psb-count{font-size:12px;color:var(--accent);min-width:70px}
#cards{padding:16px}
/* scroll-margin-top keeps the card below the sticky header when jumped to via hash */
.card{background:var(--surface);border:1px solid var(--border);
      border-radius:8px;margin-bottom:14px;overflow:hidden;scroll-margin-top:115px}
.card.hidden-by-search{display:none}
.card-header{display:flex;align-items:center;justify-content:space-between;
             padding:10px 14px;cursor:pointer;user-select:none;border-bottom:1px solid var(--border)}
.card-header:hover{background:var(--hover)}
.card-filename{font-family:'JetBrains Mono','Fira Code',Consolas,monospace;
               font-size:13px;color:var(--accent);font-weight:600}
.toggle-btn{background:none;border:1px solid var(--border);color:var(--subtext);
            border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer}
.toggle-btn:hover{background:var(--accent);color:#1e1e2e;border-color:var(--accent)}
.card-body{overflow:hidden}
.card-body.collapsed{display:none}
.card-body pre{margin:0;border-radius:0}
.card-body code{font-family:'JetBrains Mono','Fira Code',Consolas,monospace!important;
                font-size:13px!important;line-height:1.6!important}
mark.sh{background:var(--mark-y);color:#1e1e2e;border-radius:2px}
mark.sh-current{background:var(--mark-o);color:#1e1e2e;border-radius:2px;outline:2px solid var(--red)}
</style>"""

# ── Shared JS (search + collapse) ─────────────────────────────────────────────

PAGE_JS = """\
<script>
hljs.highlightAll();
function toggleCard(h){const b=h.nextElementSibling,btn=h.querySelector('.toggle-btn'),c=b.classList.toggle('collapsed');btn.textContent=c?'\\u25b6 Show':'\\u25bc Hide';}
function showAll(){document.querySelectorAll('.card-body').forEach(b=>{b.classList.remove('collapsed');b.closest('.card').querySelector('.toggle-btn').textContent='\\u25bc Hide';});}
function collapseAll(){document.querySelectorAll('.card-body').forEach(b=>{b.classList.add('collapsed');b.closest('.card').querySelector('.toggle-btn').textContent='\\u25b6 Show';});}
const psbInput=document.getElementById('psb-input'),psbCount=document.getElementById('psb-count');
let marks=[],currentIdx=-1;
function clearMarks(){document.querySelectorAll('mark.sh,mark.sh-current').forEach(m=>m.parentNode.replaceChild(document.createTextNode(m.textContent),m));document.querySelectorAll('.card-body code').forEach(c=>c.normalize());marks=[];currentIdx=-1;}
function findAll(term){clearMarks();if(!term.trim()){updateCount();return;}const lower=term.toLowerCase();document.querySelectorAll('.card-body code').forEach(code=>{const walker=document.createTreeWalker(code,NodeFilter.SHOW_TEXT);const nodes=[];let n;while((n=walker.nextNode()))nodes.push(n);nodes.forEach(node=>{const text=node.textContent,ltxt=text.toLowerCase();let pos=0,start;const frags=[];while((start=ltxt.indexOf(lower,pos))!==-1){if(start>pos)frags.push(document.createTextNode(text.slice(pos,start)));const m=document.createElement('mark');m.className='sh';m.textContent=text.slice(start,start+term.length);frags.push(m);marks.push(m);pos=start+term.length;}if(frags.length){if(pos<text.length)frags.push(document.createTextNode(text.slice(pos)));node.replaceWith(...frags);}});});updateCount();}
function goTo(idx){if(!marks.length)return;if(currentIdx>=0)marks[currentIdx].className='sh';currentIdx=((idx%marks.length)+marks.length)%marks.length;marks[currentIdx].className='sh-current';const body=marks[currentIdx].closest('.card-body');if(body&&body.classList.contains('collapsed')){body.classList.remove('collapsed');body.closest('.card').querySelector('.toggle-btn').textContent='\\u25bc Hide';}marks[currentIdx].scrollIntoView({behavior:'smooth',block:'center'});updateCount();}
function nextMatch(){if(marks.length)goTo(currentIdx+1);}
function prevMatch(){if(marks.length)goTo(currentIdx-1);}
function updateCount(){const v=psbInput.value.trim();if(!v){psbCount.textContent='';return;}psbCount.textContent=marks.length===0?'0 matches':(currentIdx+1)+' / '+marks.length;document.getElementById('psb-prev').disabled=marks.length===0;document.getElementById('psb-next').disabled=marks.length===0;}
function applyCardFilter(term){const lower=term.trim().toLowerCase();let shown=0;document.querySelectorAll('.card').forEach(card=>{const has=!lower||card.querySelector('code').textContent.toLowerCase().includes(lower);card.classList.toggle('hidden-by-search',!has);if(has)shown++;});document.getElementById('match-info').textContent=lower?(shown===0?'No match':shown+' card'+(shown>1?'s':'')+' match'):'';}
function runPageSearch(){const term=psbInput.value;applyCardFilter(term);findAll(term);if(marks.length)goTo(0);}
function clearPageSearch(){psbInput.value='';clearMarks();applyCardFilter('');psbCount.textContent='';document.getElementById('psb-prev').disabled=true;document.getElementById('psb-next').disabled=true;document.getElementById('match-info').textContent='';}
function copySearch(){if(psbInput.value)navigator.clipboard.writeText(psbInput.value);}
psbInput.addEventListener('input',runPageSearch);
psbInput.addEventListener('keydown',function(e){if(e.key==='Enter'){e.shiftKey?prevMatch():nextMatch();}if(e.key==='Escape')clearPageSearch();});
window.addEventListener('message',function(e){if(!e.data||e.data.type!=='page-search')return;psbInput.value=e.data.term||'';runPageSearch();});
</script>"""


# ── File discovery ─────────────────────────────────────────────────────────────

def camel_to_words(name: str) -> str:
    """'ObservableBasics' → 'Observable Basics'"""
    return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', name).strip()


def camel_to_snake(name: str) -> str:
    """'ObservableBasics' → 'observable_basics'"""
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)
    s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', s)
    return s.lower()


def collect_files():
    """
    Scan SRC for _NN_ClassName.java files.
    Returns list of dicts: {path, html_name, num, classname, topic, key}
    """
    result = []
    for f in sorted(SRC.glob("_*.java")):
        stem = f.stem.lstrip('_')               # "01_ObservableBasics"
        num, _, classname = stem.partition('_')  # "01", "ObservableBasics"
        if not num.isdigit():
            continue
        topic     = camel_to_words(classname)    # "Observable Basics"
        html_name = f"{num}_{camel_to_snake(classname)}.html"
        key       = classname.lower()            # sidebar data-cls / JS key
        result.append(dict(path=f, html_name=html_name, num=num,
                           classname=classname, topic=topic, key=key))
    return result


# ── Method extraction ─────────────────────────────────────────────────────────

# Matches:  private static void demoCreate() {
#           private static void demoInterval() throws InterruptedException {
METHOD_RE = re.compile(r'^\s+private static \S+ (demo\w+)\s*\(')

# Matches separator comment lines like:
#   // -------------------------------------------------------------------------
#   // ─────────────────────────────────────────────────────────────────────────
SEP_RE = re.compile(r'^\s+// [-─=]{10,}')


def split_into_sections(src: str):
    """
    Split Java source into labelled sections.

    Returns a list of (name, code_str) tuples:
      (None,          header_code)   -- package + imports + class header + main()
      ('demoCreate',  code)          -- separator comment + JavaDoc + method body
      ('demoDefer',   code)
      ...

    The card id used in HTML is  "card-" + name.lower()  (e.g. "card-democreate").
    """
    lines = src.splitlines(keepends=True)

    # Find each demo method and the separator comment that precedes it
    method_starts = []   # list of (method_name, first_line_index_of_section)
    for i, line in enumerate(lines):
        m = METHOD_RE.match(line)
        if not m:
            continue
        method_name = m.group(1)
        # Walk backwards to find the opening separator comment
        section_start = i
        for j in range(i - 1, max(i - 20, -1), -1):
            stripped = lines[j].strip()
            if SEP_RE.match(lines[j]):
                section_start = j
                break
            # Stop if we hit a non-blank, non-comment line (end of previous method body)
            if stripped and not stripped.startswith('//') and stripped != '}':
                break
        method_starts.append((method_name, section_start))

    if not method_starts:
        # No demo methods found — return the whole file as a single section
        return [(None, src.rstrip('\n'))]

    # Header: everything before the first method section
    header_end = method_starts[0][1]
    header = ''.join(lines[:header_end]).rstrip('\n')
    sections = [(None, header)]

    # Each method section runs up to the start of the next one (or end of file)
    for idx, (name, start) in enumerate(method_starts):
        end  = method_starts[idx + 1][1] if idx + 1 < len(method_starts) else len(lines)
        code = ''.join(lines[start:end]).rstrip('\n')
        sections.append((name, code))

    return sections


def method_names(src: str) -> list:
    """Return just the list of demo method names found in src."""
    return [name for name, _ in split_into_sections(src) if name is not None]


# ── Individual page builder ────────────────────────────────────────────────────

def make_page(info: dict) -> str:
    src      = info['path'].read_text(encoding='utf-8')
    sections = split_into_sections(src)
    title    = f"{info['num']} \u2014 {info['topic']}"

    cards = []
    for name, code in sections:
        card_id    = f"card-{name.lower()}" if name else "card-header"
        card_title = f"{name}()" if name else info['path'].name
        escaped    = html.escape(code)
        cards.append(
            f'  <div class="card" id="{card_id}">\n'
            f'    <div class="card-header" onclick="toggleCard(this)">\n'
            f'      <span class="card-filename">{html.escape(card_title)}</span>\n'
            f'      <button class="toggle-btn" onclick="event.stopPropagation()">&#9660; Hide</button>\n'
            f'    </div>\n'
            f'    <div class="card-body">\n'
            f'      <pre><code class="language-java">{escaped}</code></pre>\n'
            f'    </div>\n'
            f'  </div>'
        )

    cards_html = '\n'.join(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{HLJS_CSS}">
{PAGE_CSS}
</head>
<body>
<div id="header">
  <div class="header-top">
    <h1><span class="num">{html.escape(info['num'])}</span>{html.escape(info['topic'])}</h1>
    <div class="toolbar">
      <button onclick="showAll()">&#9660; Show all</button>
      <button onclick="collapseAll()">&#9654; Collapse all</button>
      <span id="match-info" class="match-info"></span>
    </div>
  </div>
  <div class="search-bar">
    <div class="search-input-wrap">
      <input id="psb-input" type="text" placeholder="Search in code..." autocomplete="off" spellcheck="false">
      <button class="search-clear" onclick="clearPageSearch()" title="Clear">&#x2715;</button>
    </div>
    <button id="psb-prev" onclick="prevMatch()" disabled>&#9664; Prev</button>
    <button id="psb-next" onclick="nextMatch()" disabled>Next &#9654;</button>
    <span id="psb-count"></span>
    <button onclick="copySearch()" title="Copy search text">&#x2398; Copy</button>
  </div>
</div>
<div id="cards">
{cards_html}
</div>
<script src="{HLJS_JS}"></script>
<script src="{HLJS_JAVA}"></script>
{PAGE_JS}
</body>
</html>
"""


# ── index.html builder ────────────────────────────────────────────────────────

def make_index(files: list) -> str:
    # Embed full (lowercased) source per file for sidebar search
    js_entries = []
    for info in files:
        src  = info['path'].read_text(encoding='utf-8').lower()
        safe = src.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        js_entries.append(f'  "{info["key"]}": `{safe}`')
    file_code_js = 'const FILE_CODE = {\n' + ',\n'.join(js_entries) + '\n};'

    # Sidebar list items — each file gets a method sub-list
    items = []
    for info in files:
        src     = info['path'].read_text(encoding='utf-8')
        methods = method_names(src)

        # Method sub-list items
        method_items = ''
        for mname in methods:
            card_id    = f"card-{mname.lower()}"
            label      = f"{mname}()"
            href       = f"{info['html_name']}#{card_id}"
            method_items += (
                f'            <li>'
                f'<a href="{href}" target="frame" onclick="setMethodActive(this)">'
                f'{html.escape(label)}</a></li>\n'
            )

        # Method list starts collapsed; toggle button reveals it
        # Use explicit id on the ul so the button can find it without DOM traversal
        ml_id = f'ml-{info["key"]}'
        method_ul = (
            f'          <ul class="method-list collapsed-methods" id="{ml_id}">\n'
            f'{method_items}'
            f'          </ul>\n'
        ) if method_items else ''

        # Visual-only chevron indicator (no onclick — the whole file-row handles toggle)
        chevron = (
            f'<span class="method-toggle" id="btn-{info["key"]}">&#9654;</span>'
        ) if method_items else ''

        # Clicking file name: navigate + let click bubble up to file-row's toggleMethods
        a_onclick = 'onclick="setActive(this);"'

        # Whole file-row toggles the method list when clicked
        row_onclick = f' onclick="toggleMethods(\'{ml_id}\')"' if method_items else ''

        items.append(
            f'          <li data-cls="{info["key"]}">\n'
            f'            <div class="file-row"{row_onclick}>\n'
            f'              <a href="{info["html_name"]}" target="frame" {a_onclick} class="file-link">\n'
            f'                <span class="file-name">{html.escape(info["classname"])}</span>\n'
            f'              </a>\n'
            f'              {chevron}\n'
            f'            </div>\n'
            f'{method_ul}'
            f'          </li>'
        )
    items_html = '\n'.join(items)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RxJava 3.x Tutorial</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#1e1e2e;--sidebar-bg:#181825;--surface:#24273a;
  --text:#cdd6f4;--subtext:#a6adc8;--muted:#585b70;
  --accent:#89b4fa;--accent2:#cba6f7;--green:#a6e3a1;
  --border:#313244;--hover:#45475a;
  --mark-y:#f9e2af;--mark-o:#fab387;--red:#f38ba8;
}}
html,body{{height:100%;overflow:hidden}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;display:flex;flex-direction:column}}
#layout{{display:flex;flex:1;overflow:hidden}}
#sidebar{{width:270px;min-width:270px;background:var(--sidebar-bg);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}}
#content-area{{flex:1;overflow:hidden;display:flex;flex-direction:column}}
#frame{{flex:1;width:100%;border:none;background:var(--bg)}}
#sidebar-header{{padding:14px 14px 10px;border-bottom:1px solid var(--border)}}
.sidebar-title{{font-size:15px;font-weight:700;color:var(--accent2);margin-bottom:2px}}
.sidebar-sub{{font-size:11px;color:var(--muted)}}
#sidebar-search{{padding:10px 12px;border-bottom:1px solid var(--border)}}
.search-wrap{{position:relative;display:flex;align-items:center}}
#search{{width:100%;background:#313244;border:1px solid var(--border);color:var(--text);border-radius:6px;padding:5px 28px 5px 10px;font-size:12px;outline:none}}
#search:focus{{border-color:var(--accent)}}
#search::placeholder{{color:var(--muted)}}
.search-clear{{position:absolute;right:7px;background:none;border:none;color:var(--muted);cursor:pointer;font-size:13px}}
.search-clear:hover{{color:var(--red)}}
#sidebar-controls{{display:flex;gap:6px;padding:8px 12px;border-bottom:1px solid var(--border)}}
#sidebar-controls button{{flex:1;background:var(--hover);border:1px solid var(--border);color:var(--text);border-radius:5px;padding:4px 6px;font-size:11px;cursor:pointer}}
#sidebar-controls button:hover{{background:var(--accent);color:#1e1e2e}}
#version-list{{flex:1;overflow-y:auto;padding:6px 0}}
#version-list::-webkit-scrollbar{{width:5px}}
#version-list::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
.version-group{{border-bottom:1px solid var(--border)}}
.version-group.no-match{{display:none}}
.version-header{{display:flex;align-items:center;gap:6px;padding:8px 12px}}
.version-label{{font-size:12px;font-weight:600;color:var(--accent);flex:1}}
.version-count{{font-size:10px;color:var(--muted)}}
.class-list{{overflow:hidden}}
.version-group.collapsed .class-list{{display:none}}
.class-list li{{list-style:none}}
.class-list li.no-match{{display:none}}
/* ── File row (link + toggle button) ──────────────────────────────── */
.file-row{{display:flex;align-items:center;border-left:2px solid transparent;cursor:pointer}}
.file-row:hover{{background:var(--hover)}}
.file-link{{flex:1;display:flex;align-items:center;padding:5px 4px 5px 28px;
           text-decoration:none;color:var(--text);font-size:12px;min-width:0;transition:color .12s}}
.file-link.active{{color:var(--accent)}}
.file-link.parent-active{{color:var(--accent);opacity:.75}}
.file-row:has(.file-link.active){{background:var(--surface);border-left-color:var(--accent)}}
.file-row:has(.file-link.parent-active){{background:var(--surface);border-left-color:var(--accent)}}
.file-name{{font-family:'JetBrains Mono','Fira Code',Consolas,monospace;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.method-toggle{{color:var(--muted);padding:5px 10px 5px 4px;font-size:10px;flex-shrink:0;user-select:none}}
/* ── Method sub-list ───────────────────────────────────────────────── */
.method-list{{list-style:none;margin-bottom:2px}}
.method-list.collapsed-methods{{display:none}}
.method-list li{{list-style:none}}
.method-list a{{display:block;padding:3px 12px 3px 40px;text-decoration:none;
               color:var(--subtext);font-size:11px;border-left:2px solid transparent;
               font-family:'JetBrains Mono',Consolas,monospace;
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
               transition:background .12s}}
.method-list a:hover{{background:var(--hover);color:var(--text)}}
.method-list a.active{{background:var(--surface);border-left-color:var(--accent2);color:var(--accent2)}}
/* ── No-match / footer ─────────────────────────────────────────────── */
#no-match-msg{{display:none;padding:14px;text-align:center;color:var(--muted);font-size:12px}}
#no-match-msg.visible{{display:block}}
#sidebar-footer{{padding:8px 12px;border-top:1px solid var(--border);font-size:10px;color:var(--muted);text-align:center}}
/* ── Welcome screen ────────────────────────────────────────────────── */
#welcome{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;padding:40px;text-align:center}}
#welcome h2{{font-size:22px;font-weight:700;color:var(--accent2)}}
#welcome p{{color:var(--subtext);max-width:380px;line-height:1.6}}
.badge-row{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:4px}}
.badge{{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:4px 12px;font-size:11px;color:var(--accent);font-family:'JetBrains Mono',Consolas,monospace}}
</style>
</head>
<body>
<div id="layout">
  <div id="sidebar">
    <div id="sidebar-header">
      <div class="sidebar-title">&#9889; RxJava 3.x Tutorial</div>
      <div class="sidebar-sub">{len(files)} topics &nbsp;&#183;&nbsp; Click a file to view</div>
    </div>
    <div id="sidebar-search">
      <div class="search-wrap">
        <input id="search" type="text" placeholder="Search files &amp; code..." autocomplete="off" spellcheck="false">
        <button class="search-clear" id="clear-btn" title="Clear">&#x2715;</button>
      </div>
    </div>
    <div id="sidebar-controls">
      <button id="show-all-btn">&#9660; Expand all</button>
      <button id="collapse-all-btn">&#9654; Collapse all</button>
    </div>
    <div id="version-list">
      <div class="version-group" id="grp-tutorials">
        <div class="version-header">
          <span class="version-label">Tutorial Files</span>
          <span class="version-count">{len(files)} files</span>
        </div>
        <ul class="class-list" id="list-tutorials">
{items_html}
        </ul>
      </div>
    </div>
    <div id="no-match-msg">No files match your search.</div>
    <div id="sidebar-footer">RxJava 3.1.9 &nbsp;&#183;&nbsp; Java 11</div>
  </div>
  <div id="content-area">
    <div id="welcome">
      <h2>&#9889; RxJava 3.x Tutorial</h2>
      <p>Select a tutorial file from the left panel to view its Java source code with syntax highlighting, search, and collapse controls.</p>
      <div class="badge-row">
        <span class="badge">Observable</span>
        <span class="badge">Flowable</span>
        <span class="badge">Schedulers</span>
        <span class="badge">Subjects</span>
        <span class="badge">map / flatMap</span>
        <span class="badge">filter / zip</span>
        <span class="badge">Single</span>
        <span class="badge">Maybe</span>
        <span class="badge">Completable</span>
        <span class="badge">Backpressure</span>
      </div>
    </div>
    <iframe id="frame" name="frame" style="display:none"></iframe>
  </div>
</div>
<script>
{file_code_js}

// Expand/collapse all method sub-lists
document.getElementById('show-all-btn').addEventListener('click',function(){{
  document.querySelectorAll('.method-list').forEach(ul=>{{
    ul.classList.remove('collapsed-methods');
    const btn=document.getElementById('btn-'+ul.id.replace('ml-',''));
    if(btn)btn.textContent='\\u25bc';
  }});
}});
document.getElementById('collapse-all-btn').addEventListener('click',function(){{
  document.querySelectorAll('.method-list').forEach(ul=>{{
    ul.classList.add('collapsed-methods');
    const btn=document.getElementById('btn-'+ul.id.replace('ml-',''));
    if(btn)btn.textContent='\\u25b6';
  }});
}});

function clearAllActive(){{
  document.querySelectorAll('#version-list a').forEach(a=>{{
    a.classList.remove('active');
    a.classList.remove('parent-active');
  }});
}}

// Toggle the method sub-list by ul id (e.g. 'ml-observablebasics')
function toggleMethods(ulId){{
  const ul=document.getElementById(ulId);
  const btn=document.getElementById('btn-'+ulId.replace('ml-',''));
  if(!ul)return;
  const collapsed=ul.classList.toggle('collapsed-methods');
  if(btn)btn.textContent=collapsed?'\\u25b6':'\\u25bc';
}}

// Expand a method sub-list without toggling (used when navigating to a file)
function expandMethods(ulId){{
  const ul=document.getElementById(ulId);
  const btn=document.getElementById('btn-'+ulId.replace('ml-',''));
  if(ul){{ul.classList.remove('collapsed-methods');if(btn)btn.textContent='\\u25bc';}}
}}

// Called when clicking a file-level link
function setActive(el){{
  clearAllActive();
  el.classList.add('active');
  document.getElementById('welcome').style.display='none';
  document.getElementById('frame').style.display='block';
}}

// Called when clicking a method sub-item link
function setMethodActive(el){{
  clearAllActive();
  el.classList.add('active');
  // Mark parent file link as parent-active and expand its method list
  const fileItem=el.closest('li[data-cls]');
  if(fileItem){{
    const fileLink=fileItem.querySelector('.file-link');
    if(fileLink)fileLink.classList.add('parent-active');
    const cls=fileItem.dataset.cls;
    const ul=document.getElementById('ml-'+cls);
    const btn=document.getElementById('btn-'+cls);
    if(ul){{ul.classList.remove('collapsed-methods');if(btn)btn.textContent='\\u25bc';}}
  }}
  document.getElementById('welcome').style.display='none';
  document.getElementById('frame').style.display='block';
}}

const searchInput=document.getElementById('search');
const clearBtn=document.getElementById('clear-btn');

function filterMenu(term){{
  const lower=term.trim().toLowerCase();
  let anyVisible=false;
  // Only filter file-level li items (those with data-cls); method sub-items follow their parent
  document.querySelectorAll('.version-group li[data-cls]').forEach(function(li){{
    const cls=(li.dataset.cls||'');
    const src=FILE_CODE[cls]||'';
    const match=!lower||cls.includes(lower)||src.includes(lower);
    li.classList.toggle('no-match',!match);
    if(match)anyVisible=true;
  }});
  document.getElementById('no-match-msg').classList.toggle('visible',!!lower&&!anyVisible);
}}

function sendSearch(term){{
  const frame=document.getElementById('frame');
  if(frame.contentWindow)frame.contentWindow.postMessage({{type:'page-search',term:term}},'*');
}}

searchInput.addEventListener('input',function(){{filterMenu(this.value);sendSearch(this.value);}});
clearBtn.addEventListener('click',function(){{searchInput.value='';filterMenu('');sendSearch('');searchInput.focus();}});
searchInput.addEventListener('keydown',function(e){{if(e.key==='Escape'){{searchInput.value='';filterMenu('');sendSearch('');}}}});
document.getElementById('frame').addEventListener('load',function(){{if(searchInput.value)sendSearch(searchInput.value);}});
</script>
</body>
</html>
"""


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    files = collect_files()
    if not files:
        print(f'No _NN_ClassName.java files found in: {SRC}')
        raise SystemExit(1)

    print(f'Source folder : {SRC}')
    print(f'Output folder : {HERE}')
    print()

    for info in files:
        src      = info['path'].read_text(encoding='utf-8')
        sections = split_into_sections(src)
        methods  = [n for n, _ in sections if n]
        page     = make_page(info)
        out      = HERE / info['html_name']
        out.write_text(page, encoding='utf-8')
        print(f'  {info["path"].name:42s} -> {info["html_name"]}  ({len(methods)} method cards)')

    index = make_index(files)
    (HERE / 'index.html').write_text(index, encoding='utf-8')
    print(f'  {"index.html":42s} -> index.html')
    print()
    print('Done. Open html_preview/index.html in your browser.')
