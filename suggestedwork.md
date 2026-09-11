---
title: "dash-lineplot: Suggested Work"
date: "2026-09-11"
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

A review of the repository as it stands, listing defects, weak constructs,
dead code and modernisation opportunities, with a recommended order of
work. No code was changed in producing it.

Markdown flavour for this file: Native/KaTeX, with PDF-export front matter.

## Orientation

The repository is one large script, `dash-lineplot.py` (2125 lines), two
helper tools under `tools/`, a browser-side synchroniser in
`assets/graphsync.js`, a LaTeX guide under `doc/`, a markdown guide under
`docs/`, and a 122 MB vendored PyInstaller tree.

The recently added parts of the script -- the JSON config and data paths,
the enumeration handling, the commonX group logic, the x/y range boxes --
are in good shape: they carry real docstrings that explain intent, and they
are written defensively. The problems concentrate in the older layers: the
configuration walk, the Excel-era cell handling, the data-file reader, and
the callback registration loop, plus everything left stranded by the removal
of PySide, visdcc and the range slider.

## Verification status

Findings below were established by reading the code. Nothing could be
executed: this machine has no `pandas`, `dash`, `plotly` or `scipy`
installed, and no conda environment for the project, so no finding here
carries a reproduced traceback. Each entry states the input that reaches
the defect, so the claims are checkable once an environment exists. Building
that environment and adding the regression tests in
[Work package 6](#wp6-tests-and-tooling) is what turns this list from read-
verified into run-verified.

## Priority summary

| # | Item | Kind | Severity | Where |
|---|---|---|---|---|
| 1 | Data reader runs two mutually exclusive branches | Defect | High | `dash-lineplot.py:1484` |
| 2 | `dfData` can be unbound on return | Defect | High | `dash-lineplot.py:1502` |
| 3 | `skiprows` reaches -1 for a `.plt` with no `%` header | Defect | High | `dash-lineplot.py:1469` |
| 4 | File-type dispatch is case-sensitive and substring-based | Defect | High | `dash-lineplot.py:1551` |
| 5 | `np.isnan` on cells that may hold text | Defect | High | six sites, see below |
| 6 | Logo path is relative and bypasses `resource_path` | Defect | Medium | `dash-lineplot.py:1184` |
| 7 | Callbacks registered against components that never exist | Defect | Medium | `dash-lineplot.py:1722` |
| 8 | Header `%` stripping applies to one format only | Inconsistency | Medium | `dash-lineplot.py:1494` |
| 9 | Missing or misspelled config names fail with raw pandas errors | Robustness | Medium | `dash-lineplot.py:953` |
| 10 | Stylesheet is loaded twice | Defect | Low | `dash-lineplot.py:204` |
| 11 | Slider callbacks are dead | Dead code | Medium | `dash-lineplot.py:1975` |
| 12 | `jsString`, `allTabUsedIdx`, `reqStart`, `reqEnd` are dead | Dead code | Low | four sites |
| 13 | Module-level `global` state instead of instance state | Structure | High | 11 sites |
| 14 | Index strings parsed by `split('#')` and `split('-')` | Structure | Medium | `dash-lineplot.py:945` |
| 15 | Config walk is row-by-row `.loc` assignment plus `concat` | Performance | Medium | `dash-lineplot.py:1406` |
| 16 | Full trace data duplicated into `self.graphTraces` | Performance | Medium | `dash-lineplot.py:1146` |
| 17 | `list(ys)[index]` per trace per click | Performance | Medium | `dash-lineplot.py:658` |
| 18 | HTML copies of every graph written on every run by default | Behaviour | Medium | `dash-lineplot.py:862` |
| 19 | Config workbook opened twice | Performance | Low | `dash-lineplot.py:567` |
| 20 | Canonical-column and sheet-filter logic duplicated | Duplication | Medium | two files |
| 21 | PyInstaller spec still describes the Qt build | Stale | High | `dash-lineplot.spec` |
| 22 | 122 MB vendored third-party tree, 1229 tracked `.pyc` | Hygiene | High | `pyInstaller/` |
| 23 | No tests, no `pyproject.toml`, no linter config | Hygiene | High | repo root |
| 24 | `doc/*.tex` documents removed features | Stale | Medium | `doc/user.tex` |
| 25 | Modern-Python items | Modernisation | Low | many |

---

## 1. Defects

### 1.1 The data reader runs two mutually exclusive branches

`readdatafile` decides the file type into three independent flags and then
tests them in two separate `if` statements rather than one dispatch:

```python
if matlab or '.plt' in filename:      # line 1484
    df = pd.read_csv(filename, sep=r'\s+', ..., skiprows=skiprows)
    ...
if comma or '.csv' in filename:       # line 1499
    dfData = pd.read_csv(filename, sep=',', header=0)
```

`comma` is set from the presence of a comma anywhere in the first line
(line 1477). A MATLAB-style header such as `%time, x, y` therefore sets
both `matlab` and `comma`, both branches run, and the second silently
discards the first result -- including its `skiprows`, so the comment lines
are read as data. Any space-separated file whose header happens to contain a
comma is affected.

The same overlap exists for filenames: a file named `run.csv` written with
a `%` header hits both.

Fix: resolve the format once, then dispatch on it with `elif`, or better
with a small mapping from format to reader function. Make the format
decision explicit and testable -- a `detectFormat(path) -> str` helper with
its own tests is worth more here than any amount of inline flag juggling.

### 1.2 `dfData` can be unbound on return

Nothing guarantees that any branch assigned `dfData` before
`return dfData` at line 1502. A space-separated file with no `%` header,
no comma and an extension other than `.plt` or `.csv` -- which is exactly
what `tp05j2a_Observer0.traj` and the other `data/` files look like by
extension -- falls through every branch and raises
`UnboundLocalError`. The window widened when the `.scd`/`.spc` branch was
removed, because that branch used to catch two more extensions.

Fix: as part of the single-dispatch change in 1.1, make the fallback
explicit -- whitespace-separated is the sensible default for an unknown
extension -- and raise a named error for a format that genuinely cannot be
read, naming the file and what was tried.

### 1.3 `skiprows` reaches -1

Lines 1457 to 1469 count leading `%` lines and then subtract one to leave
the last comment line as the header:

```python
skiprows = skiprows - 1
```

For a `.plt` file with no `%` line at all, the count is 0 and `skiprows`
becomes -1, which is not a valid `read_csv` argument. The guard is missing
because the `.plt` extension and the `%` header are treated as the same
condition when they are not.

Fix: clamp to zero, and only enter the header-counting loop when a `%`
header was actually found.

Related, in the same block: `'%' in line` tests the whole line, not its
first character, so a data line containing a percent sign inside a column
name or a value is counted as a comment.

### 1.4 File-type dispatch is case-sensitive and substring-based

```python
extension = os.path.splitext(datapath)[1]    # line 1551
if 'mat' in extension: ...
elif 'xls' in extension: ...
elif 'json' in extension: ...
```

Two problems. The extension is not case-folded, so `.CSV`, `.XLSX` and
`.JSON` -- ordinary on Windows-authored data sets, and this repository is
explicitly cross-platform -- all fall through to the whitespace reader,
where an `.XLSX` will produce either a garbage frame or an exception.
And the tests are substring tests, the same construct that was just
removed from the column-heading code: any extension containing `mat`
matches the MATLAB branch.

Fix: `extension = os.path.splitext(datapath)[1].lower()` and compare
against a set per format, or key a dispatch dictionary on it.

### 1.5 `np.isnan` applied to cells that may hold text

Six sites call `np.isnan` directly on a configuration cell:

| Line | Cell |
|---|---|
| 376 | `Scale` on the `xValue` row |
| 378 | `Offset` on the `xValue` row |
| 864 | `Value` on the `ToDisk` row |
| 909, 916, 930 | `Scale`, `Offset`, `MarkerOpacity` on a `yValue` row |
| 991 | `Linewidth` on a `yValue` row |
| 1262 | `Value` on the `Include` row |

A numeric column that contains one text cell becomes `object` dtype, and
`np.isnan` on a Python string raises `TypeError: ufunc 'isnan' not
supported for the input types`. So a single typo in a spreadsheet cell --
`1,5` for `1.5`, a stray note, `yes` instead of `TRUE` -- takes the whole
page down with a numpy error that names nothing the user can act on. The
`Value` column in `dfPlotterConfig` is object dtype by construction, since
it carries titles and labels alongside numbers.

Fix: use `pd.isna`, which is total over `None`, `NaN`, `NaT` and strings,
and add one helper each for the three cell kinds actually in use:

```python
def cellFloat(value, default):
    """A numeric cell, or the default when blank or not a number."""

def cellFlag(value, default):
    """A boolean cell: TRUE/FALSE, 1/0, yes/no, or blank for the default."""

def cellText(value, default=''):
    """A text cell, or the default when blank."""
```

Routing every cell read through three named helpers removes roughly forty
lines of repeated `isinstance`/`isnan` guarding and gives one place to
report a bad cell with its sheet, row and column.

### 1.6 The logo path is relative and bypasses `resource_path`

```python
import base64                                                  # line 1183
encoded_image = base64.b64encode(open('icons/logoSet2long.png', 'rb').read())
```

Three faults in two lines. The path is relative to the working directory,
so the page fails whenever the script is run from anywhere but the
repository root -- while every other asset goes through `resource_path`,
which exists precisely for this. The file handle is never closed. And the
file is re-read and re-encoded once per tab, then embedded once per tab in
the served page.

Fix: read and encode once, in `__init__` or lazily behind a cached
property, through `resource_path`, inside a `with` block or via
`pathlib.Path.read_bytes()`.

### 1.7 Callbacks registered against components that never exist

`setupCallbacks` iterates `itertools.chain(allTabs, allGraphs)` at line
1722 and registers, for each name, a figure callback, a range-box callback
and click and selection callbacks.

`allTabs` holds sheet names, `graph-Velocity` and the like. But the Tab
component's id is set from the stripped label, `id=tabLabel` where
`tabLabel = graphTab.split('-')[1]`, and no component anywhere is given the
sheet name as its id. Every callback registered for an `allTabs` entry
therefore targets `Output('graph-Velocity', 'figure')`,
`Output('click-graph-Velocity', 'children')` and siblings that do not
exist. They are invisible only because `suppress_callback_exceptions` is
set.

`allGraphs` has a smaller version of the same problem: it is built for
every sheet at lines 1252 to 1258, before the `Include` flag is tested at
1262, so a tab switched off in the configuration still gets its full set of
callbacks registered against components that were never built.

Fix: register callbacks from `graphList`, the list of graph ids actually
placed on the page, and drop `allTabs`/`allGraphs` from the loop. This
removes roughly half the registered callbacks on a typical configuration,
which shortens start-up and stops masking real id mistakes. Once the dead
registrations are gone, consider dropping `suppress_callback_exceptions`
too, or keeping it only for the dynamic tab content that genuinely needs
it, so the next id mismatch is reported instead of ignored.

### 1.8 Header `%` stripping applies to one format only

The leading-`%` strip at line 1494 sits inside the whitespace branch of
`readdatafile`. A `.csv`, `.xlsx` or `.json` file whose first column is
named `%time` keeps the `%` in the column name, and a configuration that
names `time` then fails to find it. The normalisation belongs to the data,
not to one reader.

Fix: normalise column names once in `loadData`, after whichever reader
produced the frame, so every format is treated alike. Use
`str.removeprefix('%')` rather than `lstrip('%')`: `removeprefix` states the
intent exactly, where `lstrip` would also eat a legitimate `%%` prefix.

### 1.9 Missing or misspelled configuration names fail with raw pandas errors

Three failure modes reach the user as an unhelpful exception:

- a misspelled column name in `xValue` or a `yValue` row surfaces as a bare
  pandas `KeyError` naming the column but not the sheet, the row, the data
  file, or what column names the file does have (`dash-lineplot.py:953`,
  `:959`);
- a sheet with no `Datafile` row and no per-row override leaves
  `ctx['datafile']` as `None`, so the lookup is `self.datafiles[None]` ->
  `KeyError: None` (lines 948 and 952);
- a `yLabel` row missing for a set raises `KeyError` on
  `dft.loc['yLabel#' + setStr, 'Value']` (line 1043).

Fix: validate the resolved configuration once, before any graph is built,
and report every problem found rather than dying on the first. The message
should name the sheet, the row and the offending value, and for a column
name it should list the columns the file actually carries -- that one line
of output saves the user a session of guessing. This is the single largest
usability return available in the script.

### 1.10 The stylesheet is loaded twice

`external_stylesheets = ['assets/bWLwgP.css']` at line 204 is passed to
`dash.Dash`, while `assets_folder=resource_path('assets')` makes Dash serve
every file in that folder automatically -- as the header comment in
`assets/graphsync.js` itself notes. So `bWLwgP.css` is linked twice.

Fix: drop the `external_stylesheets` argument and let the assets folder do
its job. Keep the variable only if a genuinely external URL is ever needed.

## 2. Dead code and stale artefacts

### 2.1 The slider callbacks

Lines 1975 to 2027 register two callbacks, `process_xSlider_data` and
`reset_xSlider`, wired to six component ids: `xSlider-*`,
`submit-button-*`, `minVal-*`, `maxVal-*`, `resetSlider-*` and
`output-container-xSlider-*`. None of these components exists anywhere in
the layout; the slider was replaced by the x-range boxes, as
`generateFeedbackBoxes` records in its own docstring. The callbacks are
therefore unreachable, and they are the only remaining caller that passes
`reqStart`/`reqEnd` to `makeGraphSet`.

They also contain the only remaining use of `global divSets` for mutation
at line 2008, and a comparison `if start < sliderMinValues[tabNum]` that
would raise on the `''` the reset callback writes into the same box.

Fix: delete both callbacks, the `for gr in allTabs` loop that wraps them,
and `sliderMinValues`/`sliderMaxValues` if nothing else needs the tab x
extents. Keep the extents if the range-box placeholders should show the
per-tab range.

### 2.2 The visdcc hover injection

`JS_STR_template` (line 1666) and the `jsString` list built from it (lines
1682 to 1686) are never used: the only reader is the commented-out
`render_content` at lines 1700 to 1712. Cross-graph hover now lives in
`assets/graphsync.js`.

Fix: delete the template, the list, and the commented-out callback.
`graphsync.js` is the documented mechanism and the comment block only
invites someone to revive a dependency that was deliberately dropped.

### 2.3 `allTabUsedIdx`

Allocated at line 1238 and written at 1267, read only inside the same
commented-out block. Delete with 2.2.

### 2.4 `reqStart` and `reqEnd`

`makeGraphSet(self, dft, graph, reqStart=0, reqEnd=0)` at line 831 accepts
both, documents both, and uses neither -- the x window is now applied in
the browser by patching the axis range. With 2.1 gone, no caller passes
them.

Fix: remove both parameters and their docstring entries.

### 2.5 `__version__`

`__version__ = '$Revision: 4633 $'` at line 184 is an unexpanded SVN
keyword. Either set a real version string or drop the attribute.

## 3. Structural problems

### 3.1 Module-level `global` state

Eleven `global` statements carry the working state of a class method into
module scope: `divSets`, `graphTabs`, `graphList`, `sliderMinValues`,
`sliderMaxValues`, `allTabs`, `allTabUsedIdx`, `allGraphs` in
`prepareGraphs`; `dfPlotterHeader`, `pageDensity`, `dfPlotterConfig` in
`loadConfig`; `dashApp` in `run_dash`.

Consequences, in order of how much they cost:

- Two `DashLinePlot` instances in one process overwrite each other's
  configuration and page. The module docstring advertises exactly that
  use -- "To use as a module in another application" -- so the documented
  API is not safe to use twice.
- `makeGraphSet` reads `dfPlotterHeader` and `pageDensity` out of module
  scope while taking `dft` as an argument, so its inputs are half explicit
  and half ambient. Nothing about the signature says what it needs.
- A callback closure reading `divSets` at line 1735 depends on
  `prepareGraphs` having run first, with no way to assert it.

Fix: make all of them instance attributes -- `self.divSets`,
`self.config`, `self.header`, `self.density` and so on. `dashApp` becomes
`self.dashApp`, and the callback definitions already live in a method, so
they close over `self` naturally. This is a mechanical change, it touches
many lines, and it is the single largest improvement available to the
file's structure. Do it in its own commit, with no behaviour change
alongside it.

### 3.2 Index strings parsed by splitting

The configuration index encodes set and trace numbers into the row label,
`yValue#003-007`, and the graph code takes it apart with string surgery:

```python
setStr = str(index).split('#')[1].split('-')[0]     # line 945
setStr = str(index).split('#')[1]                   # lines 1036, 1255
```

Membership is then tested by substring, `if 'yValue#' + setStr in value`
at line 1066, and elsewhere `if 'Title' in row['Variable']` and
`if 'Datafile' in row['Variable']` (lines 1407 and 1414) test Variable names
by substring rather than equality -- so a Variable named `SubTitle` or
`DatafileB` would be taken for a `Title` or a `Datafile` row. The tab label
is derived as `graphTab.split('-')[1]` (line 1276), which truncates any
sheet named `graph-my-signals` to `my`.

Fix: carry set and trace numbers as their own integer columns -- `SetNum`,
`TraceNum` -- alongside the existing `Graph` and `ShtNum`, and select with
`dft[dft['SetNum'] == n]` instead of parsing a label. Compare Variable
names with `==`. Use `graphTab.split('-', 1)[1]` or
`graphTab.removeprefix('graph-')` for the label.

### 3.3 Duplicated configuration logic

`readConfigTables` in `dash-lineplot.py:536` and `workbookToDict` in
`tools/xlsx_config_to_json.py:45` each implement the `'graph' in sheetname`
sheet filter and the openpyxl-for-sheet-order trick, and
`CONFIG_COLUMNS`/`onCanonicalColumns` exist only in the former while the
latter has its own `cellValue`/`isEmpty` pair covering the same ground as
the cell helpers proposed in 1.5.

Fix: extract a small `configio.py` beside the script holding
`CONFIG_COLUMNS`, the sheet filter, the workbook reader and the cell
helpers, and import it from both. That also makes the config layer
testable without importing Dash.

Note while doing so that the sheet filter is itself a substring test:
`'graph' in sn` matches a sheet named `paragraphs`. `sn.startswith('graph-')`
is what is meant, and it should be defined once.

### 3.4 Local imports

`import plotly.offline as offline` (line 824) and `import base64`
(line 1183) sit inside functions with no reason -- both are cheap and both
are needed whenever the function is called. `from scipy.io import loadmat`
(line 1573) is a defensible lazy import, since scipy is only needed for
MATLAB files; if it stays, say so in a comment.

## 4. Performance

Ordered by what a large data set actually costs.

### 4.1 The configuration walk

`loadConfig` iterates each sheet row by row and writes back through `.loc`
on every iteration (lines 1406 to 1424), then grows the master frame with
`pd.concat` inside the sheet loop (line 1427). Both are the standard pandas
anti-patterns: each `.loc` assignment on a mixed-dtype frame can copy, and
each `concat` reallocates everything accumulated so far.

Fix: build the index labels as a list comprehension over the rows, assign
the column once, and collect the per-sheet frames in a list for a single
`pd.concat(frames)` after the loop. Configurations are small, so this is
about clarity as much as speed -- but it is also where the `SetNum`/
`TraceNum` columns of 3.2 naturally get built.

### 4.2 Trace data duplicated for the click readout

```python
self.graphTraces[grID] = [                                # line 1146
    (trace.get('name', ''), trace['x'], trace['y'], trace.get('text'))
    for trace in thisGraphData]
```

Every graph's full x and y are retained for the lifetime of the process so
a commonX click can be answered. For the 19000-point traces the code
comments mention this is tolerable; for a long run it is a second copy of
the entire data set, held per graph rather than per data file.

Fix: store what identifies the trace -- data reference, x column, y column,
scale and offset -- and read the values back from `self.datafiles` on
demand. The frames are already in memory. If the indirection is not worth
it, at least store `numpy` arrays converted once rather than pandas Series,
which also fixes 4.3.

### 4.3 Per-click linear work

`commonClickMessage` calls `nearestSample` for every trace of every graph
in the group on every click, and `nearestSample` builds a fresh
`np.asarray` over the whole x column each time (line 444). Then the y value
is read as `list(ys)[index]` (line 658), which materialises the entire y
series as a Python list to take one element.

Fix: `ys[index]` on the array, or `ys.iat[index]` on a Series. Cache the
`numpy` x array per trace at build time. For a monotonic x -- which a time
column is -- `np.searchsorted` answers in logarithmic rather than linear
time, and monotonicity can be checked once at load.

`commonSelectMessage` has the same `np.asarray` per call at line 688, and
its enumeration path builds `seen` with a linear `not in` scan per sample
(line 700), which is quadratic in the number of distinct states. A `dict`
preserves insertion order and makes it linear.

### 4.4 HTML copies written on every run

`toDisk` defaults to `True` at line 862, so every graph of every included
tab is written to `./graphs/` as a standalone HTML file on every start-up,
whether or not anyone asked. Each file embeds its own copy of the data and
of the plotly bundle. Start-up cost and disk use both scale with the data.

Note also that `.gitignore` describes the directory as "Generated by
graphToDisk when a sheet sets GraphToDisk", but the flag the code reads is
`ToDisk`. One of the two names is wrong.

Fix: default `toDisk` to `False` -- exporting is an explicit request, not a
side effect of viewing -- and reconcile the flag name between the code, the
`.gitignore` comment and the documentation. Create the output directory with
`os.makedirs(grDir, exist_ok=True)` rather than the
`if not os.path.exists` / `os.mkdir` pair at lines 858 and 859, which is a
race and needlessly two calls. While there, check `plotly.offline.plot`
against the pinned `plotly>=7.0`: `plotly.io.write_html` is the current API
for this and `plotly.offline` is legacy.

### 4.5 The configuration workbook is opened twice

`readConfigTables` builds a `pd.ExcelFile` and then calls
`oxl.load_workbook(configfile)` for the sheet order (lines 567 and 571),
parsing the file twice. `pd.ExcelFile` already holds the openpyxl workbook
as its `.book`, so the order is available without a second read. The same
duplication exists in `tools/xlsx_config_to_json.py`.

### 4.6 All tabs are built up front

`prepareGraphs` builds the full Div tree, figures included, for every
included tab before the page is served, and `render_content` then hands one
over per tab click. The comment at line 1307 says the opposite -- "no data
added ... the graphs are only added to the tab when the user clicks" --
but the data is embedded in `divSets` either way; only the transfer to the
browser is deferred.

Fix: either build a tab's Divs inside `render_content` on first use and
cache them, which is what the comment describes, or correct the comment.
The first is a real start-up saving on a many-tab configuration.

## 5. Modern Python

The environment pins `python>=3.13`, so everything here is available. None
of it changes behaviour.

- `class DashLinePlot():` -> `class DashLinePlot:` (line 599).
- `import sys, os` (line 186) -> one import per line.
- `resource_path` (line 213) uses `try: sys._MEIPASS / except Exception`,
  with the docstring outside the function body where it is a no-op
  statement rather than a docstring. Use
  `getattr(sys, '_MEIPASS', None)`, and fall back to the script's own
  directory, `Path(__file__).parent`, not `os.path.abspath('.')` -- the
  working directory is not where the assets are, which is the root cause of
  1.6.
- Replace `os.path` throughout with `pathlib.Path`: `splitext` ->
  `.suffix`, `join` -> `/`, `isfile` -> `.is_file()`,
  `basename` -> `.name`. This is also what makes the Windows/Linux path
  handling uniform, per the project's cross-platform rule.
- `'data:image/png;base64,{}'.format(...)` (line 1187) -> f-string, as the
  rest of the file already does.
- `matlabspace = True if ' ' == line[1] else False` (line 1476) ->
  `line.startswith('% ')`, which also removes an `IndexError` on a
  single-character first line, reachable because the length check that
  precedes it only tests for non-empty.
- `dash.callback_context` (lines 1752, 1868, 1934, 1994) -> `dash.ctx`,
  the current spelling. `ctx.triggered_id` replaces the
  `triggered[0]['prop_id'].split('.')[0]` idiom at lines 1756 and 1995.
- Shadowed builtin: the `id` parameter of `generateFeedbackBoxes`
  (line 716) and of `display_click_data` (line 1882) -- rename to
  `graphId`.
- `display_click_data` (lines 1882 to 1916) is indented two spaces where
  the file uses four, and stores click history in a four-element list
  indexed by magic positions, `self.clickedData[id][3][0]`. The commonX
  path already solved the same problem readably with a two-element history
  list; fold the two together or at least name the fields.
- Type hints on the module-level helpers -- `splitDataRef`, `readJsonData`,
  `traceYExtent`, `nearestSample`, `isEnumSeries`, `parseCategories`,
  `enumCategories`, `isJsonConfig` -- would document the contracts the
  docstrings already describe in prose. The class methods matter less.
- `print()` for error reporting (lines 1388, 1479, 1595) -> the `logging`
  module, or at minimum `file=sys.stderr`, so a caller embedding the
  plotter as a module can control it.
- `math.isnan`, `np.isnan` and `isinstance(x, float) and math.isnan(x)` are
  all in use for the same question. Standardise on `pd.isna` -- see 1.5.
- Docstrings say `(bolean)` in eleven places. Harmless, but it is one
  `sed` away.
- Naming is camelCase throughout, against PEP 8 but consistent and
  deliberate. Leave it. Consistency with the existing file beats
  conformance here, and a rename would obscure every future diff. The one
  exception worth making is the `resource_path`/`run_dash` pair, which are
  the only snake_case names in the file.

## 6. Repository hygiene

### 6.1 The PyInstaller spec describes a build that no longer exists

`dash-lineplot.spec` bundles `pyInstaller\qt\translations`,
`pyInstaller\qt\resources`, `QtWebEngineProcess.exe` and
`pyInstaller\visdcc`, and declares `hiddenimports=['PyQt5.QtWebEngineWidgets',
'PyQt5.QtNetwork', ...]`. PySide, Qt and visdcc are all removed
dependencies -- the module docstring and `README.md` both say so. It also
carries `pathex=['C:\\Temp']`, hard-codes backslash paths, and describes
itself in its own header as the spec for `p2TestbenchAssistant.py`.

`runPyInstaller.bat` matches it, deleting `PyQt5\Qt\bin\QtWebEngineProcess.exe`
after the build.

Fix: decide whether a frozen build is still wanted. If yes, rewrite the
spec for the current dependency set and make the paths relative. If no,
delete the spec, the `.bat` and the vendored tree together (6.2) -- a
build file that cannot work is worse than no build file, because someone
will try it.

### 6.2 The vendored third-party tree

`pyInstaller/` is 3012 of the repository's 3064 tracked files and 122 MB,
consisting of vendored copies of `dash`, `dash_core_components`,
`dash_html_components`, `dash_renderer`, `plotly`, `visdcc` and Qt
runtime pieces. It includes 1229 tracked `.pyc` files compiled for
CPython 3.7, against an environment that now pins Python 3.13.

Every clone pays 122 MB for a build that no longer works, and the tree
pins vendored copies of libraries the environment installs properly from
conda-forge.

Fix: delete the tree, in the same change as 6.1. If a frozen build returns,
PyInstaller resolves the packages from the environment; it does not need
them vendored. Note that deleting it does not shrink the history -- the
objects stay in the pack -- so if clone size is the actual concern, say so
and a history rewrite can be considered separately. That is a rewrite of
published history and needs a deliberate decision, not a side effect of
this cleanup.

### 6.3 No tests, no packaging metadata, no linter configuration

There is no test of any kind, no `pyproject.toml`, no
`requirements.txt`, and no linter or formatter configuration. `environment.yml`
is the only dependency declaration, and it is conda-only.

The absence of tests is what makes every item above riskier than it needs
to be: there is no way to show that a refactor of `readdatafile` or a move
of the globals onto the instance preserved behaviour.

Fix, in the order that pays off soonest:

1. A `pyproject.toml` with `[tool.ruff]` configured to the file's actual
   style, so the dead names in section 2 would have been reported
   automatically. `ruff` also finds the unbound-variable class of defect in
   1.2.
1. `pytest` tests for the pure helpers, which need neither Dash nor a
   browser: `splitDataRef`, `readJsonData` on all three shapes and all
   three error paths, `parseCategories`, `enumCategories` including the
   append-unknown-states rule, `isEnumSeries`, `selectionBounds` for box
   and lasso, `nearestSample`, `traceYExtent`, `resolveSetContexts` for a
   multi-block sheet, and `readConfigTables` on a workbook and its
   converted JSON -- the last of which is also the regression test that the
   two formats agree.
1. Round-trip tests for `readdatafile` over small fixtures covering each
   format in section 1: `%` header with and without a space, a `%` header
   containing a comma, a comma file, an uppercase extension, an unknown
   extension.
1. A `pip`-installable declaration alongside `environment.yml`, so the
   package can be installed without conda.

### 6.4 Other

- `__pycache__/` exists in the working tree and is correctly ignored, but
  1229 `.pyc` files are tracked under `pyInstaller/` -- see 6.2.
- `dash-config.xlsx`, `dash-3dof.xlsx`, `exmple-dash-config.xlsx` and
  `commonx-example.json` sit in the root as both examples and live
  configuration. Moving the examples into `examples/` would make it clear
  which one the default `-f ./dash-config.xlsx` refers to.
  `exmple-dash-config.xlsx` is also a typo for `example-`.

## 7. Stale documentation

`doc/user.tex` documents the range slider at length, with three figures --
section "Slider Usage" at `doc/user.tex:184`, and the submit-button
workflow at `:204`. The slider does not exist; its callbacks are the dead
code of 2.1.

`doc/system.tex:19` lists visdcc as a dependency, `:20` and `:33` list
PySide and Qt, and `:35` pins visdcc 0.0.40 on Python 3.7. `:89` tells the
reader to `conda install pyside2`.

`README.md:105` and `:122` still reference the range-slider documentation
and the visdcc bz2 install, although the surrounding text at `:82` and
`:228` correctly records the removals.

The module docstring in `dash-lineplot.py` is 180 lines and mostly a Dash
tutorial transcribed from `dash.plot.ly` around 2019 -- the `Tab` property
list at line 149, the `getting-started` notes at line 111. It also
describes a `DashPlotWindow` class, at line 101, that no longer exists:
the snippet the docstring offers as the module API would raise
`ImportError`.

Fix: bring `doc/*.tex` in line with the current feature set -- the x-range
boxes replace the slider section, and the dependency list loses Qt and
visdcc. Cut the module docstring to what the module actually does and
offers, and let `docs/userguide.md` carry the usage narrative. The
tutorial material is on the Dash site and does not need a copy here.

## 8. Suggested order of work

Sequenced so that each package leaves the tree working, and so that the
tests exist before the invasive changes.

### WP1 -- Deletions

Sections 2.1 to 2.5, 6.1, 6.2. Dead callbacks, the visdcc remnants, the
unused parameters, the stale spec and `.bat`, the vendored tree. Nothing
here can change behaviour, and it removes roughly 3000 files and 122 MB
before anyone has to read around them. Do the tree deletion as its own
commit so it can be reverted independently of the code deletions.

### WP2 -- Cell handling and file-type dispatch

Sections 1.1 to 1.5, 1.8. The three cell helpers, one format dispatch,
case-folded extensions, the `skiprows` clamp, header normalisation moved to
`loadData`. This is where the user-visible crashes are, and it is
self-contained.

### WP3 -- Asset and start-up fixes

Sections 1.6, 1.7, 1.10, 4.4, 4.5. The logo path and caching, callback
registration from `graphList`, the duplicate stylesheet, `toDisk` defaulting
off, the single workbook read. Small, independent, immediately visible in
start-up time.

### WP4 -- Validation and error reporting

Section 1.9. One validation pass over the resolved configuration, reporting
every problem with sheet, row, value and the available column names. Best
done after WP2, whose cell helpers it uses.

### WP5 -- Structure

Sections 3.1 to 3.4, 4.1, plus the `configio.py` extraction. Globals onto
the instance, set and trace numbers as columns, shared configuration
module. The largest and riskiest package: do it after WP6 exists, one
concern per commit, no behaviour changes mixed in.

### WP6 -- Tests and tooling {#wp6-tests-and-tooling}

Section 6.3. `pyproject.toml` with `ruff`, then the helper tests, then the
`readdatafile` fixtures. Bring this forward ahead of WP5 -- the helper
tests are worth writing before anything is restructured, and `ruff` would
have found most of section 2 on its own.

### WP7 -- Performance

Sections 4.2, 4.3, 4.6. Trace storage, per-click work, deferred tab
building. Worth measuring before doing: on a modest data set none of it is
noticeable, and the read-back-from-frames change in 4.2 trades memory for
indirection. Measure with the largest run available, then decide.

### WP8 -- Documentation

Section 7 and the module docstring. Last, so it describes the code as it
then stands rather than being rewritten twice.

### Modernisation

Section 5 is not a work package. Fold each item into whichever package
touches that code, so no commit is a pure style change over code that is
about to move anyway.
