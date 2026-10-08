# dash-lineplot -- Task Handoff Document

Status: 2026-10-08 -- browser-served Dash viewer for time-series data,
configured by an Excel workbook or an equivalent JSON file, reading CSV,
XLSX and JSON (including multi-rate JSON) data. Work happens directly on
`master`. Committed up to `8313ec9` (hardcopy to the working directory or
a chosen folder).

Uncommitted in the working tree when this was written -- check
`git status`, and note that several new files still have to be added,
not just staged as modifications (`tests/test_commonx_range.py` and
`tests/test_legend.py` were untracked):

- A `yValue` row may name its own x column (`xValue` cell), so one graph
  can plot one quantity from several files with differently named time
  columns; demonstrated by `multisource-example.json`.
- A blank `PageBottom` header cell no longer crashes the page build.
- A `commonX` tab's graphs start on, and return to, the tab's exact x
  extent.
- Legend settings at page, tab and graph level: `LegendTransparency`,
  `LegendOrientation`, `LegendX`, `LegendY`.
- Every example carries `LegendTransparency` 0.7; both workbooks were
  edited through their XML and `dash-config.json` regenerated from the
  workbook.
- `suggestedwork.md` re-triaged, `docs/userguide.md` and `docs/SDD.md`
  brought to current status with history and legacy text removed.

Two working-tree items are the user's, not an agent's: a modified
`archive-no-commit/prompt.md`, and an untracked `engagementproforma.json`
in the repository root. Leave both alone.

No work is in progress; the next work is whatever the user picks from
`suggestedwork.md` (section 5).

History-file cadence: size threshold, 30 KB.

The early work was recorded in the sibling `systemCHandbook` repository
(WP2 of its development plan); this repository's handoff and history are
authoritative for `dash-lineplot` (section 8).

## 1. File Inventory

Guidance: key files/folders and what each one is.

| Path | What it is |
|---|---|
| `dash-lineplot.py` | The whole application, one file of about 2360 lines: config and data loading, graph building, Dash callbacks, the hardcopy server routes, CLI entry point. |
| `assets/graphsync.js` | Browser script served by Dash's assets folder: page-wide hover sync, `commonX` x linking, Autoscale to the tab extent. |
| `assets/hardcopy.js` | Browser script for the Ctrl+Alt+H hardcopy. Its pure functions are exported under node for `tests/hardcopy.test.js`. |
| `assets/bWLwgP.css`, `assets/density.css` | Page styling; `density.css` drives the compact/comfortable layout and documents the row layout. |
| `icons/logoSet2long.png` | Logo embedded at the foot of every tab; read at import time, so the script fails to start without it. |
| `dash-config.xlsx` | The default configuration workbook (the CLI default). Its `documentation` sheet lists the variables and ends with a dated change log. |
| `dash-config.json` | The JSON twin of `dash-config.xlsx`. Regenerate it with `python tools/xlsx_config_to_json.py dash-config.xlsx` after editing the workbook; never hand-edit it. |
| `dash-config-sim.xlsx` | A second example workbook, plotting `data/sensor-tel-test*.txt` (the `%` comment-header variants). |
| `commonx-example.json` | `commonX` linked tab and the same graphs unlinked; also the three `LegendTransparency` levels (page 0.7, tab `independent` 0.4, its second graph 0). |
| `hardcopy-example.json` | Hardcopy and the 200 px box threshold: tabs `many` (10 graphs, 4 per page), `mixed` (`commonX`, mixed heights), `boundary` (200 vs 201). Data from `tools/make_hardcopy_demo_data.py`. |
| `multisource-example.json` | One quantity from three files per graph (`t`, `time`, `CurrentSimTime` on 0.1/0.25/0.5 s grids) via the per-row `Datafile`/`xValue` overrides; also the legend layout at three levels. Data from `tools/make_multisource_demo_data.py`. |
| `data/` | The data the example configs use; only these files are tracked. Do not leave ad-hoc run data here. |
| `tools/config_from_run.py` | First-pass JSON config for a directory of JSON telemetry: one tab per group, one graph per field, text columns as enumerations. |
| `tools/xlsx_config_to_json.py` | Workbook to JSON config converter; reads `header` and the `graph` sheets only. |
| `tests/` | 43 pytest (`python -m pytest tests`) and 8 node (`node --test tests/hardcopy.test.js`) tests. `conftest.py` loads `dash-lineplot.py` by path and builds a page from a config; `tests/pngcheck.py page.png` checks a written hardcopy page. Covers the work since the hardcopy feature only. |
| `README.md` | Quick start and the example configs. |
| `docs/userguide.md` | The user-facing reference, current state only. LaTeX-conversion-safe markdown, CRLF in the working copy. |
| `docs/SDD.md` | Software design description, current state only, with a code map of line ranges that must be regenerated when the file changes shape. LaTeX-conversion-safe, Pandoc/Puppeteer front matter. |
| `docs/superpowers/specs/2026-10-08-hardcopy-design.md` | The hardcopy spec, amended to match what was built. |
| `docs/superpowers/plans/2026-10-08-hardcopy.md` | The executed hardcopy plan; a record, not maintained. |
| `doc/*.tex`, `doc/pic/` | A stale 2020 LaTeX guide, each chapter marked historical. **The user will remove this tree; do not delete it.** |
| `environment.yml` | Portable conda environment: version floors only, no build strings, no `prefix:`. |
| `suggestedwork.md` | The forward-looking backlog only (see section 4). |
| `archive-no-commit/closed-history.md` | Write-ups of every closed backlog item and past review pass, including the accepted hardcopy edge cases (pass 6). |
| `archive-no-commit/prompt.md` | The user's own prompt file: read when relevant, never edit. |
| `graphs/` | `ToDisk` output, git-ignored. May hold the user's files; never clean it out. |
| `.superpowers/sdd/2026-10-08-hardcopy/` | Git-ignored scratch from executing the hardcopy plan (ledger, briefs). Safe to delete. |

