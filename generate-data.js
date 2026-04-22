'use strict';
/**
 * Scans local project directories, copies screenshots into screens/,
 * and generates projects-data.js with relative paths (static-hosting ready).
 * Run: node generate-data.js
 */
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = __dirname;

const GROUPS_CONFIG = [
  {
    id: 'shopping',
    name: 'Shopping',
    root: 'C:/Users/roman/Work/pohovor/projects/shopping',
    skip: [],
  },
  {
    id: 'others',
    name: 'Others',
    root: 'C:/Users/roman/Work/pohovor/projects',
    skip: ['shopping', 'screens', 'sql'],
  },
  {
    id: 'byClaude',
    name: 'By Claude',
    root: 'C:/Users/roman/Work/claude/projects',
    skip: ['MyStudyPages', 'MyStudyProjects', 'MyStudyProjectsWeb'],
  },
];

// Fixed sub-directory names to scan for tech stack detection
const STACK_SCAN_DIRS = ['client', 'server', 'frontend', 'backend', 'app', 'mobile'];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function norm(p) { return p.replace(/\\/g, '/'); }

function safeStat(p) {
  try { return fs.statSync(p); } catch { return null; }
}

function safeRead(p) {
  try {
    const buf = fs.readFileSync(p);
    if (buf[0] === 0xFF && buf[1] === 0xFE) return buf.toString('utf16le').replace(/^\uFEFF/, '');
    if (buf[0] === 0xFE && buf[1] === 0xFF) {
      const swapped = Buffer.alloc(buf.length);
      for (let i = 0; i + 1 < buf.length; i += 2) { swapped[i] = buf[i+1]; swapped[i+1] = buf[i]; }
      return swapped.toString('utf16le').replace(/^\uFEFF/, '');
    }
    return buf.toString('utf8');
  } catch { return null; }
}

function safeDir(p) {
  try { return fs.readdirSync(p); } catch { return []; }
}

function getMajor(ver) {
  if (!ver) return '';
  const m = ver.replace(/[\^~>=< ]/g, '').match(/^(\d+)/);
  return m ? m[1] : '';
}

function isSubfolderName(name) {
  const lower = name.toLowerCase();
  const fixed = ['frontend', 'backend', 'client', 'server', 'app', 'mobile'];
  return fixed.includes(lower)
    || lower.endsWith('-frontend')
    || lower.endsWith('-backend')
    || lower.endsWith('-client')
    || lower.endsWith('-server')
    || lower.endsWith('-mobile')
    || lower.startsWith('frontend-')
    || lower.startsWith('backend-')
    || lower.startsWith('client-')
    || lower.startsWith('server-');
}

// ─── Tech stack detection ─────────────────────────────────────────────────────

function collectDeps(projectDir) {
  const deps = {};
  function addPkg(pkgPath) {
    const txt = safeRead(pkgPath);
    if (!txt) return;
    try {
      const pkg = JSON.parse(txt);
      Object.assign(deps, pkg.dependencies || {});
      Object.assign(deps, pkg.devDependencies || {});
    } catch {}
  }
  addPkg(path.join(projectDir, 'package.json'));
  for (const entry of safeDir(projectDir)) {
    if (!isSubfolderName(entry)) continue;
    const sub = path.join(projectDir, entry);
    if (safeStat(sub)?.isDirectory()) addPkg(path.join(sub, 'package.json'));
  }
  return deps;
}

function parsePubspecDeps(content) {
  const deps = new Set();
  for (const m of content.matchAll(/^  ([\w][\w_-]*):/gm)) {
    if (m[1] !== 'sdk' && m[1] !== 'flutter') deps.add(m[1]);
  }
  return deps;
}

function collectFlutterDeps(projectDir) {
  for (const sub of ['.', 'app']) {
    const txt = safeRead(path.join(projectDir, sub, 'pubspec.yaml'));
    if (txt && txt.includes('flutter:')) return { pubspec: txt, flutterDeps: parsePubspecDeps(txt) };
  }
  return null;
}

