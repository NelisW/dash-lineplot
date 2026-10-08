---
title: "dash-lineplot Hardcopy Output Design"
date: "2026-10-08"
pdf-engine: lualatex
style: |
  .markdown-preview.markdown-preview {
    font-size: 11pt;
    line-height: 1.5;
  }
puppeteer:
  displayHeaderFooter: true
  format: "A4"
  margin:
    top: "1.5cm"
    bottom: "1.5cm"
    left: "1cm"
    right: "1cm"
  headerTemplate: |
    <div style="font-family: Arial, sans-serif; font-size: 9pt; width: 100%; padding: 0 1cm; display: flex; justify-content: space-between; color: #000;">
      <span class="title"></span>
      <span class="date"></span>
    </div>
  footerTemplate: |
    <div style="font-family: Arial, sans-serif; font-size: 9pt; width: 100%; text-align: center; color: #000;">
      <span class="pageNumber"></span>/<span class="totalPages"></span>
    </div>
---

# dash-lineplot Hardcopy Output Design

Markdown flavour: LaTeX-conversion-safe (ASCII only, LF line endings),
with Pandoc/Puppeteer PDF front matter.

## Orientation

This document specifies a hardcopy facility for `dash-lineplot`: a
keystroke that writes the graphs of the tab currently on screen to one or
more A4 pages, each a 300 dpi PNG file. It also specifies a related layout
change, that graphs configured with a small `Height` are drawn without the
range-entry and readout column beside them, and a demonstration
configuration that exercises both.

Line references to `dash-lineplot.py` are to the file as it stands at
commit `ef0bdf0`.

## Requirements

| Id | Requirement |
|---|---|
| R1 | A graph whose block `Height` is 200 or less is drawn without the column of text-entry and readout boxes beside it; the graph takes the full row width, except on a `commonX` tab that also has boxed graphs, where an empty column keeps its x axis aligned with theirs (amended 2026-10-08 after review). |
| R2 | A keystroke starts hardcopy generation for the tab currently on screen, and only that tab. |
| R3 | The user names the output file. By default the pages are saved into the directory the server was started in, with no dialog; a native folder dialog remains available to save elsewhere (amended 2026-10-08: the dialog cannot be opened at a given path, see "Saving into the working directory"). |
| R4 | The hardcopy shows graphs only: no tab strip, no page or graph markdown, no readouts, no logo. |
| R5 | Output is PNG, 300 dpi, A4 portrait. |
| R6 | A tab with more graphs than fit on one page produces several pages. |
| R7 | A tab may set, in its configuration, how many graphs go on one hardcopy page. |
| R8 | A new demonstration configuration with dummy data exercises R1 to R7. |

## Feasibility and choice of approach

Two approaches were considered.

**Browser-side (chosen).** Plotly in the browser already provides
`Plotly.toImage`, which renders a graph to a PNG at a requested size and
scale. A plain JavaScript file in `assets/`, served by Dash with no
callback and no package, can render each graph of the visible tab, compose
the pages on a canvas, and write the files through the File System Access
API. This adds no Python or conda dependency, prints exactly what is on
screen (including the current zoom), and keeps the browser as the only
user interface, as it is today.

**Server-side (rejected).** Plotly's static export needs `kaleido`, which
in current releases needs a local Chrome, and page composition would need
`pillow`; none of these are in `environment.yml` today. A native file
dialog opened from the Flask server thread (tkinter) is fragile, tends to
open behind the browser window, and cannot work at all when the browser
and the server are on different machines.

**Constraint accepted with the chosen approach.** The File System Access
API (`showDirectoryPicker`) exists in Chromium browsers (Chrome, Edge)
only, and only in a secure context, which `http://localhost` and
`http://127.0.0.1` are. Chrome and Edge are the supported browsers for
hardcopy. Elsewhere the keystroke reports that hardcopy is unavailable in
this browser and does nothing else.

**Why a folder dialog, not a Save-As dialog.** `showSaveFilePicker`
grants write access to the one file named in the dialog and to nothing
beside it, so it cannot write the second and later pages of a multi-page
tab. `showDirectoryPicker` grants access to a folder, into which every page
can be written after a single dialog. The file name is therefore typed in
a small in-page box, and the folder is chosen in the native dialog.

