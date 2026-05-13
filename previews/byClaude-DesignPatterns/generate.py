#!/usr/bin/env python3
"""Generate static HTML preview pages for the Design Patterns project."""

import os
import html as html_lib

BASE = r"C:\Users\roman\Work\claude\projects\DesignPatterns"
OUT  = os.path.join(BASE, "html_preview")

NAMES = {
    "AbstractFactory": "Abstract Factory", "abstractFactory": "Abstract Factory",
    "Builder":         "Builder",          "builder":         "Builder",
    "FactoryMethod":   "Factory Method",   "factoryMethod":   "Factory Method",
    "Prototype":       "Prototype",        "prototype":       "Prototype",
    "Singleton":       "Singleton",        "singleton":       "Singleton",
    "Adapter":         "Adapter",          "adapter":         "Adapter",
    "Composite":       "Composite",        "composite":       "Composite",
    "Decorator":       "Decorator",        "decorator":       "Decorator",
    "Facade":          "Facade",           "facade":          "Facade",
    "Proxy":           "Proxy",            "proxy":           "Proxy",
    "Command":         "Command",          "command":         "Command",
    "Iterator":        "Iterator",         "iterator":        "Iterator",
    "Observer":        "Observer",         "observer":        "Observer",
    "Strategy":        "Strategy",         "strategy":        "Strategy",
    "TemplateMethod":  "Template Method",  "templateMethod":  "Template Method",
}

LANGS = [
    {
        "id": "java", "display": "Java", "ext": ".java",
        "hljs_class": "language-java",
        "hljs_extra": '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>',
        "groups": [
            {"id": "creational", "display": "Creational",
             "patterns": ["AbstractFactory", "Builder", "FactoryMethod", "Prototype", "Singleton"]},
            {"id": "structural",  "display": "Structural",
             "patterns": ["Adapter", "Composite", "Decorator", "Facade", "Proxy"]},
            {"id": "behavioral",  "display": "Behavioral",
             "patterns": ["Command", "Iterator", "Observer", "Strategy", "TemplateMethod"]},
        ],
    },
    {
        "id": "javascript", "display": "JavaScript", "ext": ".js",
        "hljs_class": "language-javascript", "hljs_extra": "",
        "groups": [
            {"id": "creational", "display": "Creational",
             "patterns": ["abstractFactory", "builder", "factoryMethod", "prototype", "singleton"]},
            {"id": "structural",  "display": "Structural",
             "patterns": ["adapter", "composite", "decorator", "facade", "proxy"]},
            {"id": "behavioral",  "display": "Behavioral",
             "patterns": ["command", "iterator", "observer", "strategy", "templateMethod"]},
        ],
    },
    {
        "id": "typescript", "display": "TypeScript", "ext": ".ts",
        "hljs_class": "language-typescript",
        "hljs_extra": '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/typescript.min.js"></script>',
        "groups": [
            {"id": "creational", "display": "Creational",
             "patterns": ["abstractFactory", "builder", "factoryMethod", "prototype", "singleton"]},
            {"id": "structural",  "display": "Structural",
             "patterns": ["adapter", "composite", "decorator", "facade", "proxy"]},
            {"id": "behavioral",  "display": "Behavioral",
             "patterns": ["command", "iterator", "observer", "strategy", "templateMethod"]},
        ],
    },
]