function detectStack(projectDir) {
  const deps = collectDeps(projectDir);
  const pom = safeRead(path.join(projectDir, 'pom.xml'));
  const flutter = collectFlutterDeps(projectDir);
  const hasDeps = Object.keys(deps).length > 0;

  const language = new Set();
  const backend  = new Set();
  const database = new Set();
  const ui       = new Set();
  const tools    = new Set();
  let   frontend = null;

  // ── Flutter ──
  if (flutter) {
    const fd = flutter.flutterDeps;
    frontend = 'Flutter';
    language.add('Dart');
    if (fd.has('flutter_riverpod') || fd.has('hooks_riverpod')) tools.add('Riverpod');
    if (fd.has('provider'))       tools.add('Provider');
    if (fd.has('bloc') || fd.has('flutter_bloc')) tools.add('BLoC');
    if (fd.has('go_router'))      tools.add('go_router');
    if (fd.has('dio'))            tools.add('Dio');
    if (fd.has('http'))           tools.add('http');
    if (fd.has('freezed') || fd.has('freezed_annotation')) tools.add('Freezed');
    if (fd.has('hive') || fd.has('hive_flutter')) database.add('Hive');
    if (fd.has('sqflite'))        database.add('SQLite');
    if (fd.has('isar'))           database.add('Isar');
  }

  // ── Frontend (JS/TS) ──
  if (!frontend && deps['@ionic/angular']) {
    const v = getMajor(deps['@angular/core'] || deps['@ionic/angular']);
    frontend = `Ionic + Angular${v ? ' ' + v : ''}`;
    language.add('TypeScript');
  } else if (deps['@ionic/react']) {
    const v = getMajor(deps['react'] || deps['react-dom'] || deps['@ionic/react']);
    frontend = `Ionic + React${v ? ' ' + v : ''}`;
    language.add('TypeScript');
  } else if (deps['@angular/core']) {
    const v = getMajor(deps['@angular/core']);
    frontend = `Angular${v ? ' ' + v : ''}`;
    language.add('TypeScript');
  } else if (deps['next']) {
    const v = getMajor(deps['next']);
    frontend = `Next.js${v ? ' ' + v : ''}`;
    language.add('TypeScript');
  } else if (deps['react'] || deps['react-dom']) {
    const v = getMajor(deps['react'] || deps['react-dom']);
    frontend = `React${v ? ' ' + v : ''}`;
    language.add(deps['typescript'] || deps['@types/react'] ? 'TypeScript' : 'JavaScript');
  } else if (deps['@sveltejs/kit']) {
    const v = getMajor(deps['@sveltejs/kit'] || deps['svelte']);
    frontend = `SvelteKit${v ? ' ' + v : ''}`;
    language.add(deps['typescript'] ? 'TypeScript' : 'JavaScript');
  } else if (deps['svelte']) {
    const v = getMajor(deps['svelte']);
    frontend = `Svelte${v ? ' ' + v : ''}`;
    language.add(deps['typescript'] ? 'TypeScript' : 'JavaScript');
  } else if (deps['vue']) {
    const v = getMajor(deps['vue']);
    frontend = `Vue.js${v ? ' ' + v : ''}`;
    language.add('JavaScript');
  } else if (deps['electron']) {
    frontend = 'Electron';
    language.add('JavaScript');
  } else if (hasDeps) {
    language.add(deps['typescript'] ? 'TypeScript' : 'JavaScript');
  }

  // ── Backend (JS) ──
  if (deps['express'])         backend.add('Express.js');
  if (deps['@nestjs/core'])    backend.add('Nest.js');
  if (deps['fastify'])         backend.add('Fastify');
  if (deps['json-server'])     backend.add('JSON Server');
  if (deps['@angular/ssr'] || deps['@angular/platform-server']) backend.add('Angular SSR');

  // ── Database (JS) ──
  if (deps['mongoose'] || deps['mongodb']) database.add('MongoDB');
  if (deps['mysql'] || deps['mysql2'])     database.add('MySQL');
  if (deps['pg'])                          database.add('PostgreSQL');
  if (deps['sqlite3'] || deps['better-sqlite3']) database.add('SQLite');

  // ── UI Frameworks ──
  if (deps['bootstrap'] || deps['@ng-bootstrap/ng-bootstrap'] || deps['ngx-bootstrap']) ui.add('Bootstrap');
  if (deps['primeng'])            ui.add('PrimeNG');
  if (deps['tailwindcss'])        ui.add('Tailwind CSS');
  if (deps['@angular/material'])  ui.add('Angular Material');
  if (deps['@mui/material'] || deps['@mui/core']) ui.add('Material UI');
  if (deps['styled-components'])  ui.add('styled-components');

  // ── Tools / API ──
  if (deps['axios'])              tools.add('Axios');
  if (deps['rxjs'])               tools.add('RxJS');
  if (deps['@ngrx/store'])        tools.add('NgRx');
  if (deps['recoil'])             tools.add('Recoil');
  if (deps['@reduxjs/toolkit'] || deps['redux']) tools.add('Redux');
  if (deps['sequelize'])          tools.add('Sequelize');
  if (deps['typeorm'])            tools.add('TypeORM');
  if (deps['@prisma/client'] || deps['prisma']) tools.add('Prisma');
  if (deps['lodash'])             tools.add('Lodash');
  if (deps['@capacitor/core'])    tools.add('Capacitor');
  if (deps['electron-store'])     tools.add('electron-store');
  if (deps['@dnd-kit/core'])      tools.add('dnd-kit');

  // ── Java / Maven ──
  if (pom) {
    language.add('Java');
    if (pom.includes('spring-boot-starter'))               backend.add('Spring Boot');
    else if (pom.includes('spring-webmvc') || pom.includes('spring-web')) backend.add('Spring MVC');
    if (pom.includes('spring-data-jpa') || pom.includes('jakarta.persistence')) tools.add('Spring Data JPA');
    if (pom.includes('kafka'))                             tools.add('Apache Kafka');
    if (pom.includes('lombok'))                            tools.add('Lombok');
    if (pom.includes('spring-security') || pom.includes('spring-boot-starter-security')) tools.add('Spring Security');
    if (pom.includes('oauth2-client'))                     tools.add('OAuth2');
    if (pom.includes('mapstruct'))                         tools.add('MapStruct');
    if (pom.includes('thymeleaf'))                         ui.add('Thymeleaf');
    if (pom.includes('vaadin'))   { frontend = 'Vaadin';  ui.add('Vaadin'); }
    if (pom.includes('mysql-connector') || pom.includes('mysql-connector-j')) database.add('MySQL');
    if (pom.includes('mariadb'))                           database.add('MariaDB');
    if (pom.includes('com.h2database') || pom.includes('<artifactId>h2</artifactId>')) database.add('H2');
    if (pom.includes('spring-data-mongodb') || pom.includes('mongodb')) database.add('MongoDB');
    if (pom.includes('postgresql'))                        database.add('PostgreSQL');
    if (pom.includes('swing') || pom.includes('javax.swing')) frontend = 'Swing';
  }

  return {
    language: [...language],
    frontend,
    backend:  [...backend],
    database: [...database],
    ui:       [...ui],
    tools:    [...tools],
  };
}

