---
title: "dash-lineplot: Suggested Work"
date: "2026-09-14 (third pass)"
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

# dash-lineplot: Suggested Work

A review of the repository, listing defects, weak constructs, dead code and
modernisation opportunities, with a recommended order of work.

Markdown flavour for this file: Native/KaTeX, with PDF-export front matter.

This is the third pass over this document. The first pass (2026-09-11,
commit `3bc7304`) was read-only. The second pass, earlier the same day,
found and fixed the broken-callbacks defect (N1 below) while fixing an
unrelated zoom-controls bug the user reported. This third pass, later the
same day, fixes two more user-reported defects -- missing axis labels (N5)
and Scale/Offset leaking into every hover/click/selection value (N6) -- and
then does a documentation sweep across the whole repository (not just this
file) at the user's request, since by this point the gap between what the
docs claimed and what the code did had grown in more than one place. Every
item below has been re-checked against the current code and docs and marked
**Closed**, **Open**, **Partly done** or **New**.

**Standing decision, recorded 2026-09-14:** the xlsx configuration path is
the one in daily use and stays the primary, actively maintained format. JSON
config support is kept for the cases it already serves, but is not where
further investment should go -- no new JSON-only features, and any shared
refactor (`configio.py`, validation, cell helpers) should be judged by
whether it helps the xlsx path, not by JSON parity. This reprioritises
WP5 and the tools/ deduplication below.

## Verification status

Most findings are now checked against the running application (conda env
`dashplot`, `dash-lineplot.py -f dash-config.xlsx`), not just read from the
source, so several of this pass's findings carry more confidence than the
first pass's did. Items not exercised in the browser are marked as such.

## Closed since the last review