## Design

### Small graphs without the readout column (R1)

- The rule is evaluated per graph, from the `height` of the block the
  graph belongs to (`resolveSetContexts`, `dash-lineplot.py:275-337`). A
  graph has boxes when `height > 200`. A sheet with no `Height` row takes
  the default of 300 (`dash-lineplot.py:299`) and so keeps its boxes; the
  threshold is a module constant, `BOXES_MIN_HEIGHT = 200`.
- In `makeGraphSet` (`dash-lineplot.py:1259-1274`), a graph without boxes
  is placed in a `twelve columns` div and no `three columns` div is
  emitted; on a `commonX` tab where any block has boxes it keeps the
  `nine columns` div and gets an empty `three columns` spacer instead, so
  its plot area matches the boxed graphs' and the shared x axis lines up.
  A graph with boxes is unchanged.
- `makeGraphSet` records which graphs have boxes in a new instance set,
  `self.boxedGraphs`.
- `setupCallbacks` (`dash-lineplot.py:1689-1966`) changes as follows:
    - The x/y range-apply callback (`apply_ranges`) takes its `Input` and
      `State` lists from the boxed members of the graph's `commonX` group
      only. It is registered for a graph only if that list is not empty.
      A graph without boxes on a `commonX` tab therefore still follows an
      x range typed into a sibling's boxes; a graph without boxes on any
      other tab gets no range callback.
    - `show_ranges`, the click readout callbacks and the selection readout
      callbacks are registered for boxed graphs only, since their outputs
      live in the boxes. Their `Input` lists keep listening to every graph
      of the `commonX` group, boxed or not, because graphs themselves are
      always on the page.
- Mouse zoom, pan and autoscale, page-wide hover and `commonX` x linking
  in `assets/graphsync.js` are unaffected: they operate on the Plotly
  graphs, not on the boxes.

### Tab container and per-tab settings (R2, R7)

- `makeGraphSet` wraps everything it builds for a tab in one
  `html.Div(className='graph-tab')` carrying two data attributes:
    - `data-tab-name`: the tab name (the text after `graph-` in the sheet
      name), used as the default file name.
    - `data-hardcopy-per-page`: the value of the tab's
      `HardcopyGraphsPerPage` row, or an empty string when the row is
      missing or its value is not a positive integer.
- `makeGraphSet` returns a one-element list holding that wrapper, so
  `render_content` and `makePage` (`dash-lineplot.py:1379-1395`,
  `dash-lineplot.py:1710-1712`) need no change.
- The graph rows stay siblings inside the wrapper, so `xGroupOf` in
  `graphsync.js`, which collects `.graph-row.common-x` rows from one
  parent, is unaffected.

### Configuration (R7)

One new graph-sheet row:

| Variable | Value | Meaning |
|---|---|---|
| `HardcopyGraphsPerPage` | positive integer | Number of equal-height graph slots on each hardcopy page of this tab. |

No change is needed in `readConfigTables` or in
`tools/xlsx_config_to_json.py`: both carry any `Variable`/`Value` row
through unchanged (`tools/xlsx_config_to_json.py:59-70`).

### Hardcopy script (R2 to R6)

A new file, `assets/hardcopy.js`, in the same style as `graphsync.js`: one
immediately invoked function, no globals, no dependencies beyond
`window.Plotly`.

**Trigger.** A `keydown` listener on `document` reacts to Ctrl+Alt+H
(`event.ctrlKey && event.altKey && event.code === 'KeyH'`), wherever the
focus is, and calls `preventDefault`. Ctrl+P is left to the browser.

**Sequence.**

1. Find the visible `.graph-tab` (the one whose `offsetParent` is not
   `null`), which covers both the callback-rendered layout and the layout
   with every tab built in advance. If there is none, or it holds no
   Plotly graph, show a short message and stop.
1. If `window.showDirectoryPicker` is missing, show "Hardcopy needs Chrome
   or Edge, opened at a localhost address" and stop.
