# My Study Projects

A static web app for browsing and cataloging personal study projects across multiple technologies.

## GitHub :
- https://github.com/rpokluda72/my-self-study-projects.git
- https://rpokluda72.github.io/my-self-study-projects/index.html

## Features

- Hierarchical sidebar navigation (groups → subgroups → projects)
- Live search/filter by project name, tech stack, and readme content
- Tech stack display (frontend, backend, database, UI libraries, tools)
- Screenshot gallery with modal view
- README and build file (package.json, pom.xml, etc.) preview
- URL hash navigation (`#projectId`) for direct linking

## Usage

Open `index.html` in a browser — no server or build step required.

## Regenerating Project Data

The catalog is stored in `projects-data.js` (auto-generated). To rebuild it from your local projects:

```bash
node generate-data.js
```

This scans the source directories configured in `GROUPS_CONFIG` inside `generate-data.js`, detects tech stacks, copies screenshots, and rewrites `projects-data.js`.

## Tech Stack

Vanilla HTML/CSS/JS — no framework, no bundler. [Marked.js](https://marked.js.org/) loaded from CDN for markdown rendering.