## 2. Current Design

Guidance: what the system does now, stated plainly.

The tool serves a Dash/Flask page to the system browser:

```bash
python dash-lineplot.py --configfile <path> [--port N] [--datadir DIR]
```

**Configuration.** A `header` of page-level settings and any number of
graph sheets, one browser tab each, in a workbook or a JSON file;
`readConfigTables` reads either into the same table shape.

**Data.** CSV-style text (first line or first `%` comment line gives the
column names), XLSX (first sheet), and JSON: a top-level list is one
table, a top-level object is a set of named groups selected as
`file.json#group`. Nothing is ever merged, resampled or aligned between
tables; each is drawn at its own rate. `self.datafiles` is keyed by the
exact `Datafile` reference, fragment included.

**Blocks and per-row overrides.** A sheet is read top to bottom: a
`Height` row opens a block, and `Datafile`, `xValue` and `xLabel` rows
apply to the graphs below until replaced. A `yValue` row may name its
own file and x column in its `Datafile` and `xValue` cells; x scale,
offset, label and format stay the block's (one x axis per graph).

**Enumerations.** A text column is plotted as integer codes drawn as
steps (`line.shape = 'hv'`), with the y axis relabelled by name; the
order is the declared `Categories` or first appearance, and a value
missing from a declared order is appended, never dropped.