1. Open an in-page modal: one text field, pre-filled with `data-tab-name`,
   plus Save and Cancel buttons. Enter is Save, Escape is Cancel. The name
   is trimmed, a trailing `.png` is removed, and a name that is empty or
   contains any of `<>:"/\|?*` is refused in the modal itself.
1. On Save, call
   `showDirectoryPicker({mode: 'readwrite', id: 'dash-lineplot-hardcopy'})`
   directly in the Save handler, which keeps the user activation the API
   requires. The `id` makes the browser reopen the folder used last time.
   A cancelled dialog ends the operation silently.
1. Lay out the pages (below) to learn the page count, and so the file
   names: `<name>.png` for a single page, otherwise `<name>-p1.png`,
   `<name>-p2.png`, and so on.
1. If any of those files already exists in the folder, ask once, through
   the browser's `confirm`, before overwriting.
1. Render each page and write it. While this runs, the modal shows
   "Page k of n"; when it finishes, it reports the folder-relative file
   names written and closes on the next key press or click.
1. Any failure (permission refused, write error, render error) is shown in
   the modal with the error message; nothing is retried.

**Page geometry.** All sizes are worked in CSS pixels at 96 per inch and
multiplied by `scale = 300 / 96` only at the final rendering step, so that
text and line widths come out at the same physical size they have on
screen.

| Quantity | Value |
|---|---|
| Page | A4 portrait, 210 mm x 297 mm, 2480 px x 3508 px at 300 dpi |
| Margin | 10 mm on every side |
| Printable area | 190 mm x 277 mm, about 718 x 1047 CSS px |
| Graph width | the full printable width |
| Gap between graphs | none, matching the compact screen layout |

**Layout when `HardcopyGraphsPerPage` = N.** Each page has N equal slots
of height `1047 / N` CSS px. Graphs fill the slots in page order. The last
page keeps the same slot height and leaves its unused slots white.

**Layout when the row is absent.** Each graph keeps its on-screen height in
CSS px, which is its configured `Height`, so the relative heights of the
graphs are preserved and a graph prints at the physical height it occupies
on a 96 dpi screen. Graphs are placed top-down; a graph that does not fit
in what is left of the page starts the next page. A single graph taller
than the printable height is scaled down to exactly the printable height.

**Rendering.** For each graph, call
`Plotly.toImage(gd, {format: 'png', width: w, height: h, scale: 300 / 96})`
with `w` and `h` its printed size in CSS px. This renders the graph's
current figure, so the current axis ranges are what print. Each result is
drawn onto a 2480 x 3508 canvas filled white, at its slot's top-left
corner in 300 dpi pixels.

**300 dpi marking.** `canvas.toBlob` does not record a resolution, and
without one most programs assume 96 dpi and show the image at about three
times its intended size. After encoding, the script inserts a `pHYs` chunk
immediately after `IHDR`: 11811 pixels per metre on both axes, unit byte
1 (metre), with its CRC-32 computed over the chunk type and data. An
existing `pHYs` chunk, if the encoder ever writes one, is replaced.

**Writing.** Each page is written with
`dir.getFileHandle(name, {create: true})`, then `createWritable`, `write`
and `close`. Existence is tested beforehand with
`getFileHandle(name, {create: false})`, which raises `NotFoundError` for
a missing file.

### Saving into the working directory (R3, amended)

`showDirectoryPicker`'s `startIn` option accepts only a file-system
handle or one of the well-known folders `desktop`, `documents`,
`downloads`, `music`, `pictures` and `videos`; a page cannot open the
dialog at an arbitrary path such as the server's working directory. The
default destination is therefore reached through the server:

- `DashLinePlot.setupHardcopyRoutes(server, folder)`, called from
  `runDash` with `Path.cwd()`, adds `GET /_hardcopy/folder` (the
  directory), `HEAD /_hardcopy/files/<name>` (200 or 404) and
  `PUT /_hardcopy/files/<name>` (write, 204) to the Flask server.
- A name must be one file name ending in `.png` with none of
  `<>:"/\|?*` or control characters (400 otherwise); the body must start
  with the PNG signature (400) and arrive as `image/png` (415).
