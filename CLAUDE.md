# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A static web application that catalogs and displays study projects. It has no build step — deploy the folder as-is to any static host.

## Data Generation

The only "build" step is regenerating the project catalog:

```bash
node generate-data.js
```

This scans local project directories (hardcoded paths in `GROUPS_CONFIG`), extracts tech stack info, copies screenshots, and writes `projects-data.js` (auto-generated, ~1.3MB). **Do not manually edit `projects-data.js`.**

The hardcoded source paths in `generate-data.js`:
- `C:/Users/roman/Work/pohovor/projects/shopping` → `shopping` group
- `C:/Users/roman/Work/pohovor/projects` → `others` group
- `C:/Users/roman/Work/claude/projects` → `byClaude` group

## Architecture

**Three files form the app core:**

- `index.html` — entry point, loads Marked.js from CDN for markdown rendering
- `app.js` — all application logic: navigation rendering, search/filter, URL hash routing (`#projectId`), screenshot gallery, markdown/build file display
- `style.css` — CSS variables for theming, flexbox two-panel layout

**Data flow:**
```
Local filesystem → generate-data.js → projects-data.js (window.PROJECTS) → app.js → UI
```

**Navigation hierarchy** (up to 3 levels): group → subgroup → project. `app.js` builds an in-memory project registry from the hierarchical `window.PROJECTS` structure and uses event delegation on the sidebar for click handling.

**Project data schema** (defined in `generate-data.js`, consumed by `app.js`):
```javascript
{
  type: "project",
  id, name, path, stack, readme, aboutTxt,
  buildFiles, subfolders, screenshots, github
}
```

**Tech stack detection** lives entirely in `generate-data.js` — it reads `package.json`, `pom.xml`, `pubspec.yaml`, etc. from project directories to infer frontend/backend/database/UI/tool tags.

## No Dependencies to Install

Vanilla JS only. No `npm install`, no bundler, no transpilation. The only external dependency is Marked.js loaded via CDN at runtime.