// ─── File collection ──────────────────────────────────────────────────────────

function getReadme(dir) {
  return safeRead(path.join(dir, 'README.md'))
      || safeRead(path.join(dir, 'README.txt'));
}

function getAboutTxt(projectDir) {
  return safeRead(path.join(projectDir, 'about.txt'));
}

function getBuildFiles(projectDir) {
  const results = [];
  function tryAdd(filePath, displayName) {
    const content = safeRead(filePath);
    if (content) results.push({ name: displayName || path.basename(filePath), content });
  }
  tryAdd(path.join(projectDir, 'package.json'));
  tryAdd(path.join(projectDir, 'pom.xml'));
  tryAdd(path.join(projectDir, 'pubspec.yaml'));
  return results;
}

function getSubfolders(projectDir) {
  const result = [];

  function scanSubfolder(subPath, displayName) {
    const readme     = getReadme(subPath);
    const buildFiles = [];
    function tryBuild(p) {
      const c = safeRead(p);
      if (c) buildFiles.push({ name: path.basename(p), content: c });
    }
    tryBuild(path.join(subPath, 'package.json'));
    tryBuild(path.join(subPath, 'pom.xml'));
    tryBuild(path.join(subPath, 'pubspec.yaml'));

    if (readme || buildFiles.length) {
      result.push({ name: displayName, readme, buildFiles, stack: detectStack(subPath) });
    }

    // Recurse into children that look like project sub-dirs (not standard named subfolders themselves)
    for (const child of safeDir(subPath)) {
      const childPath = path.join(subPath, child);
      if (!safeStat(childPath)?.isDirectory()) continue;
      if (child.startsWith('.') || child === 'node_modules' || child === 'target') continue;
      const childBuildFiles = [
        path.join(childPath, 'package.json'),
        path.join(childPath, 'pom.xml'),
        path.join(childPath, 'pubspec.yaml'),
      ].filter(p => safeRead(p));
      const childReadme = getReadme(childPath);
      if (childBuildFiles.length || childReadme) {
        const bfs = childBuildFiles.map(p => ({ name: path.basename(p), content: safeRead(p) }));
        result.push({
          name: displayName + '/' + child,
          readme: childReadme,
          buildFiles: bfs,
          stack: detectStack(childPath),
        });
      }
    }
  }

  for (const entry of safeDir(projectDir)) {
    if (!isSubfolderName(entry)) continue;
    const subPath = path.join(projectDir, entry);
    if (!safeStat(subPath)?.isDirectory()) continue;
    scanSubfolder(subPath, entry);
  }
  return result;
}