| # | Item | How it was closed |
|---|---|---|
| 1.1 | Data reader ran two mutually exclusive branches | `readdatafile` rewritten as a single scan-then-parse pass (`dash-lineplot.py:1480`). No more `matlab`/`comma` flag pair. |
| 1.3 | `skiprows` could reach -1 | Same rewrite: `skip_count` only increments on an actual `%` line, never decremented. |
| 1.5 | `np.isnan` on cells that may hold text | `cellFloat`/`cellText`/`cellFlag` helpers added and used at every site the original table listed. |
| 1.7 | Callbacks registered against components that never exist | Original defect (`allTabs`/`allGraphs`) was replaced by a *different* broken loop (`itertools.chain(graphList)`, which doesn't flatten a list of lists) in commit `a37bd56`, then fixed to `itertools.chain(*graphList)` in this session, 2026-09-14. Verified in the browser: Apply/Reset on the X/Y range boxes now work. See the new finding N1 below for how this regressed in between. |
| 1.10 | Stylesheet loaded twice | `external_stylesheets` no longer passed to `dash.Dash(...)`; the assets folder serves it once. (Left behind a dead module-level variable -- see N4.) |
| 2.2 | `visdcc`/hover-injection dead code (`JS_STR_template`, `jsString`, commented `render_content`) | Deleted outright. |
| 2.3 | `allTabUsedIdx` | Deleted outright. |
| 2.4 | `reqStart`/`reqEnd` on `makeGraphSet` | Parameters removed; no caller passed them anyway. |
| 2.5 | `__version__` SVN keyword | Attribute removed. |
| 5 | `class DashLinePlot():` -> `class DashLinePlot:` | Done. |
| 5 | `import sys, os` -> one per line | Done. |
| 5 | f-string for the base64 image `src` | Done. |
| 5 | Shadowed builtin `id` (`generateFeedbackBoxes`, `display_click_data`) | Renamed to `graphId` in both places, and `display_click_data`'s indentation was straightened to four spaces at the same time. |
| 5 | `math.isnan`/`np.isnan` mixed with the rest | Standardised on `pd.isna`; `import math` removed. |
| 5 | `(bolean)` typo in docstrings | Fixed everywhere; none remain. |
| N2 | MATLAB (`.mat`) support undocumented after removal | Resolved by finishing the removal: `scipy` dropped from `environment.yml`, and every doc site corrected -- see "Documentation sweep" below. |

## New findings, this pass (second pass, callback fix)

### N1. The zoom Apply/Reset buttons were completely broken (now fixed)

`setupCallbacks` (`dash-lineplot.py:1682`, was `:1722`) builds one callback
per graph by iterating what it believes is a flat list of graph ids. Commit
`a37bd56` changed the source of that iteration from
`itertools.chain(allTabs, allGraphs)` (flat, but targeting ids that mostly
don't exist -- the original item 1.7) to `itertools.chain(graphList)`.
`graphList` is a *list of lists*, one list of graph ids per tab, and
`itertools.chain()` given a single argument does not flatten it -- it just
walks the outer list. So `gr` was bound to each tab's whole list of ids, and
`theGraph = str(gr)` produced ids like
`"['graph-RelativePosition000', 'graph-RelativePosition001']"`, wired to
components that never existed. Every per-graph callback was affected: the
X/Y range Apply/Reset buttons, the range-box-follows-mouse-zoom sync, and
both click and selection readouts. This is why the range boxes accepted
typed values but Apply visibly did nothing.

Fixed in this session by flattening correctly: `itertools.chain(*graphList)`.
Verified by starting the app and driving the X-range boxes in the browser:
Reset returns to the full data range, and typing `1`/`5` and clicking Apply
zooms the axis to exactly `[1, 5]`.

This closes item 1.7 for real, but it is worth recording that a mechanical,
one-token change to a `for` loop took down every interactive control on the
page with no exception raised anywhere (`suppress_callback_exceptions` is
still `True` -- see 1.7's original fix note, still open). **This is the
strongest argument in the repository for WP6 (tests) landing before WP5
(structure): the next refactor of this exact loop deserves a regression
test, not a bug report.**

### N2. MATLAB (`.mat`) support was silently dropped, but was still documented as current -- now closed

The rewrite of `loadData`'s extension dispatch (`dash-lineplot.py:1578`)
deleted the `'mat' in extension` branch and the `from scipy.io import
loadmat` import along with it -- reasonably, since nothing in this
repository's own data or configs used it. But several places still told a
reader `.mat` is supported: `README.md`, `docs/userguide.md`, `doc/func.tex`
(plus `environment.yml`, which still pinned `scipy`) -- see the original
list this finding shipped with, in the version-history of this file, for
the exact line numbers at the time.

A `.mat` file named in a configuration still does not raise a clear error
today -- `extension` is `.mat`, matches neither `'xls'` nor `'json'`, and
falls to `self.readdatafile(datapath)`, which will try to open a binary
MATLAB file as text and fail confusingly -- but this is no longer a
*documentation* problem: every site above was corrected in this pass's
"Documentation sweep" to say plainly that `.mat` is not supported, rather
than either restoring the reader or leaving the docs wrong. If MATLAB
support is ever needed again, it must be re-implemented, not re-enabled --
the reader is gone, not disabled.

### N3. `readdatafile` now requires a file to have a `%`-prefixed header line

The rewritten `readdatafile` (`dash-lineplot.py:1480`) scans leading lines,
keeps the first one that starts with `%` as `header_line`, and then does:

```python
header = header_line.strip().removeprefix("%")   # line 1511
```

If the file has *no* `%` line at all -- an ordinary CSV with a plain
top-of-file header, exactly what `docs/userguide.md:157` documents as
supported (`` `.csv` and most others | Column names on the top line, one
sample per line. ``) -- `header_line` is still `None`, and this raises
`AttributeError: 'NoneType' object has no attribute 'strip'`. This is the
same class of defect as the original item 1.2 (`dfData` unbound), in a new
shape: the rewrite fixed the traced failure but introduced a different
unconditional crash on a documented, previously-working input. It has not
been hit in this repository only because every shipped data file
(`data/*.traj`) happens to carry a `%` header.

Fix: when no `%` line is found, fall back to the ordinary case -- read row
1 as the header (`pd.read_csv(..., header=0)` with the same multi-separator
`sep` regex) rather than raising. Add this exact case (plain CSV, no `%`)
to the fixture list in WP6; it is the one most likely to recur, since it is
what any tool other than the ones already writing `%`-headed `.traj` files
will produce by default.

### N4. Dead `external_stylesheets` module-level variable

Closing item 1.10 (dropping the `external_stylesheets=` keyword from
`dash.Dash(...)`) left the variable itself, `external_stylesheets =
[str(resourcePath('assets/bWLwgP.css'))]` (`dash-lineplot.py:226`), with no
reader anywhere in the file. Small, but worth folding into WP1's next pass.

## New findings, third pass (user-reported, this session) -- both fixed

### N5. Axis labels were missing on every graph (fixed)

`xaxis`/`yaxis` titles were built as plain strings --
`'xaxis':{'title': ctx['xlabel'], ...}` and `yAxisDict = {'title': yLabel,
...}`. Plotly.js 4 (bundled by the `dash>=4.4` this environment now pins)
accepts a bare string for `title` without error -- `gd.layout.xaxis.title`
reads back correctly -- but renders it as nothing: the `<g class="g-xtitle">`
element exists in the DOM with empty text content. Confirmed with
`Plotly.relayout(gd, {'xaxis.title': {text: '...'}})` in the browser
console: the object form renders immediately, the string form never did.

Fixed by wrapping both in `{'text': ...}`, at `dash-lineplot.py:1193`
(`yAxisDict`) and `:1202` (`xaxis`). Verified in the browser: "Time [s]"
and "Distance [m]" (etc.) now show on every graph, in both `compact` and
`comfortable` density.

### N6. Scale and Offset leaked into every value the reader read off (fixed)

A `yValue` row's `Scale`/`Offset` (and a block's `xValue` `Scale`/`Offset`)
are meant to be a *display* convenience only, so traces of very different
magnitude -- the user's own example was microvolts and megavolts -- can
share one axis. They were not display-only: the hover tooltip, the Click
Data box, and the Rectangle Tool Selection Data box all read the value
straight back off the trace's plotted `x`/`y`, which *is* the scaled,
offset one. A line configured with `Scale=0.01` (the shipped
`dash-config.xlsx` has one, `Missile rol/100`) reported `0.225` on hover
where the recorded value was `22.5125`.

Fixed by giving every trace a `customdata` array carrying the true,
unscaled x (and for a numeric trace, the true y) alongside the plotted one,
and reading from it everywhere a value is displayed:

- Each trace's `hovertemplate` now renders `customdata`, not the default
  `%{y}`, so the native Plotly hover tooltip shows the recorded value
  (`dash-lineplot.py:1069-1090`, completed once the graph's y hoverformat
  is known at `:1150-1157`).
- `commonClickMessage` and `commonSelectMessage` (the `commonX` readouts,
  `:689` and `:744`) now read each trace's value from `customdata` instead
  of its plotted `y`, and convert the clicked x / selection edges back to
  true x through a new `self.graphXAxis[grID]` = `(xscale, xoffset)`
  recorded per graph (`:1260`) -- a selection box's edges are a plot
  position with no recorded sample behind them, so there is nothing else to
  convert them from.
- `display_click_data` (`:1901`, the non-`commonX` click box) now prefers
  the clicked point's own `customdata` over its plotted `x`/`y`.
- `display_selected_data` (`:1979`, the non-`commonX` rectangle-select box)
  previously reported the selection box's raw top-left/bottom-right
  corners. That report is not just stale but ambiguous: two lines on one
  graph can carry different `Scale`/`Offset`, so a box corner has no single
  true value to convert to. It now delegates to `commonSelectMessage`,
  which already solves this correctly by reporting each line's own true y
  extent inside the selected x window -- the non-`commonX` and `commonX`
  selection boxes now report in the same format. This is a visible
  behaviour change, documented in `docs/userguide.md`'s "Rectangle Tool
  Selection Data" section.

Verified in the browser on `Missile rol/100` (`Scale=0.01`): hover tooltip,
Click Data, and Rectangle Tool Selection Data all report `22.5125` (or the
correct value at other points/windows), never the scaled `0.225`, across
both a plain graph and a `commonX`-linked pair. The X-range zoom controls
(N1) were re-tested alongside and are unaffected.

## Documentation sweep, this pass

Requested by the user directly: "update all documentation ... with current
status." Covered every `.md`, `.tex` and the module docstring, plus
`environment.yml`, not just this file.

- **`environment.yml`**: dropped `scipy`, unused since the MATLAB reader
  was removed (resolves N2).
- **`README.md`**: dropped the MATLAB bullet from "What it does" (with a
  note on why, and a pointer to the known `%`-header limitation); dropped
  the dead range-slider link; dropped `scipy` from the two dependency/
  license lines; fixed "To use as a module", which told a reader to import
  a `DashPlotWindow` class that no longer exists.
- **`dash-lineplot.py` module docstring**: the same `DashPlotWindow`
  mistake existed here too (it's what `README.md`'s example was copied
  from) -- fixed the same way. Also dropped `scipy` from the license header
  and the dependency line, and the dead range-slider and Plotly-subplots
  links. Rewrote the stale comment block above `setupCallbacks` that
  described a removed `visdcc`/subplot hover mechanism attached to code
  that no longer does that -- current hover sync is `assets/graphsync.js`,
  already documented at the top of the file.
- **`docs/userguide.md`**: removed the `.mat` row and the "scipy needed for
  Matlab" requirement; replaced the stale "Matlab reader carried forward,
  unverified" TODO with an accurate note that it was removed outright, not
  carried forward; **added an explicit "known limitation, not the intended
  design" callout** for N3 (the plain-CSV-without-`%` crash) rather than
  either hiding it or silently documenting the crash as if it were the
  spec; added a note under `Scale`/`Offset` stating the N6 guarantee
  explicitly (values shown are always true, never scaled); rewrote the
  "Rectangle Tool Selection Data" section to match N6's behaviour change.
- **`doc/*.tex`** (`intro.tex`, `func.tex`, `system.tex`, `user.tex`,
  `lic.tex`): this whole LaTeX guide describes a March-2020, Qt-desktop-
  window, PyInstaller-packaged, Plotly-subplot version substantially
  different from the current one, and until this pass carried no warning
  saying so beyond a note in `docs/userguide.md` that a reader of the LaTeX
  guide directly would never see. Added an explicit "this guide/chapter is
  historical" notice to the Introduction and to the top of every affected
  chapter, pointing at `docs/userguide.md` as current. Also fixed the
  handful of plain-text factual errors that don't depend on regenerating
  screenshots: the MATLAB bullet in `func.tex`, the licence and dependency
  lists in `system.tex` (which no longer match `README.md`'s), the PySide/Qt
  line in `lic.tex`'s LGPL section, and the "subplots" claim in `user.tex`'s
  Click Data description. **What this pass did not do**: rewrite the
  screenshots-and-figures narrative (the Slider Usage subsection, the
  subplot-vs-no-subplot comparison figures, the PyInstaller folder-structure
  figures) to describe the current UI -- that needs new screenshots this
  session cannot produce, and the historical notice is judged sufficient to
  stop the guide from being *mistaken* for current, which was the actual
  risk. See WP8 below for whether a full rewrite is still worth doing.

## Priority summary

| # | Item | Kind | Severity | Status |
|---|---|---|---|---|
| N1 | Every per-graph callback silently mis-wired (`itertools.chain(graphList)`) | Defect | Critical | **Closed** 2026-09-14, see above |
| N2 | `.mat` support removed but still documented; `scipy` now an orphaned dependency | Defect/Stale | High | **Closed** 2026-09-14 -- documentation and `environment.yml` corrected |
| N3 | `readdatafile` crashes on a plain CSV with no `%` header | Defect | High | Open (new shape of old item 1.2) -- now clearly flagged in `docs/userguide.md` as a known limitation rather than silently documented as spec |
| N5 | Axis labels missing on every graph (Plotly.js 4 needs `title: {text:...}`) | Defect | High | **Closed** 2026-09-14, see above |
| N6 | Scale/Offset leaked into hover, click and selection values | Defect | High | **Closed** 2026-09-14, see above |
| 1 | *(was: data reader ran two branches)* | Defect | — | Closed |
| 2 | *(was: `dfData` could be unbound)* | Defect | — | Closed by the same rewrite, see N3 |
| 3 | *(was: `skiprows` reached -1)* | Defect | — | Closed |
| 4 | File-type dispatch is substring-based | Defect | Medium | Partly done -- now case-folded (`.suffix.lower()`), still `'xls' in extension` / `'json' in extension` rather than equality |
| 5 | *(was: `np.isnan` on text cells)* | Defect | — | Closed |
| 6 | Logo path is relative and bypasses `resourcePath` | Defect | Medium | Open, unchanged |
| 7 | *(was: callbacks registered against components that never exist)* | Defect | — | Closed, see N1 |
| 8 | Header `%` stripping applies to one format only | Inconsistency | Low | Mostly moot -- only one text reader remains, but still not normalised in `loadData` |
| 9 | Missing/misspelled config names fail with raw pandas errors | Robustness | Medium | Open, unchanged |
| 10 | *(was: stylesheet loaded twice)* | Defect | — | Closed, minor residue N4 |
| 11 | Slider callbacks are dead | Dead code | Low | Partly done -- commented out, not deleted |
| 12 | *(was: `jsString`, `allTabUsedIdx`, `reqStart`/`reqEnd` dead)* | Dead code | — | Closed |
| 13 | Module-level `global` state instead of instance state | Structure | High | Open, unchanged |
| 14 | Index strings parsed by `split('#')`/`split('-')`, Variable names compared by substring | Structure | Medium | Open, unchanged |
| 15 | Config walk is row-by-row `.loc` plus `concat` | Performance | Medium | Open, unchanged |
| 16 | Full trace data duplicated into `self.graphTraces` | Performance | Medium | Open, unchanged |
| 17 | `list(ys)[index]` per trace per click | Performance | Medium | Open, unchanged (now also in `commonClickMessage`) |
| 18 | HTML copies of every graph written by default | Behaviour | Medium | Open -- `toDisk` still defaults `True`; `.gitignore` still names the wrong flag |
| 19 | Config workbook opened twice | Performance | Low | Open, unchanged |
| 20 | Canonical-column/sheet-filter logic duplicated (script vs. `tools/xlsx_config_to_json.py`) | Duplication | Medium | Open, unchanged -- reprioritised (xlsx-first), see WP5 note |
| 21 | PyInstaller spec still describes the Qt build | Stale | High | Open, untouched since 2020 (now explicitly flagged as non-working in `doc/system.tex`) |
| 22 | 122 MB vendored third-party tree, 1229 tracked `.pyc` | Hygiene | High | Open, untouched |
| 23 | No tests, no `pyproject.toml`, no linter config | Hygiene | High | Open -- and N1 is the demonstration of why this matters |
| 24 | `doc/*.tex` documents removed features | Stale | Medium | Partly done -- every chapter now carries an explicit "historical, superseded" notice pointing at `docs/userguide.md`, and the plain-text factual errors (licences, dependencies, MATLAB) are corrected; the screenshots-and-figures narrative (slider, subplots, PyInstaller packaging) is not rewritten |
| 25 | Modern-Python items | Modernisation | Low | Partly done, see the closed-items table; remainder below |

---

## 1. Defects still open

### 1.4 File-type dispatch is still substring-based

```python
extension = Path(datapath).suffix.lower()    # line 1571 (case-folding now done)
if 'xls' in extension: ...                   # line 1578
elif 'json' in extension: ...                # line 1583
```

The case-sensitivity half of this is fixed. The substring half is not: an
extension containing `xls` or `json` as a substring of something else would
still misdispatch, though in practice this is now low-risk since the set of
extensions actually reaching this code is small and controlled by the
config. Low effort, low payoff -- fold into whichever change next touches
this block rather than doing it alone.

### 1.6 The logo path is still relative and bypasses `resourcePath`

Unchanged from the first review:

```python
encoded_image = base64.b64encode(open('icons/logoSet2long.png', 'rb').read())  # line 1229
```

Still relative to the working directory rather than routed through
`resourcePath` (which now exists and is used for `assets/`), still an
unclosed file handle, still re-read and re-encoded once per tab. The
`resourcePath` fallback itself (`dash-lineplot.py:221`,
`base_path = Path(".").resolve()`) is the root cause: it resolves against
the working directory, not the script's own directory, so this bug and any
future one like it will recur wherever a relative asset path is added.

Fix, in order: change `resourcePath`'s fallback to
`Path(__file__).resolve().parent`, which is correct regardless of where the
script is invoked from; then route the logo through it, read once (cached
on `self` or a module-level constant computed at import time), inside a
`with` block.

### 1.9 Missing or misspelled configuration names still fail with raw pandas errors

Unchanged. Still the single largest usability return available, and now
slightly cheaper to build than before, since `cellFloat`/`cellText`/
`cellFlag` already exist to build a validator on top of.

### 1.11 `suppress_callback_exceptions` still hides the class of bug N1 was

This is what let N1 run silently for however long it was live. Noted as a
`# todo` comment in the code already (`dash-lineplot.py:1629-1631`). Worth
promoting from a comment to a tracked item: once callback registration is
driven only by `graphList` (which it now is, since N1's fix), the dynamic
content that still needs suppression is just the tab-switch `children`
output. Scoping suppression to that one callback, rather than the whole
app, would have surfaced N1 immediately as a startup error instead of a
silent no-op button.

## 2. Dead code, revisited

### 2.1 The slider callbacks are commented out, not deleted

`dash-lineplot.py:1934` onward still carries `process_xSlider_data` and
`reset_xSlider` in full, as a `#`-commented block, rather than removed as
the original review recommended. Functionally equivalent to deletion --
nothing executes -- but it is 90-odd lines of commentary on a feature three
generations removed (Qt slider -> range slider -> current range boxes),
and it is what a future reader will assume is one uncomment away from
working when it is not (`sliderMinValues`/`sliderMaxValues` are the only
things still computed for it). Low-risk deletion, any time.

## 3. Structural problems -- all still open

Section unchanged from the first review: 11 `global` statements carrying
class state at module scope, index strings parsed by `split('#')`/
`split('-')`, `'Title' in var_name`-style substring tests standing in for
equality (`dash-lineplot.py:1463` and siblings), and the tab label still
truncating at the first `-` (`graphTab.split('-')[1]`, line 1317). Nothing
here regressed and nothing here was touched. See the original document's
text for the full detail; it still applies verbatim. The one thing worth
adding, given the standing decision above: **do the `SetNum`/`TraceNum`
column work (3.2) against the xlsx path's test fixtures first** if WP6 and
WP5 proceed, since that is the path every real configuration in this
project uses.

## 4. Performance -- all still open

Unchanged: the row-by-row `.loc` config walk with per-sheet `concat`
(4.1), the full trace duplication into `self.graphTraces` (4.2, now also
read via the newer `commonClickMessage`/`commonSelectMessage` helpers that
did not exist at the first review -- same cost, same fix), `list(ys)[index]`
materialising a full column per click (4.3), `toDisk` defaulting to `True`
(4.4, and the `.gitignore` comment still says `GraphToDisk` while the code
reads `ToDisk`), the workbook opened twice (4.5), and all tabs built up
front despite the comment claiming otherwise (4.6). No data set large
enough to make these visible has been run against the current code in this
session, so severity is unchanged from "worth doing, not urgent" -- measure
before investing, as WP7 already said.

## 5. Modern Python -- remainder

Closed items are in the table above. Still open:

- `resourcePath`'s `try: sys._MEIPASS / except Exception` -> could still
  become `getattr(sys, '_MEIPASS', None)`, and its fallback still needs the
  `Path(__file__).parent` fix from 1.6/N... above regardless of style.
- `os.path` remains in active use alongside `pathlib.Path` in the same
  file (`os.mkdir(grDir)` at `dash-lineplot.py:920`, versus
  `Path(grDir).exists()` two lines above it) -- the conversion from the
  first review is about half done, which is arguably worse than not
  started, since the file now has two idioms for the same thing instead of
  one.
- `dash.callback_context` is still used at three sites (lines 1712, 1828,
  1894) rather than `dash.ctx`/`ctx.triggered_id`.
- The four-element magic-index click history (`self.clickedData[graphId][3][0]`,
  `dash-lineplot.py:1853` on) is unchanged; `commonClickMessage`
  (added since the first review) already solved the same problem with a
  plain two-element list and reads far better -- worth folding
  `display_click_data` onto the same shape rather than maintaining both.
- Type hints on the module-level helpers: still none. The helper set has
  grown since the first review (`cellFloat`, `cellText`, `cellFlag` all
  postdate it) and all three are exactly the kind of small, pure function
  hints pay for immediately.
- `print()` for error reporting: unchanged, still three sites.
- Naming: still deliberately camelCase and consistent; still leave it, per
  the first review's own reasoning.

## 6. Repository hygiene -- unchanged

`dash-lineplot.spec` still describes the removed Qt/PySide/visdcc build
with a hard-coded `C:\\Temp` path (6.1); the 122 MB, 3012-file vendored
`pyInstaller/` tree is untouched (6.2); there is still no test, no
`pyproject.toml`, no `requirements.txt`, no linter configuration (6.3).
Nothing here was in scope for the work that has happened since the first
review, so none of it regressed, but none of it has moved either.

One addition to 6.3's fixture list, from N3 above: the `readdatafile`
round-trip tests should include a plain CSV with no `%` header, since that
is the one currently-undetected crash.

## 7. Stale documentation -- largely addressed this pass

The plain-text factual errors this section originally listed are fixed:
`README.md`'s range-slider and `DashPlotWindow` references, the module
docstring's matching mistakes, and `doc/system.tex`'s licence/dependency
lists (PySide, visdcc, Qt, `scipy`) are all corrected, and every LaTeX
chapter now says plainly that it is historical and points at
`docs/userguide.md`. N2 (the `.mat` doc mismatch) is closed -- see the
"Documentation sweep" section above for the full list of files touched.

**What is not done**: the LaTeX guide's screenshots and the prose built
around them -- `doc/user.tex`'s Slider Usage subsection and its subplot-
vs-no-subplot comparison figures, `doc/system.tex`'s PyInstaller
folder-structure figures -- still describe the 2020 UI, because doing this
properly needs new screenshots of the current browser display, which this
pass could not produce. The historical notice on each chapter is judged
sufficient to stop a reader from mistaking the content for current; a full
rewrite is downgraded to optional in WP8 below rather than dropped, since
`docs/userguide.md` is now the complete, accurate, actively maintained
guide and the LaTeX document's main remaining value is the PDF export
workflow itself, not any content unique to it.

## 8. Suggested order of work

Revised from the first review: N1 is done, and the user's standing
decision to keep xlsx as the primary, maintained format reprioritises the
JSON-adjacent parts of WP5.

### WP1 -- Deletions (unchanged scope, slightly smaller)

Sections 2.1 (now: actually delete the commented slider block), 6.1, 6.2,
plus N4 (the dead `external_stylesheets` variable). Nothing here can change
behaviour.

### WP2 -- Data-path correctness

N2 is closed. What remains is N3: the plain-CSV-without-`%` fallback in
`readdatafile`, plus its fixture. This is the highest-value remaining
package -- it is a user-visible crash on the exact data-loading path, now
clearly flagged in the docs but not yet fixed in the code.

### WP3 -- Asset and start-up fixes

Sections 1.6 (logo path, folded together with `resourcePath`'s cwd-vs-
script-dir fallback), 1.4's residual substring dispatch, 4.4, 4.5. Small,
independent, immediately visible in start-up time and in "does it work when
launched from a shortcut/cron/other cwd".

### WP4 -- Validation and error reporting

Section 1.9, unchanged from the first review, now with `cellFloat`/
`cellText`/`cellFlag` already available to build on. Build and test this
against xlsx configurations specifically, per the standing decision --
JSON's error paths (`readJsonData`'s `ValueError`s) are already reasonably
good and are not what a working session actually exercises.

### WP5 -- Structure

Sections 3.1 to 3.4, 4.1. Globals onto the instance, `SetNum`/`TraceNum` as
columns, `configio.py` extraction. Reprioritised: do the xlsx-side
extraction and structure work; do not extend it to close JSON/xlsx parity
gaps unless a gap actively blocks the xlsx path. This is still the largest
and riskiest package -- do it after WP6, one concern per commit.

### WP6 -- Tests and tooling

Section 6.3, plus the fixture WP2 needs (plain-CSV-no-`%`, from N3; a
`.mat` fixture is no longer relevant now that N2 is closed as "removed"
rather than "restore"). N1 is the concrete argument for pulling this
forward: a one-token change silently broke every button on the page,
with no exception anywhere, because nothing exercised
`setupCallbacks`/`graphList` outside a human clicking around in a browser.
A test as simple as "build the callback graph for the shipped
`dash-config.xlsx` and assert every registered `Output`/`Input`/`State` id
exists in the rendered layout" would have caught both N1's regression and
the original item 1.7 it replaced.

### WP7 -- Performance

Unchanged: sections 4.2, 4.3, 4.6. Measure with the largest run available
before investing.

### WP8 -- Documentation

Largely done this pass -- see Section 7 and "Documentation sweep" above.
What is left is optional: a full rewrite of `doc/user.tex`'s and
`doc/system.tex`'s screenshots-and-figures content (new screenshots of the
current browser UI, dropping the slider/subplot/PyInstaller narrative
rather than just flagging it historical). Worth doing only if the LaTeX
PDF itself is still wanted as a deliverable; if `docs/userguide.md` is
sufficient going forward, this can be deprioritised indefinitely rather
than scheduled.

### Modernisation

Section 5's remainder is still not a work package on its own -- fold each
item into whichever package touches that code.
