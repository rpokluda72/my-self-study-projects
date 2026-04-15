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

    nav.innerHTML = html;
    const stats = document.getElementById('welcome-stats');
    if (stats) stats.textContent = `${totalProjects} projects in 3 groups`;
  }

  // ── Collapse toggling (event delegation) ───────────────────────────────────

  document.addEventListener('click', function (e) {
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
</div>`;
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
    if (hash && registry[hash]) selectProject(hash);
  });

})();
