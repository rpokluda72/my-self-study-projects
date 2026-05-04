# Java Versions Features — HTML Preview

Static HTML preview of all Java study classes, from Java 8 to Java 24.

## How to open

Open `index.html` in any modern web browser (Chrome, Firefox, Edge).

> **Note:** An internet connection is required for the first load — the page fetches
> [Highlight.js](https://highlightjs.org/) from a CDN for syntax highlighting.
> After the first load the browser will cache the CDN assets.

## Features

| Feature | Description |
|---------|-------------|
| Two-level menu | Left sidebar groups classes by Java version; click a version header to expand/collapse |
| Collapse All | Button at the top of the sidebar collapses all version groups at once |
| Direct navigation | Click a class name to load its page and auto-scroll to that class card |
| Sidebar search | Filters the menu to show only versions/classes whose source contains the search term |
| In-page search | Search bar inside each page highlights all matches; **Prev / Next** navigate between them |
| Cross-frame search | Typing in the sidebar search simultaneously searches the currently open page |
| Card collapse | Each class card can be individually expanded or collapsed via its header |
| Show all / Collapse all | Toolbar buttons on each page expand or collapse all cards at once |
| Dark theme | IntelliJ-style syntax highlighting via Highlight.js `atom-one-dark` theme |

## Keyboard shortcuts (in-page search bar)

| Key | Action |
|-----|--------|
| `Enter` | Next match |
| `Shift+Enter` | Previous match |
| `Escape` | Clear search |

## Regenerating after source changes

When `.java` files are modified, regenerate the HTML by running:

```bash
cd html_preview
python generate.py
```

Requires Python 3.6+. No external Python packages needed.

## File structure

```
html_preview/
  index.html        Main page (sidebar + iframe layout)
  java8.html        Java 8 features (Lambda, Stream, Optional, ...)
  java9.html        Java 9 features (Collection factories, try-with-resources)
  java10.html       Java 10 features (var)
  java11.html       Java 11 features (String methods, HttpClient, Files)
  java14.html       Java 14 features (Switch expressions)
  java15.html       Java 15 features (Text blocks)
  java16.html       Java 16 features (Records, Pattern instanceof, Stream.toList)
  java17.html       Java 17 features (Sealed classes)
  java21.html       Java 21 features (Virtual threads, Record patterns, Pattern switch, Sequenced collections)
  java23.html       Java 23 features (Unnamed variables)
  java24.html       Java 24 features (Stream Gatherers)
  generate.py       Generator script
  README.md         This file
```
