(function () {
  'use strict';

  // ── Utilities ──────────────────────────────────────────────────────────────

  function esc(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }


  // ── Project registry ───────────────────────────────────────────────────────

  const registry = {};

  function registerItems(items) {
    for (const item of items) {
      if (item.type === 'project') registry[item.id] = item;
      else if (item.type === 'group') registerItems(item.items);
    }
  }

  function initRegistry() {
    for (const key of Object.keys(window.PROJECTS)) {
      registerItems(window.PROJECTS[key].items);
    }
  }

  // ── Sidebar ────────────────────────────────────────────────────────────────

  function countProjects(items) {
    return items.reduce((n, item) =>
      n + (item.type === 'group' ? countProjects(item.items) : 1), 0);
  }

  function renderItems(items, nested) {
    return items.map(item => {
      if (item.type === 'project') {
        const cls = 'nav-item' + (nested ? ' nested' : '');
        return `<div class="${cls}" data-id="${esc(item.id)}">${esc(item.name)}</div>`;
      }
      if (item.type === 'group') {
        return `
<div class="nav-subgroup" data-subgroup="${esc(item.id)}">
  <div class="nav-subgroup-header">
    ${esc(item.name)}
    <span class="nav-group-count">${countProjects(item.items)}</span>
  </div>
  <div class="nav-subgroup-body">${renderItems(item.items, true)}</div>
</div>`;
      }
      return '';
    }).join('');
  }

  function buildNav() {
    const nav = document.getElementById('nav');
    const groups = window.PROJECTS;
    const ORDER  = ['shopping', 'others', 'byClaude'];
    let totalProjects = 0;
    let html = '';

    for (const key of ORDER) {
      const group = groups[key];
      if (!group) continue;
      const cnt = countProjects(group.items);
      totalProjects += cnt;
      html += `
<div class="nav-group" data-group="${esc(key)}">
  <div class="nav-group-header">
    ${esc(group.name)}
    <span class="nav-group-count">${cnt}</span>
  </div>
  <div class="nav-group-body">${renderItems(group.items, false)}</div>
</div>`;
    }

    html += `<div class="nav-packages-item" id="nav-packages">📦 Packages &amp; POM</div>`;
    nav.innerHTML = html;
    const stats = document.getElementById('welcome-stats');
    if (stats) stats.textContent = `${totalProjects} projects in 3 groups`;
  }

  // ── Collapse toggling (event delegation) ───────────────────────────────────

  document.addEventListener('click', function (e) {
    const navPkgItem = e.target.closest('.nav-packages-item');
    if (navPkgItem) { renderPackages(); return; }

    const groupHeader = e.target.closest('.nav-group-header');
    if (groupHeader) { groupHeader.closest('.nav-group').classList.toggle('collapsed'); return; }

    const subHeader = e.target.closest('.nav-subgroup-header');
    if (subHeader) { subHeader.closest('.nav-subgroup').classList.toggle('collapsed'); return; }

    const navItem = e.target.closest('.nav-item');
    if (navItem && navItem.dataset.id) { selectProject(navItem.dataset.id); return; }

    const panelHeader = e.target.closest('.panel-header');
    if (panelHeader) { panelHeader.closest('.panel').classList.toggle('open'); return; }

    const btnScreens = e.target.closest('.btn-screens');
    if (btnScreens) {
      const gridId = btnScreens.dataset.grid;
      const grid   = document.getElementById(gridId);
      if (grid) {
        const visible = grid.classList.toggle('visible');
        const cnt     = grid.querySelectorAll('.screenshot-wrap').length;
        btnScreens.textContent = (visible ? '▲ Hide' : '▼ Show') + ` screens (${cnt})`;
      }
      return;
    }
  });

  // ── Project selection ──────────────────────────────────────────────────────

  function selectProject(id) {
    const project = registry[id];
    if (!project) return;
    document.querySelectorAll('.nav-item').forEach(el =>
      el.classList.toggle('active', el.dataset.id === id));
    const navPkg = document.getElementById('nav-packages');
    if (navPkg) navPkg.classList.remove('active');
    history.replaceState(null, '', '#' + encodeURIComponent(id));
    renderProject(project);
  }

  // ── Rendering helpers ──────────────────────────────────────────────────────

  function renderStack(stack) {
    if (!stack) return '';
    const rows = [
      { label: 'Language',     value: (stack.language || []).join(', ') },
      { label: 'Frontend',     value: stack.frontend || '' },
      { label: 'Backend',      value: (stack.backend  || []).join(', ') },
      { label: 'Database',     value: (stack.database || []).join(', ') },
      { label: 'UI Framework', value: (stack.ui       || []).join(', ') },
      { label: 'Tools / API',  value: (stack.tools    || []).join(', ') },
    ].filter(r => r.value);
    if (!rows.length) return '';
    return `
<div class="stack-section">
  <h2>Tech Stack</h2>
  <div class="stack-grid">
    ${rows.map(r => `
    <div class="stack-card">
      <div class="s-label">${esc(r.label)}</div>
      <div class="s-value">${esc(r.value)}</div>
    </div>`).join('')}
  </div>
</div>`;
  }

  function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
      return `<div class="md-content">${marked.parse(text)}</div>`;
    }
    // fallback if CDN unavailable
    return `<div class="about-text">${esc(text)}</div>`;
  }

  function makePanel(icon, title, bodyHtml) {
    return `
<div class="panel">
  <div class="panel-header">
    ${icon} ${esc(title)} <span class="panel-arrow">▶</span>
  </div>
  <div class="panel-body">${bodyHtml}</div>
</div>`;
  }

  function renderPanels(project) {
    let html = '<div class="panels">';

    if (project.readme) {
      html += makePanel('📖', 'README.md', renderMarkdown(project.readme));
    }
    if (project.aboutTxt) {
      html += makePanel('📄', 'about.txt',
        `<div class="about-text">${esc(project.aboutTxt)}</div>`);
    }
    if (project.commentsTxt) {
      html += makePanel('💬', 'comments.txt',
        `<div class="about-text">${esc(project.commentsTxt)}</div>`);
    }
    for (const bf of (project.buildFiles || [])) {
      const icon = bf.name.includes('pom') ? '☕' : '📦';
      html += makePanel(icon, bf.name,
        `<pre class="file-content">${esc(bf.content)}</pre>`);
    }

    html += '</div>';
    return html;
  }

  function renderSubfolders(project) {
    const subs = (project.subfolders || []).filter(sf =>
      sf.readme || (sf.buildFiles && sf.buildFiles.length));
    if (!subs.length) return '';

    let html = '';
    for (const sf of subs) {
      let inner = '';

      // Only show subfolder stack if it adds new info vs root stack
      const sfStack = sf.stack || {};
      const rootStack = project.stack || {};
      const hasNewInfo = (sfStack.frontend && sfStack.frontend !== rootStack.frontend)
        || (sfStack.backend || []).some(b => !(rootStack.backend || []).includes(b))
        || (sfStack.database || []).some(d => !(rootStack.database || []).includes(d));
      if (hasNewInfo) inner += renderStack(sfStack);

      if (sf.readme) {
        inner += makePanel('📖', 'README.md', renderMarkdown(sf.readme));
      }
      for (const bf of (sf.buildFiles || [])) {
        const icon = bf.name.includes('pom') ? '☕' : '📦';
        inner += makePanel(icon, bf.name,
          `<pre class="file-content">${esc(bf.content)}</pre>`);
      }

      html += `
<div class="subfolder-section">
  <div class="subfolder-title">📁 ${esc(sf.name)}</div>
  <div class="panels">${inner}</div>
</div>`;
    }
    return html;
  }

  function renderScreenshots(project) {
    if (!project.screenshots || !project.screenshots.length) return '';
    const gridId = 'screens-' + project.id;
    const imgs   = project.screenshots.map(s => `
<div class="screenshot-wrap">
  <img src="${esc(s)}" alt="screenshot"
       title="Click to open full size"
       onclick="window.open('${esc(s)}','_blank')">
</div>`).join('');
    return `
<div class="screenshots-section">
  <button class="btn-screens" data-grid="${gridId}">
    ▲ Hide screens (${project.screenshots.length})
  </button>
  <div class="screenshots-grid visible" id="${gridId}">${imgs}</div>
</div>`;
  }

  function renderExamples(project) {
    const examples = project.examples || [];
    if (!examples.length) return '';
    let html = '';
    for (const ex of examples) {
      let inner = '';
      if (ex.screenshots && ex.screenshots.length) {
        const gridId = 'screens-' + project.id + '--' + ex.name;
        const imgs = ex.screenshots.map(s => `
<div class="screenshot-wrap">
  <img src="${esc(s)}" alt="screenshot" title="Click to open full size"
       onclick="window.open('${esc(s)}','_blank')">
</div>`).join('');
        inner += `
<div class="screenshots-section">
  <button class="btn-screens" data-grid="${gridId}">▼ Show screens (${ex.screenshots.length})</button>
  <div class="screenshots-grid" id="${gridId}">${imgs}</div>
</div>`;
      }
      if (ex.readme) inner += makePanel('📖', 'README.md', renderMarkdown(ex.readme));
      for (const bf of (ex.buildFiles || [])) {
        const icon = bf.name.includes('pom') ? '☕' : '📦';
        inner += makePanel(icon, bf.name, `<pre class="file-content">${esc(bf.content)}</pre>`);
      }
      html += `
<div class="subfolder-section">
  <div class="subfolder-title">📁 ${esc(ex.name)}</div>
  <div class="panels">${inner}</div>
</div>`;
    }
    return html;
  }

  function renderProject(project) {
    const githubHtml = project.github
      ? `<a class="github-link" href="${esc(project.github)}" target="_blank" rel="noopener">⎈ GitHub</a>`
      : '';

    document.getElementById('content').innerHTML = `
<div class="project-page">
  <div class="project-header">
    <h1>${esc(project.name)}</h1>
    <div class="project-meta">
      <span class="project-path">${esc(project.path)}</span>
      ${githubHtml}
    </div>
  </div>
  ${renderStack(project.stack)}
  ${renderScreenshots(project)}
  ${renderPanels(project)}
  ${renderSubfolders(project)}
  ${renderExamples(project)}
</div>`;
  }

  // ── Packages & POM view ────────────────────────────────────────────────────

  let pkgAllRows = [];

  const PKG_PATH_PREFIXES = {
    'Shopping': 'C:\\Users\\roman\\Work\\pohovor\\projects\\shopping',
    'Others':   'C:\\Users\\roman\\Work\\pohovor\\projects',
    'By Claude':'C:\\Users\\roman\\Work\\claude\\projects',
  };

  function shortPath(fullPath, groupName) {
    const prefix = PKG_PATH_PREFIXES[groupName];
    if (!prefix) return fullPath;
    // normalise separators for comparison
    const normFull   = fullPath.replace(/\//g, '\\');
    const normPrefix = prefix.replace(/\//g, '\\');
    if (normFull.toLowerCase().startsWith(normPrefix.toLowerCase())) {
      return '…' + normFull.slice(normPrefix.length);
    }
    return fullPath;
  }

  const PKG_NOISE = new Set([
    'tslib', 'zone.js', 'popper.js', '@popperjs/core', 'core-js', 'reflect-metadata',
  ]);

  function groupPackageNames(deps) {
    const groups = new Map();
    deps.filter(d => !PKG_NOISE.has(d)).forEach(dep => {
      const root = dep.startsWith('@') ? dep.split('/')[0] : dep.split('-')[0];
      if (!groups.has(root)) groups.set(root, []);
      groups.get(root).push(dep);
    });
    const result = [];
    groups.forEach((names, root) => result.push(names.length >= 2 ? root : names[0]));
    return result.sort().join(', ');
  }

  function extractPackageJsonDeps(content) {
    let pkg;
    try { pkg = JSON.parse(content); } catch (e) { return ''; }
    return groupPackageNames(Object.keys(pkg.dependencies || {}));
  }

  function extractPackageJsonDevDeps(content) {
    let pkg;
    try { pkg = JSON.parse(content); } catch (e) { return ''; }
    return groupPackageNames(Object.keys(pkg.devDependencies || {}));
  }

  function parsePomDepBlocks(content) {
    const depsMatch = content.match(/<dependencies>([\s\S]*?)<\/dependencies>/);
    if (!depsMatch) return { main: [], test: [] };
    const main = [], test = [];
    const re = /<dependency>([\s\S]*?)<\/dependency>/g;
    let m;
    while ((m = re.exec(depsMatch[1])) !== null) {
      const block = m[1];
      const idMatch = block.match(/<artifactId>([^<]+)<\/artifactId>/);
      if (!idMatch) continue;
      const id = idMatch[1].trim();
      if (/<scope>\s*test\s*<\/scope>/i.test(block)) test.push(id);
      else main.push(id);
    }
    return { main, test };
  }

  function extractDependencies(row) {
    if (row.fileType === 'package') return extractPackageJsonDeps(row.content);
    if (row.fileType === 'pom')     return [...new Set(parsePomDepBlocks(row.content).main)].join(', ');
    return '';
  }

  function extractDevDependencies(row) {
    if (row.fileType === 'package') return extractPackageJsonDevDeps(row.content);
    if (row.fileType === 'pom')     return [...new Set(parsePomDepBlocks(row.content).test)].join(', ');
    return '';
  }

  function collectBuildFileRows() {
    const rows = [];
    const groupOrder = ['shopping', 'others', 'byClaude'];

    function fromItems(items, groupName) {
      for (const item of items) {
        if (item.type === 'project') {
          const sep = item.path.includes('\\') ? '\\' : '/';
          const addRow = (filePath, bf) => rows.push({
            project: item,
            groupName,
            path: filePath,
            content: bf.content,
            fileType: bf.name.includes('pom') ? 'pom' : bf.name === 'pubspec.yaml' ? 'pubspec' : 'package',
          });
          for (const bf of (item.buildFiles || [])) {
            addRow(item.path + sep + bf.name, bf);
          }
          for (const sf of (item.subfolders || [])) {
            for (const bf of (sf.buildFiles || [])) {
              addRow(item.path + sep + sf.name + sep + bf.name, bf);
            }
          }
          for (const ex of (item.examples || [])) {
            for (const bf of (ex.buildFiles || [])) {
              addRow(item.path + sep + ex.name + sep + bf.name, bf);
            }
          }
        } else if (item.type === 'group') {
          fromItems(item.items, groupName);
        }
      }
    }

    for (const key of groupOrder) {
      const group = window.PROJECTS[key];
      if (!group) continue;
      fromItems(group.items, group.name);
    }
    return rows;
  }

  function renderPackagesTableBody(rows, matchLines) {
    const tbody = document.getElementById('pkg-tbody');
    if (!tbody) return;
    const showMatch = matchLines !== null;

    document.querySelectorAll('.packages-table .col-match').forEach(el => {
      el.style.display = showMatch ? '' : 'none';
    });
    document.querySelectorAll('.packages-table .col-deps').forEach(el => {
      el.style.display = showMatch ? 'none' : '';
    });
    // dev-deps: keep user's toggle state, but hide during search
    const devDepsBtn = document.getElementById('pkg-btn-devdeps');
    const devDepsOn = devDepsBtn && devDepsBtn.classList.contains('active');
    document.querySelectorAll('.packages-table .col-dev-deps').forEach(el => {
      el.style.display = (!showMatch && devDepsOn) ? '' : 'none';
    });

    // Group consecutive rows by project (preserve order)
    const groups = [];
    const seen = new Map();
    rows.forEach((row, i) => {
      const key = row.project.id;
      if (!seen.has(key)) {
        const g = { project: row.project, groupName: row.groupName, entries: [] };
        seen.set(key, g);
        groups.push(g);
      }
      seen.get(key).entries.push({ row, i });
    });

    let html = '';
    for (const { project, groupName, entries } of groups) {
      for (let j = 0; j < entries.length; j++) {
        const { row, i } = entries[j];
        const rid = 'pkgrow-' + i;
        const typeClass = 'pkg-row-' + row.fileType;
        const projCell = j === 0
          ? `<td class="pkg-project-cell" rowspan="${entries.length}"><div class="pkg-project-cell-inner"><span class="pkg-project-name">${esc(project.name)}</span><span class="pkg-group-badge">${esc(groupName)}</span></div></td>`
          : '';
        const depsCellHtml = showMatch
          ? '<td class="pkg-deps-cell col-deps" style="display:none"></td>'
          : `<td class="pkg-deps-cell col-deps">${esc(extractDependencies(row))}</td>`;
        const devDepsCellHtml = `<td class="pkg-deps-cell col-dev-deps" style="display:none">${esc(extractDevDependencies(row))}</td>`;
        const matchCellHtml = showMatch
          ? `<td class="pkg-match-cell col-match">${esc(matchLines[i] || '')}</td>`
          : '<td class="pkg-match-cell col-match" style="display:none"></td>';
        html += `<tr class="pkg-row ${typeClass}" data-row-id="${rid}">${projCell}<td class="pkg-file-cell"><span class="pkg-file-link" title="${esc(row.path)}">${esc(shortPath(row.path, row.groupName))}</span></td>${depsCellHtml}${devDepsCellHtml}${matchCellHtml}</tr>
<tr class="file-panel-row" id="panel-${rid}" style="display:none"><td colspan="5"><pre class="file-content">${esc(row.content)}</pre></td></tr>`;
      }
    }
    tbody.innerHTML = html;
  }

  function applyPackageFilters() {
    const q = (document.getElementById('pkg-search').value || '').trim().toLowerCase();
    const activeBtn = document.querySelector('.pkg-filter-btn.active');
    const groupFilter = activeBtn ? activeBtn.dataset.filter : 'all';

    const filteredRows = [];
    const matchLines = [];
    pkgAllRows.forEach(row => {
      if (groupFilter !== 'all' && row.groupName !== groupFilter) return;
      if (q && !row.content.toLowerCase().includes(q)) return;
      filteredRows.push(row);
      if (q) {
        const line = row.content.split('\n').find(l => l.toLowerCase().includes(q)) || '';
        matchLines.push(line.trim());
      }
    });

    renderPackagesTableBody(filteredRows, q ? matchLines : null);

    const countEl = document.getElementById('pkg-search-count');
    if (countEl) {
      const isFiltered = q || groupFilter !== 'all';
      countEl.textContent = isFiltered ? `${filteredRows.length} file${filteredRows.length !== 1 ? 's' : ''} found` : '';
    }
  }

  function clearPackageSearch() {
    const input = document.getElementById('pkg-search');
    if (input) input.value = '';
    document.querySelectorAll('.pkg-filter-btn').forEach(b => b.classList.remove('active'));
    const allBtn = document.querySelector('.pkg-filter-btn[data-filter="all"]');
    if (allBtn) allBtn.classList.add('active');
    applyPackageFilters();
  }

  function renderPackages() {
    pkgAllRows = collectBuildFileRows();
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const navPkg = document.getElementById('nav-packages');
    if (navPkg) navPkg.classList.add('active');
    history.replaceState(null, '', '#packages');

    document.getElementById('content').innerHTML = `
<div class="packages-page">
  <div class="packages-header">
    <h1>Packages &amp; POM</h1>
    <div class="pkg-search-bar">
      <div class="pkg-group-filter">
        <button class="pkg-filter-btn active" data-filter="all">All</button>
        <button class="pkg-filter-btn" data-filter="Shopping">Shopping</button>
        <button class="pkg-filter-btn" data-filter="Others">Others</button>
        <button class="pkg-filter-btn" data-filter="By Claude">By Claude</button>
      </div>
      <input type="text" id="pkg-search" placeholder="Search in file contents…" />
      <button id="pkg-btn-search">Search</button>
      <button id="pkg-btn-clear">Clear</button>
      <span id="pkg-search-count"></span>
      <button id="pkg-btn-devdeps" class="pkg-devdeps-toggle">Dev-Deps</button>
    </div>
  </div>
  <table class="packages-table">
    <thead>
      <tr>
        <th class="pkg-th-project">Project</th>
        <th>File</th>
        <th class="col-deps">Dependencies</th>
        <th class="col-dev-deps" style="display:none">Dev-Dependencies</th>
        <th class="col-match" style="display:none">Match</th>
      </tr>
    </thead>
    <tbody id="pkg-tbody"></tbody>
  </table>
</div>`;

    renderPackagesTableBody(pkgAllRows, null);

    document.getElementById('pkg-btn-search').addEventListener('click', applyPackageFilters);
    document.getElementById('pkg-search').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') applyPackageFilters();
    });
    document.getElementById('pkg-btn-clear').addEventListener('click', clearPackageSearch);

    document.getElementById('pkg-btn-devdeps').addEventListener('click', function () {
      this.classList.toggle('active');
      const on = this.classList.contains('active');
      const isSearchActive = document.querySelectorAll('.packages-table .col-match')[0]?.style.display !== 'none';
      document.querySelectorAll('.packages-table .col-dev-deps').forEach(el => {
        el.style.display = (on && !isSearchActive) ? '' : 'none';
      });
    });

    document.querySelector('.pkg-group-filter').addEventListener('click', function (e) {
      const btn = e.target.closest('.pkg-filter-btn');
      if (!btn) return;
      document.querySelectorAll('.pkg-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyPackageFilters();
    });

    document.getElementById('pkg-tbody').addEventListener('click', function (e) {
      if (e.target.closest('a.pkg-file-link')) return;
      const row = e.target.closest('tr.pkg-row');
      if (!row) return;
      const rid = row.dataset.rowId;
      const panel = document.getElementById('panel-' + rid);
      if (panel) panel.style.display = panel.style.display === 'none' ? '' : 'none';
    });
  }

  // ── Search ─────────────────────────────────────────────────────────────────

  function projectMatchesQuery(project, q) {
    if (!q) return true;
    const stack = project.stack || {};
    const haystack = [
      project.name,
      stack.frontend,
      ...(stack.language || []),
      ...(stack.backend  || []),
      ...(stack.database || []),
      ...(stack.ui       || []),
      ...(stack.tools    || []),
      project.github || '',
      project.readme   || '',
      project.aboutTxt || '',
    ].filter(Boolean).join(' ').toLowerCase();
    return haystack.includes(q);
  }

  function applySearch(query) {
    const q = query.trim().toLowerCase();
    let visible = 0;

    document.querySelectorAll('.nav-group').forEach(group => {
      let groupVisible = 0;
      group.querySelectorAll('.nav-item').forEach(item => {
        const project = registry[item.dataset.id];
        const match   = project && projectMatchesQuery(project, q);
        item.classList.toggle('hidden', !match);
        if (match) { groupVisible++; visible++; }
      });
      group.querySelectorAll('.nav-subgroup').forEach(sg => {
        const hasVisible = sg.querySelectorAll('.nav-item:not(.hidden)').length > 0;
        sg.classList.toggle('all-hidden', !hasVisible);
        if (q && hasVisible) sg.classList.remove('collapsed');
      });
      group.classList.toggle('all-hidden', groupVisible === 0);
      if (q && groupVisible > 0) group.classList.remove('collapsed');
    });

    const el = document.getElementById('search-count');
    if (el) {
      el.textContent = q ? `${visible} project${visible !== 1 ? 's' : ''} found` : '';
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    if (!window.PROJECTS) {
      document.getElementById('content').innerHTML = `
<div class="welcome">
  <h1>No data</h1>
  <p>Run <code>node generate-data.js</code> first.</p>
</div>`;
      return;
    }

    initRegistry();
    buildNav();
    document.querySelectorAll('.nav-group, .nav-subgroup').forEach(el => el.classList.add('collapsed'));

    document.getElementById('btn-collapse-all').addEventListener('click', function () {
      document.querySelectorAll('.nav-group, .nav-subgroup').forEach(el => el.classList.add('collapsed'));
    });

    const searchInput = document.getElementById('search');
    let timer;
    searchInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(() => applySearch(this.value), 180);
    });
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { this.value = ''; applySearch(''); }
    });

    const hash = decodeURIComponent(location.hash.slice(1));
    if (hash === 'packages') renderPackages();
    else if (hash && registry[hash]) selectProject(hash);
  });

})();