function getCommentsTxt(projectDir) {
  return safeRead(path.join(projectDir, 'comments.txt'));
}

// Copy screenshots into screens/<uid>/ and return relative paths
function getScreenshots(projectDir, uid) {
  const files = safeDir(projectDir)
    .filter(f => /\.(png|jpg|jpeg)$/i.test(f) && !safeStat(path.join(projectDir, f))?.isDirectory());
  // Also collect from standard-named subfolders (frontend-*, backend-*, client, server, etc.)
  const subFiles = [];
  for (const entry of safeDir(projectDir)) {
    if (!isSubfolderName(entry)) continue;
    const subPath = path.join(projectDir, entry);
    if (!safeStat(subPath)?.isDirectory()) continue;
    for (const f of safeDir(subPath)) {
      if (/\.(png|jpg|jpeg)$/i.test(f) && !safeStat(path.join(subPath, f))?.isDirectory()) {
        subFiles.push({ f, srcDir: subPath });
      }
    }
  }

  if (!files.length && !subFiles.length) return [];

  const targetDir = path.join(OUTPUT_DIR, 'screens', uid);
  fs.mkdirSync(targetDir, { recursive: true });

  const result = [];
  for (const f of files) {
    const src = path.join(projectDir, f);
    const dst = path.join(targetDir, f);
    try { fs.copyFileSync(src, dst); } catch {}
    result.push(norm(path.join('screens', uid, f)));
  }
  for (const { f, srcDir } of subFiles) {
    const src = path.join(srcDir, f);
    const dst = path.join(targetDir, f);
    try { fs.copyFileSync(src, dst); } catch {}
    result.push(norm(path.join('screens', uid, f)));
  }
  return result;
}

const EXAMPLE_SKIP = new Set([
  'node_modules', 'target', 'dist', 'build', '.git', '.idea', '.vscode', '.mvn', 'out',
]);

function getExamples(projectDir, projectUid) {
  const result = [];
  for (const entry of safeDir(projectDir)) {
    if (EXAMPLE_SKIP.has(entry) || entry.startsWith('.')) continue;
    if (isSubfolderName(entry)) continue;
    const subPath = path.join(projectDir, entry);
    if (!safeStat(subPath)?.isDirectory()) continue;

    const readme = getReadme(subPath);
    const buildFiles = [];
    const pom = safeRead(path.join(subPath, 'pom.xml'));
    if (pom) buildFiles.push({ name: 'pom.xml', content: pom });
    const pkg = safeRead(path.join(subPath, 'package.json'));
    if (pkg) buildFiles.push({ name: 'package.json', content: pkg });

    const screenFiles = safeDir(subPath).filter(f => /^screen.*\.(png|jpg|jpeg)$/i.test(f));
    let screenshots = [];
    if (screenFiles.length) {
      const uid = `${projectUid}--${entry}`;
      const targetDir = path.join(OUTPUT_DIR, 'screens', uid);
      fs.mkdirSync(targetDir, { recursive: true });
      screenshots = screenFiles.map(f => {
        try { fs.copyFileSync(path.join(subPath, f), path.join(targetDir, f)); } catch {}
        return norm(path.join('screens', uid, f));
      });
    }

    if (!readme && !buildFiles.length && !screenshots.length) continue;
    result.push({ name: entry, readme, buildFiles, screenshots });
  }
  return result;
}