# ── CSS shared by all pattern pages ───────────────────────────────────────────
PAGE_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow: hidden; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; display: flex; flex-direction: column; }
    #page-header { flex-shrink: 0; background: #f0f2f5; padding: 16px 20px 10px; border-bottom: 1px solid #e2e8f0; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
    h1 { color: #2d3748; margin-bottom: 10px; font-size: 1.3rem; }
    .breadcrumb { font-size: 0.82rem; font-weight: 400; color: #718096; }
    .toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
    .toolbar button { padding: 5px 13px; border: none; border-radius: 5px; cursor: pointer; font-size: 0.82rem; font-weight: 600; transition: background 0.15s; }
    .btn-show { background: #3182ce; color: #fff; }
    .btn-show:hover { background: #2b6cb0; }
    .btn-hide { background: #718096; color: #fff; }
    .btn-hide:hover { background: #4a5568; }
    .match-info { font-size: 0.82rem; color: #718096; margin-left: 4px; }
    .page-search-bar { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; background: #fff; border: 1px solid #cbd5e0; border-radius: 7px; padding: 6px 12px; }
    .page-search-bar input { flex: 1; min-width: 160px; padding: 5px 8px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.85rem; outline: none; color: #2d3748; }
    .page-search-bar input:focus { border-color: #63b3ed; }
    .psb-btn { padding: 5px 11px; border: 1px solid #cbd5e0; border-radius: 5px; background: #f7fafc; cursor: pointer; font-size: 0.8rem; color: #4a5568; transition: background 0.12s; }
    .psb-btn:hover { background: #e2e8f0; }
    .psb-btn:disabled { opacity: 0.4; cursor: default; }
    .psb-clear { padding: 5px 9px; border: 1px solid #cbd5e0; border-radius: 5px; background: #f7fafc; cursor: pointer; font-size: 0.85rem; color: #718096; transition: background 0.12s; }
    .psb-clear:hover { background: #fed7d7; color: #c53030; border-color: #fc8181; }
    .psb-count { font-size: 0.8rem; color: #718096; white-space: nowrap; min-width: 60px; }
    mark.sh { background: #fef08a; color: inherit; border-radius: 2px; padding: 0 1px; }
    mark.sh-current { background: #f97316; color: #fff; border-radius: 2px; padding: 0 1px; }
    #cards-container { flex: 1; overflow-y: auto; padding: 20px; }
    .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
    .card.hidden-by-search { display: none; }
    .card-header { background: #2d3748; color: #e2e8f0; padding: 9px 14px; display: flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; }
    .card-header:hover { background: #3a4a5c; }
    .card-header .filename { font-size: 0.9rem; font-weight: 700; flex: 1; }
    .card-header .path { color: #a0aec0; font-size: 0.78rem; }
    .card-header .toggle-btn { background: none; border: 1px solid #4a5568; border-radius: 4px; color: #a0aec0; font-size: 0.75rem; padding: 2px 8px; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
    .card-header .toggle-btn:hover { border-color: #63b3ed; color: #63b3ed; }
    .card-body { display: block; }
    .card-body.collapsed { display: none; }
    pre { margin: 0; overflow-x: auto; }
    pre code.hljs { font-size: 13px; line-height: 1.5; padding: 16px !important; }
"""

# ── JS shared by all pattern pages ────────────────────────────────────────────
PAGE_JS = r"""
    document.addEventListener('DOMContentLoaded', () => hljs.highlightAll());

    function toggleCard(header) {
      const body = header.nextElementSibling;
      const btn  = header.querySelector('.toggle-btn');
      btn.textContent = body.classList.toggle('collapsed') ? '▶ Show' : '▼ Hide';
    }
    function showAll() {
      document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {
        b.classList.remove('collapsed');
        b.closest('.card').querySelector('.toggle-btn').textContent = '▼ Hide';
      });
    }
    function collapseAll() {
      document.querySelectorAll('.card:not(.hidden-by-search) .card-body').forEach(b => {
        b.classList.add('collapsed');
        b.closest('.card').querySelector('.toggle-btn').textContent = '▶ Show';
      });
    }

    let allMatches = [], curIdx = -1;

    function applyCardFilter(term) {
      let n = 0;
      document.querySelectorAll('.card').forEach(c => {
        const show = !term || c.textContent.toLowerCase().includes(term.toLowerCase());
        c.classList.toggle('hidden-by-search', !show);
        if (show && term) n++;
      });
      document.getElementById('match-info').textContent =
        term ? n + ' card' + (n !== 1 ? 's' : '') + ' match' : '';
    }

    function clearMarks() {
      Array.from(document.querySelectorAll('mark.sh')).forEach(m => {
        const p = m.parentNode;
        if (p) p.replaceChild(document.createTextNode(m.textContent), m);
      });
      document.getElementById('cards-container').normalize();
    }

    function findAll(term) {
      clearMarks(); allMatches = []; curIdx = -1;
      if (!term) { upd(); return; }
      const lc = term.toLowerCase();
      const walker = document.createTreeWalker(
        document.getElementById('cards-container'), NodeFilter.SHOW_TEXT);
      const nodes = [];
      let n;
      while ((n = walker.nextNode())) nodes.push(n);
      nodes.forEach(tn => {
        const val = tn.nodeValue, lv = val.toLowerCase();
        let i = lv.indexOf(lc), off = 0;
        if (i < 0) return;
        const frag = document.createDocumentFragment();
        while (i >= 0) {
          if (i > off) frag.appendChild(document.createTextNode(val.slice(off, i)));
          const m = document.createElement('mark');
          m.className = 'sh'; m.textContent = val.slice(i, i + term.length);
          frag.appendChild(m); allMatches.push(m);
          off = i + term.length; i = lv.indexOf(lc, off);
        }
        if (off < val.length) frag.appendChild(document.createTextNode(val.slice(off)));
        tn.parentNode.replaceChild(frag, tn);
      });
      upd();
      if (allMatches.length) goTo(0);
    }

    function goTo(i) {
      if (!allMatches.length) return;
      if (curIdx >= 0) allMatches[curIdx].className = 'sh';
      curIdx = ((i % allMatches.length) + allMatches.length) % allMatches.length;
      allMatches[curIdx].className = 'sh sh-current';
      allMatches[curIdx].scrollIntoView({ behavior: 'smooth', block: 'center' });
      upd();
    }

    function upd() {
      const inp = document.getElementById('psb-input').value;
      document.getElementById('psb-count').textContent =
        allMatches.length ? (curIdx + 1) + ' / ' + allMatches.length
        : (inp ? '0 matches' : '');
      const has = allMatches.length > 0;
      document.getElementById('psb-prev').disabled = !has;
      document.getElementById('psb-next').disabled = !has;
    }

    function nextMatch() { if (allMatches.length) goTo(curIdx + 1); }
    function prevMatch() { if (allMatches.length) goTo(curIdx - 1); }

    function clearPageSearch() {
      document.getElementById('psb-input').value = '';
      clearMarks(); allMatches = []; curIdx = -1;
      document.getElementById('psb-count').textContent = '';
      document.getElementById('match-info').textContent = '';
      document.querySelectorAll('.card').forEach(c => c.classList.remove('hidden-by-search'));
      upd();
    }

    document.getElementById('psb-input').addEventListener('input', function() {
      const t = this.value.trim();
      applyCardFilter(t); findAll(t);
    });
    document.getElementById('psb-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') { e.preventDefault(); e.shiftKey ? prevMatch() : nextMatch(); }
      if (e.key === 'Escape') clearPageSearch();
    });
"""

# ── CSS for index.html ────────────────────────────────────────────────────────
INDEX_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; }
    #layout { display: flex; height: 100vh; }

    #sidebar { width: 270px; min-width: 270px; background: #1a202c; color: #e2e8f0; display: flex; flex-direction: column; overflow-y: auto; }
    #sidebar h2 { padding: 18px 16px 12px; font-size: 0.85rem; font-weight: 700; color: #63b3ed; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #2d3748; flex-shrink: 0; }

    .lang-list { list-style: none; padding: 4px 0; flex: 1; }
    .lang-item { border-bottom: 1px solid #2d3748; }
    .lang-toggle { display: flex; align-items: center; gap: 8px; padding: 10px 16px; font-size: 0.9rem; font-weight: 700; color: #e2e8f0; cursor: pointer; user-select: none; transition: background 0.12s; }
    .lang-toggle:hover { background: #2d3748; }

    .group-list { list-style: none; }
    .group-item {}
    .group-toggle { display: flex; align-items: center; gap: 8px; padding: 7px 16px 7px 28px; font-size: 0.82rem; font-weight: 600; color: #a0aec0; cursor: pointer; user-select: none; transition: background 0.12s; }
    .group-toggle:hover { background: #2d3748; color: #e2e8f0; }

    .pattern-list { list-style: none; }
    .pattern-list li a { display: block; padding: 6px 16px 6px 44px; color: #718096; text-decoration: none; font-size: 0.83rem; border-left: 3px solid transparent; transition: background 0.12s, color 0.12s; }
    .pattern-list li a:hover { background: #2d3748; color: #e2e8f0; }
    .pattern-list li a.active { background: #2d3748; color: #63b3ed; border-left-color: #63b3ed; }

    .arrow { font-size: 0.65rem; display: inline-block; transition: transform 0.18s; }
    .arrow.rotated { transform: rotate(-90deg); }
    .hidden { display: none; }

    #content { flex: 1; overflow: hidden; }
    #content iframe { width: 100%; height: 100%; border: none; }
"""

INDEX_JS = r"""
  function toggleSection(id) {
    const el  = document.getElementById(id);
    const arr = document.getElementById('arr-' + id);
    el.classList.toggle('hidden');
    arr.classList.toggle('rotated');
  }
  function setActive(link) {
    document.querySelectorAll('.pattern-list a').forEach(a => a.classList.remove('active'));
    link.classList.add('active');
  }
  document.addEventListener('DOMContentLoaded', () => {
    const first = document.querySelector('.pattern-list a');
    if (first) first.classList.add('active');
  });
"""


def make_pattern_page(lang, group, pattern):
    src = os.path.join(BASE, lang["id"], group["id"], pattern + lang["ext"])
    with open(src, encoding="utf-8") as f:
        code_escaped = html_lib.escape(f.read(), quote=False)

    name     = NAMES[pattern]
    fname    = pattern + lang["ext"]
    rel_path = f"{lang['id']}/{group['id']}/{fname}"
    title    = f"{name} — {lang['display']} | Design Patterns"
    heading  = f"{name} <span class=\"breadcrumb\">— {lang['display']} › {group['display']}</span>"
    hljs_ex  = (f"\n  {lang['hljs_extra']}") if lang["hljs_extra"] else ""

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        f"  <title>{title}</title>\n"
        "  <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css\">\n"
        "  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>"
        f"{hljs_ex}\n"
        f"  <style>{PAGE_CSS}  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <div id=\"page-header\">\n"
        f"    <h1>{heading}</h1>\n"
        "    <div class=\"toolbar\">\n"
        "      <button class=\"btn-show\" onclick=\"showAll()\">&#9660; Show all</button>\n"
        "      <button class=\"btn-hide\" onclick=\"collapseAll()\">&#9654; Collapse all</button>\n"
        "      <span class=\"match-info\" id=\"match-info\"></span>\n"
        "    </div>\n"
        "    <div class=\"page-search-bar\">\n"
        "      <input id=\"psb-input\" type=\"text\" placeholder=\"&#128269; Search in code&hellip;\" autocomplete=\"off\">\n"
        "      <button class=\"psb-btn\" id=\"psb-prev\" onclick=\"prevMatch()\" disabled title=\"Previous (Shift+Enter)\">&#9650; Prev</button>\n"
        "      <button class=\"psb-btn\" id=\"psb-next\" onclick=\"nextMatch()\" disabled title=\"Next (Enter)\">&#9660; Next</button>\n"
        "      <button class=\"psb-clear\" onclick=\"clearPageSearch()\" title=\"Clear (Esc)\">&#x2715;</button>\n"
        "      <span class=\"psb-count\" id=\"psb-count\"></span>\n"
        "    </div>\n"
        "  </div>\n"
        "  <div id=\"cards-container\">\n"
        "    <div class=\"card\">\n"
        "      <div class=\"card-header\" onclick=\"toggleCard(this)\">\n"
        f"        <span class=\"filename\">{fname}</span>\n"
        f"        <span class=\"path\">{rel_path}</span>\n"
        "        <button class=\"toggle-btn\""
        " onclick=\"event.stopPropagation();toggleCard(this.closest('.card-header'))\">&#9660; Hide</button>\n"
        "      </div>\n"
        "      <div class=\"card-body\">\n"
        f"        <pre><code class=\"{lang['hljs_class']}\">{code_escaped}</code></pre>\n"
        "      </div>\n"
        "    </div>\n"
        "  </div>\n"
        f"  <script>{PAGE_JS}  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def make_index():
    sidebar = ""
    for lang in LANGS:
        lang_id = f"lang-{lang['id']}"
        sidebar += f'  <li class="lang-item">\n'
        sidebar += f'    <div class="lang-toggle" onclick="toggleSection(\'{lang_id}\')">\n'
        sidebar += f'      <span class="arrow" id="arr-{lang_id}">&#9660;</span> {lang["display"]}\n'
        sidebar += f'    </div>\n'
        sidebar += f'    <ul class="group-list" id="{lang_id}">\n'
        for group in lang["groups"]:
            group_id = f"group-{lang['id']}-{group['id']}"
            sidebar += f'      <li class="group-item">\n'
            sidebar += f'        <div class="group-toggle" onclick="toggleSection(\'{group_id}\')">\n'
            sidebar += f'          <span class="arrow" id="arr-{group_id}">&#9660;</span> {group["display"]}\n'
            sidebar += f'        </div>\n'
            sidebar += f'        <ul class="pattern-list" id="{group_id}">\n'
            for pattern in group["patterns"]:
                href = f"{lang['id']}/{group['id']}/{pattern}.html"
                sidebar += (
                    f'          <li><a href="{href}" target="content"'
                    f' onclick="setActive(this)">{NAMES[pattern]}</a></li>\n'
                )
            sidebar += f'        </ul>\n'
            sidebar += f'      </li>\n'
        sidebar += f'    </ul>\n'
        sidebar += f'  </li>\n'

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <title>Design Patterns — Code Preview</title>\n"
        f"  <style>{INDEX_CSS}  </style>\n"
        "</head>\n"
        "<body>\n"
        "<div id=\"layout\">\n"
        "  <nav id=\"sidebar\">\n"
        "    <h2>Design Patterns</h2>\n"
        "    <ul class=\"lang-list\">\n"
        + sidebar +
        "    </ul>\n"
        "  </nav>\n"
        "  <div id=\"content\">\n"
        "    <iframe name=\"content\" id=\"frame\" src=\"java/creational/Singleton.html\"></iframe>\n"
        "  </div>\n"
        "</div>\n"
        "<script>\n"
        + INDEX_JS +
        "</script>\n"
        "</body>\n"
        "</html>\n"
    )


def main():
    count = 0
    for lang in LANGS:
        for group in lang["groups"]:
            for pattern in group["patterns"]:
                content  = make_pattern_page(lang, group, pattern)
                out_path = os.path.join(OUT, lang["id"], group["id"], pattern + ".html")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  {lang['id']}/{group['id']}/{pattern}.html")
                count += 1

    index_path = os.path.join(OUT, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(make_index())
    print(f"  index.html")
    count += 1
    print(f"\nDone — {count} files generated.")


if __name__ == "__main__":
    main()