- Only the server's own page can write: a cross-origin `PUT` of
  `image/png` needs a CORS preflight the server never grants, and the
  requests that need none are refused (405). The server binds to
  127.0.0.1.
- In `assets/hardcopy.js`, `serverFolder(path, fetch)` presents the
  routes as the subset of the folder-handle interface the writer uses, so
  existence checks, the overwrite prompt, leftovers and writing are the
  same code for both destinations.
- The box shows where Save writes. Save and Enter use the server; Choose
  folder opens the dialog (Chromium only, disabled elsewhere, with the
  explanation as its tooltip). Save works in any browser.

## Demonstration (R8)

| File | Content |
|---|---|
| `tools/make_hardcopy_demo_data.py` | Writes `data/hardcopy-demo.csv`: a `Time` column, 0 to 20 s at 0.01 s, and about a dozen dummy signals (sines of several frequencies, a ramp, a square wave, a step, seeded noise). Fixed seed, so the file is reproducible. |
| `data/hardcopy-demo.csv` | The generated data, tracked like the other demonstration data. |
| `hardcopy-example.json` | The demonstration configuration, three tabs, described below. |

| Tab | Content | What it exercises |
|---|---|---|
| `many` | 10 graphs, `Height` 150, `HardcopyGraphsPerPage` 4 | R1 (no boxes); R7 and R6: 3 pages holding 4, 4 and 2 graphs. |
| `mixed` | `commonX` set; 2 graphs at `Height` 300, then 4 at `Height` 150; no per-page row | R1 on a mixed `commonX` tab: an x range typed into a boxed graph also reaches the graphs without boxes. Default layout: 600 + 600 CSS px exceeds 1047, so 2 pages. |
| `boundary` | 2 graphs at `Height` 200, 1 at `Height` 201; no per-page row | The R1 threshold (200 has no boxes, 201 has them); single-page naming, `<name>.png`. |

## Verification

The repository has no automated tests (`suggestedwork.md`, section 4).
Rendering and file writing happen in the browser and cannot be exercised
from Python. Verification is therefore manual, in Chrome or Edge, against
servers started on ports from 8120 upward:

1. Each shipped configuration (`dash-config.xlsx`, `dash-config-sim.xlsx`,
   `dash-config.json`, `commonx-example.json`) still loads, and its
   range-entry, click and selection boxes still work. One included tab is
   affected by R1: `graph-gimbal` in `dash-config.xlsx` and
   `dash-config.json` has `Height` 200, so its two graphs lose their
   boxes. Every other included sheet has a `Height` of 220 or more and is
   unchanged.
1. `hardcopy-example.json`: tab `many` and the 150 and 200 graphs show no
   boxes; the 201 and 300 graphs do; typing an x range on a boxed graph of
   tab `mixed` zooms all six graphs.
1. Ctrl+Alt+H on each demonstration tab writes the expected number of
   files with the expected names.
1. Each file is checked by a short Python script for: 2480 x 3508 pixels,
   a `pHYs` chunk of 11811 pixels per metre with unit 1, and a valid CRC.
1. The pages are inspected by eye: no tab strip, no markdown, no boxes,
   current zoom preserved, text legible at 100 % print size.
1. Cancelling the name box, cancelling the folder dialog, and declining
   the overwrite prompt each leave no file written.

## Documentation to update

- `docs/userguide.md`: the `HardcopyGraphsPerPage` row, the 200 px box
  threshold, the keystroke and its browser requirement.
- `docs/SDD.md`: the new asset, the tab wrapper, the boxed-graph callback
  rule, and the code map.
- `README.md`: one line pointing at the hardcopy keystroke and the
  demonstration configuration.
- `archive-no-commit/handoff.md`: file inventory and design summary.

## Out of scope

- A toolbar or on-page button for hardcopy (the keystroke is the only
  trigger).
- PDF output, other paper sizes, landscape orientation.
- Page headers, footers, page numbers or titles on the hardcopy.
- Hardcopy in browsers without the File System Access API.