**Hover and `commonX`** (`assets/graphsync.js`). Hovering any graph shows
every graph's readout at that x, each against its own samples. A
`commonX` tab ties its graphs to one x range: zoom, pan, click and
selection apply to all. Its graphs start on the tab's exact x extent
(Plotly's autorange pads marker traces), and Reset, Autoscale and Reset
axes return there (`commonXExtent`, `data-x-extent`).

**Range boxes and readouts.** Beside each graph: typed X/Y ranges with
Apply and Reset (patched into the figure with `Patch()`; on a `commonX`
tab x reaches every graph, y only the graph used), Click Data, and, when
a trace has markers, Rectangle Tool Selection Data. A mouse zoom writes
its range back into the boxes.

**Small graphs.** A block `Height` of 200 or less (`BOXES_MIN_HEIGHT`)
gives no box column and no callbacks writing into one. Such a graph takes
the full row, except on a `commonX` tab with boxed graphs, where an empty
spacer column keeps x aligned (`hasBoxColumn`, `alignToBoxes`).

**Legend.** Inside each plot, shaped by `LegendTransparency` (0 solid
white to 1 fully see-through, default 0.4, drawn as alpha
`1 - LegendTransparency`), `LegendOrientation` (`v`/`h`), `LegendX` and
`LegendY` (0 to 1, default top-right, anchors `auto`). Each resolves on
its own: header for the page, a sheet row before the first `Title` for
the tab, a row after a graph's `Title` for that graph
(`resolveLegendSettings`, `LEGEND_DEFAULTS`, `LEGEND_CHECKS`).

**Layout and export.** Compact density by default: readouts beside the
graph, no gap between rows, title inside the plot. `ToDisk` true writes
standalone HTML copies to `./graphs/`; a missing row means off.

**Server start-up.** `freePort` picks the requested port or the next free
one; several servers can run side by side (section 3).

**Hardcopy.** Ctrl+Alt+H writes the visible tab's graphs as A4 portrait,
300 dpi PNG pages (`name.png` or `name-p1.png`, ...). Save writes into
the server's working directory through the `/_hardcopy` routes
(`setupHardcopyRoutes`), in any browser; Choose folder uses the
Chrome/Edge folder dialog. Graphs only, current zoom included;
`HardcopyGraphsPerPage` gives equal slots, otherwise on-screen heights.
Existing files are overwritten only after a `confirm`; older pages of the
same name that are not replaced are reported, never deleted. Each tab is
wrapped in a `graph-tab` div whose data attributes carry the tab name,
the per-page setting and the `commonX` extent.

## 3. Critical Implementation Details

Guidance: current behavior that isn't obvious from the code and is worth
not silently forgetting.

- `Height` becomes a CSS length with `px` appended; a bare number is
  invalid CSS and Plotly silently falls back to 450 px.
- A blank workbook cell, or a JSON `null`, arrives as NaN, not `''`. Read
  every header and sheet cell through `cellText`, `cellFloat` or
  `cellFlag`; a raw `.loc[..., 'Value']` used as a string crashes.
- Box Select and Lasso Select report different keys in `selectedData`
  (`range` vs `lassoPoints`); both must be handled.
- The sync guard in `graphsync.js` is a per-graph counter, not one
  page-wide flag: `Plotly.relayout` is asynchronous, and a flag cleared on
  the next line races the echo it suppresses. On a `commonX` tab an
  Autoscale drives every graph of the group, the autoscaled one included,
  to the extent; otherwise that graph keeps its padded range.
- The legend rows on a graph sheet are positional: before the first
  `Title` they are the tab's, after a `Title` that graph's. A row left at
  the end of a sheet, where `Include`/`ToDisk` usually go, belongs to the
  last graph.
- `openpyxl` silently drops workbook parts it does not model, so the
  workbooks are edited through their XML when nothing else may change:
  map sheet names to `xl/worksheets/sheetN.xml` through `xl/workbook.xml`
  and its rels; write `t="inlineStr"` text cells and numeric `<v>` cells;
  widen `<dimension ref>`; copy every other zip entry byte for byte in
  order; confirm only the intended entries changed.
- `tools/xlsx_config_to_json.py` reads only `header` and sheets whose name
  contains `graph`; the `documentation` sheet is for people only.
- pandas 3: a filtered frame keeps its row labels, so `series[0]` can
  raise `KeyError: 0`; use `.values[0]` or `.iloc[0]`. Dash 4: the
  server method is `run`, not `run_server`.
- `freePort`: on Windows, Werkzeug's `SO_REUSEADDR` lets a second server
  bind a busy port. A port is accepted only if an exclusive bind
  (`SO_EXCLUSIVEADDRUSE` on Windows) succeeds and then nothing answers a
  connect; the bind runs first because a refused loopback connect costs
  the full 0.5 s timeout, which would make skipping a reserved range
  (`netsh interface ipv4 show excludedportrange protocol=tcp`) take
  minutes. The chosen port is `self.port`.
- Hardcopy: `showDirectoryPicker` must be called synchronously from the
  Choose folder click (user activation); its `startIn` takes only a
  handle or a well-known folder, never a path, hence the server routes. A
  Save-As picker cannot write pages 2 onward. `serverFolder` mimics the
  part of the folder-handle interface the writer uses; keep both
  destinations in step.
- The `/_hardcopy` write route is a `PUT` of `image/png` on purpose: a
  cross-origin page cannot send it without a CORS preflight, which the
  server never grants (verified: only the OPTIONS reached the server; a
  plain `POST` got 405). Never relax it to `POST` or `text/plain`. Dash
  refuses every request until a layout is set, so a test app needs
  `app.layout = html.Div()`.
- `canvas.toBlob` records no resolution, so `setPngDpi` inserts a `pHYs`
  chunk; hardcopy sizes are worked in CSS px (96/inch) and rendered with
  `scale = 300/96` so text keeps its physical size.
- `pkill -f dash-lineplot.py` from a shell running that command matches
  its own process too.

## 4. Standing Constraints

Guidance: decisions marked "do not silently revisit", one line each on
why.

- **The tool knows nothing about any caller's project layout.** Data is
  found through `--datadir` and the config; `tools/config_from_run.py`
  plus a hand-edited config is the bridge, never code in the tool.
- **Never merge or resample tables.** A zero-order hold belongs to the
  process that caused it, not to the plotting layer.
- **Cross-platform (Ubuntu and Windows).** `pathlib.Path` only; no
  hard-coded paths, drive letters or home directories.
- **`environment.yml` pins version floors only**, never build strings or a
  `prefix:`, so one file solves on both platforms.
- **Work happens on `master`** (user's decision).
- **Claude never commits or pushes**, and does not offer to; the user
  commits everything.
- **`archive-no-commit/` is always committed, despite its name.** The name
  comes from the handoff-management convention; the repository is cloned
  to several PCs and these files must travel with it.
- **`suggestedwork.md` stays forward-looking only.** A closed item's
  write-up moves to `archive-no-commit/closed-history.md` and the item is
  deleted, never marked closed in place.
- **`dash-config.json` is generated from `dash-config.xlsx`**, never
  hand-edited (the workbook is the reference format).
- **`LegendTransparency` means transparency: 0 solid white, 1 see-through**
  (user's decision; the earlier opposite meaning read backwards).
- **Legend positions stay within 0 to 1** (inside the plot): a legend
  outside widens that graph's margin and breaks x alignment.
- **Tests run from scratch working directories** when a config exports
  (`ToDisk`) or a hardcopy is saved, so nothing lands in the repository or
  in the user's `graphs/`.

## 5. Current Backlog

Guidance: prioritized, currently open items only.

Read `suggestedwork.md` for the backlog; do not copy it here. In one
line: instance state instead of module globals, `SetNum`/`TraceNum`
columns instead of parsed index strings, the `configio.py` extraction,
tooling (linter, `pyproject.toml`) and tests for the older code,
performance items not yet worth measuring, and small items -- click
history shared between browsers (3.5), dead `UseSubplots` rows (3.7),
selection callbacks without a box (3.9), the hardcopy slot seam (3.10),
an unreachable fallback (3.11). Its own section 5 says to start with tests
and tooling.

`suggestedwork.md`'s `dash-lineplot.py` line citations and `docs/SDD.md`'s
code map are current for the working file. Refresh both whenever the file
changes shape: remap each citation by diffing the version it was last
checked against with the current file, confirm each cited line still
holds the same source text, and regenerate the code map from the `def`
lines rather than editing numbers by hand.

Left undone deliberately: subplot-scoped hover (page-wide hover in
`graphsync.js` replaced it; revisit only if missed), and three accepted
hardcopy edge cases (`closed-history.md` pass 6).

## 6. How to Cold-Restart

Guidance: the minimum steps a fresh session needs to resume work
correctly.

1. Read this file and the current (highest-numbered) file under
   `handoff-history/` -- never an older, closed one.
1. `git status`, `git branch -vv` and `git log --oneline -10` for the
   real state; trust them over any hash or file list quoted here.
1. Use the `dashplot` conda environment, by path if conda is not on
   `PATH` (section 7).
1. `docs/userguide.md` says how the tool behaves, `docs/SDD.md` how it is
   built; do not restate them here. A code change usually needs both,
   `README.md`, and the SDD code map regenerated.
1. `suggestedwork.md` says what is wrong and what to do next;
   `archive-no-commit/closed-history.md` why closed items are the way they
   are.
1. When working from a caller project (originally `systemCHandbook`),
   reach this tool by relative path only; it never learns the caller's
   layout (section 4).
1. Run `python -m pytest tests` and `node --test tests/hardcopy.test.js`
   from the repository root (43 and 8 passing). Then start the shipped
   configs (`dash-config.xlsx`, `dash-config-sim.xlsx`,
   `dash-config.json`, `commonx-example.json`, `hardcopy-example.json`,
   `multisource-example.json`) and check each page loads. `dash-config.*`
   export two tabs with `ToDisk`, so run those from a scratch directory
   with `--datadir <repo>`. Use ports checked free beforehand (8120
   upward, never 8050, which the user may be using) and stop only the
   processes the test started, after checking each PID's command line.
1. Browser testing in the desktop app's built-in pane: start hardcopy
   tests from an empty scratch directory with `--datadir <repo>`; emulate
   a wide viewport (e.g. 1400 px) before checking layout, since the narrow
   pane collapses the grid; screenshots time out, so to see a page image
   post its blob to a throwaway local receiver and read the file; the
   native folder dialog cannot be driven, so replace
   `window.showDirectoryPicker` with a stand-in object that stores the
   blobs.

## 7. Technical Reference

Guidance: config format, key function signatures, dependencies.

**Environment.** `environment.yml` floors: Python 3.13, Dash 4.4, Plotly
7.0, pandas 3.0, numpy 2.5, openpyxl 3.1 (last full solve: Python 3.14.7,
Dash 4.4.1, Plotly 7.0.0, pandas 3.0.5, numpy 2.5.3, openpyxl 3.1.5).

- Ubuntu: Miniforge at `~/miniforge3`, no `conda init`; invoke
  `~/miniforge3/envs/dashplot/bin/python` by path.
- Windows: Anaconda,
  `C:\Users\nwillers\AppData\Local\anaconda3\envs\dashplot\python.exe`
  (Git Bash: `/c/Users/nwillers/AppData/Local/anaconda3/envs/dashplot/python.exe`),
  with Python 3.14.7, Dash 4.4.1, Plotly 7.1.0, pandas 3.0.2, numpy 2.4.4
  (below the 2.5 floor) and pytest. Node v24 is on `PATH` for the JS
  tests. `conda env list` prints a harmless `anaconda-anon-usage` error
  first.

**Configuration schema.** A `header` Variable/Value table and graph
sheets of rows with the columns in `CONFIG_COLUMNS` (`Variable`, `Value`,
`Format`, `LineLabel`, `GraphType`, `Scale`, `Offset`, `Colour`,
`Linewidth`, `Dash`, `Mode`, `MarkerOpacity`, `Categories`, `Datafile`,
`xValue`); JSON mirrors the workbook one for one. Header variables:
`Pagetitle`, `PageTop`, `PageBottom`, `Datafile`, `Density`, and the four
legend settings. Sheet rows beyond the graph rows: `Height`, `Datafile`,
`xValue`, `xLabel`, `GraphTop`, `GraphBottom`, `Include`, `ToDisk`,
`commonX`, `HardcopyGraphsPerPage`, and the legend settings (positional,
section 3). Full reference: `docs/userguide.md`.

**Hardcopy routes** (`setupHardcopyRoutes`, registered by `runDash` with
`Path.cwd()`): `GET /_hardcopy/folder` gives `{"path": ...}`;
`HEAD /_hardcopy/files/<name>` 200 or 404; `PUT` of an `image/png` PNG
writes it, 204. Bad name 400, non-PNG body 400, other content type 415.

**Entry points.**

```bash
python dash-lineplot.py --configfile <path> [--port 8050] [--datadir DIR]
python tools/config_from_run.py <directory>
python tools/xlsx_config_to_json.py dash-config.xlsx
```

`--datadir` resolves relative `Datafile` references; a `#group` fragment
selects one group of a multi-rate JSON file.

## 8. History Index

Guidance: edit the STATE sections above in place, never append a new
top-level section with a fresh number. Session narrative goes in the
current history file, not here.

- `handoff-history/handoff-history-001-2026-09-onward.md` -- closed and
  frozen at 29.7 KB. Opens with the narrative carried over from the
  sibling `systemCHandbook` repository (its sessions 7 to 10 and
  `docs/devplan/wp2-dashboard-fork.md`; expect some duplication with
  that repository's WP2 record), then this repository's sessions from
  2026-09-14 through the first hardcopy round.
- `handoff-history/handoff-history-002-2026-10-onward.md` -- current,
  actively appended: the hardcopy follow-ups, backlog triage,
  `dash-config.json` regeneration, the per-trace x column, the
  `PageBottom` fix, the `commonX` start range, the legend settings and
  the `LegendTransparency` rename, and the documentation cleanup.