function getGitOrigin(projectDir) {
  const cfg = safeRead(path.join(projectDir, '.git', 'config'));
  if (!cfg) return null;
  const m = cfg.match(/\[remote "origin"\][\s\S]*?url\s*=\s*(.+)/);
  if (!m) return null;
  return m[1].trim()
    .replace(/^git@github\.com:/, 'https://github.com/')
    .replace(/\.git$/, '');
}

// ─── Project builder ──────────────────────────────────────────────────────────

function isProject(dir) {
  return fs.existsSync(path.join(dir, '.idea'));
}

function buildProject(dir, name, uid) {
  return {
    type:       'project',
    id:         uid,
    name,
    path:       norm(dir),
    stack:       detectStack(dir),
    readme:      getReadme(dir),
    aboutTxt:    getAboutTxt(dir),
    commentsTxt: getCommentsTxt(dir),
    buildFiles:  getBuildFiles(dir),
    subfolders:  getSubfolders(dir),
    examples:    getExamples(dir, uid),
    screenshots: getScreenshots(dir, uid),
    github:      getGitOrigin(dir),
  };
}

// ─── Group scanner ────────────────────────────────────────────────────────────

function scanGroup(config) {
  const { id, root, skip } = config;
  const items = [];
  for (const entry of safeDir(root)) {
    if (skip.includes(entry)) continue;
    const fullPath = path.join(root, entry);
    if (!safeStat(fullPath)?.isDirectory()) continue;

    if (isProject(fullPath)) {
      items.push(buildProject(fullPath, entry, `${id}-${entry}`));
    } else {
      const groupItems = [];
      for (const sub of safeDir(fullPath)) {
        const subPath = path.join(fullPath, sub);
        if (!safeStat(subPath)?.isDirectory()) continue;

        if (isProject(subPath)) {
          groupItems.push(buildProject(subPath, sub, `${id}-${entry}-${sub}`));
        } else {
          const subSubProjects = [];
          for (const subsub of safeDir(subPath)) {
            const subSubPath = path.join(subPath, subsub);
            if (safeStat(subSubPath)?.isDirectory() && isProject(subSubPath)) {
              subSubProjects.push(buildProject(subSubPath, subsub, `${id}-${entry}-${sub}-${subsub}`));
            }
          }
          if (subSubProjects.length > 0) {
            groupItems.push({ type: 'group', id: `${id}-${entry}-${sub}`, name: sub, items: subSubProjects });
          }
        }
      }
      if (groupItems.length > 0) {
        items.push({ type: 'group', id: `${id}-${entry}`, name: entry, items: groupItems });
      }
    }
  }
  return items;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

console.log('Generating projects-data.js...\n');
const data = {};
let total = 0;
for (const config of GROUPS_CONFIG) {
  process.stdout.write(`  Scanning ${config.name}...`);
  const items = scanGroup(config);
  const count = items.reduce((n, item) =>
    n + (item.type === 'group' ? item.items.length : 1), 0);
  total += count;
  data[config.id] = { id: config.id, name: config.name, items };
  console.log(` ${count} projects`);
}

const output = [
  `// Auto-generated by generate-data.js`,
  `// Last updated: ${new Date().toLocaleString()}`,
  `// Run: node generate-data.js  to regenerate`,
  `window.PROJECTS = ${JSON.stringify(data, null, 2)};`,
].join('\n') + '\n';

fs.writeFileSync(path.join(OUTPUT_DIR, 'projects-data.js'), output, 'utf8');
console.log(`\nDone — ${total} projects written to projects-data.js`);
console.log('Screenshots copied to screens/');
console.log('Deploy the whole folder to GitHub Pages or any static host.\n');
