# dash-lineplot -- Task Handoff Document

Status: 2026-09-14 -- browser-served Dash viewer, modernised off a 2022
conda-and-Qt base. Reads Matlab, CSV, XLSX and JSON data (including
multi-rate JSON), configured by an Excel workbook or an equivalent JSON
file. Runs on `feature/modernise-and-json`, pushed to `origin`, not merged
to `master`; that stays the user's decision.

History-file cadence: size threshold, 30 KB (matching the convention this
work already used in the `systemCHandbook` handoff it was split out of).

This work was originally developed and recorded inside the sibling
`systemCHandbook` repository's own handoff, history files and
`docs/devplan/wp2-dashboard-fork.md` (WP2 of that project's development
plan), because the two repositories were being worked on together in one
session. It has now been split out here so this tool can be worked on in
its own right, independently of that project. Nothing in `systemCHandbook`
was edited to remove it -- see the note at the end of section 8.

## 1. File Inventory

Guidance: key files/folders and what each one is.

| Path | What it is |
|---|---|
| `dash-lineplot.py` | The whole application: config loading, data loading, graph building, Dash callbacks, CLI entry point. About 2000 lines, one file. |
| `assets/graphsync.js` | Browser-side JavaScript, served automatically by Dash's assets folder. Page-wide hover sync and `commonX` axis linking -- see section 2. |
| `assets/bWLwgP.css`, `assets/density.css` | Page styling. `density.css` drives the compact/comfortable layout toggle. |
| `dash-config.xlsx` | The default configuration workbook (`-f ./dash-config.xlsx` is the CLI default). Points at the bundled `data/` folder and is the one that actually renders. |
| `dash-config.json` | The JSON-format equivalent of `dash-config.xlsx`, produced by `tools/xlsx_config_to_json.py`. The two are expected to stay behaviourally identical. |
| `dash-3dof.xlsx` | A ready-made viewer for the `CB_3dof` project's telemetry: eight sheets, one per file in that project's `out/ENG-01`, signals grouped rather than one graph per column. Runs without `--datadir`. This is the one file here that is specific to a caller project; everything else in the tool is general-purpose. |
| `commonx-example.json` | A small runnable example demonstrating the `commonX` axis-linking feature. |
| `data/` | The data files the bundled example configs reference: `.rgeo`, `.traj`, `.gmbl` (OSSIM-style space/comma-separated text) and one `.xlsx`. |
| `tools/config_from_run.py` | Generates a first-pass JSON configuration for a directory of JSON telemetry files: one tab per data group, one graph per field, enumerations detected and plotted rather than skipped. |
| `tools/xlsx_config_to_json.py` | Converts an `.xlsx` configuration workbook to the equivalent JSON schema, losslessly (verified by round-trip comparison against `dash-config.xlsx`). |
| `docs/userguide.md` | The maintained user-facing reference for the tool as it stands today. Follows the markdown house style, LaTeX-conversion-safe flavour. Read this, not `doc/*.tex`, for how to use the tool. |
| `doc/*.tex`, `doc/pic/` | A March-2020 LaTeX user guide. **Stale** -- documents the removed PySide/Qt desktop window, the removed range slider (with three figures), and `visdcc` as a live dependency. Every chapter now carries a "this is historical, see `docs/userguide.md`" notice (added a session ago) rather than being half-fixed. **The user has said they will remove this tree themselves; do not delete it.** |
| `environment.yml` | Portable conda environment, pins version floors only, no build strings, no `prefix:`. Solves on both Linux and Windows. See section 7 for the versions it currently solves to. |
| `suggestedwork.md` | A read-verified code review of this repository: defects, dead code, structural problems, and an eight-work-package remediation plan. This is the current backlog in detail; section 5 below only summarises it. |

## 2. Current Design

Guidance: what the system does now, stated plainly.

The tool serves a Dash/Flask page to the system browser -- there is no
desktop window; the PySide2/PyQt5 shell was removed because PySide2 has no
Python 3.14 support and the window added nothing the browser does not
already do. It is invoked as:

```bash
python dash-lineplot.py --configfile <path> [--port N] [--datadir DIR]
```

**Configuration** is an Excel workbook or an equivalent JSON file: a
`header` sheet/object of page-level settings, and any number of graph
sheets/objects, each becoming one browser tab. `readConfigTables` reads
either format into the same table shape, so the rest of the code never
has to care which one it got.

**Data** can be Matlab (`scipy.io.loadmat`), CSV, XLSX, or JSON. JSON
supports two shapes: a top-level list is one record array (one table); a
top-level object is a set of named groups, one per sample rate, each
selected in the config as `file.json#group`. Nothing is ever merged,
resampled, or aligned between files or between groups of one file -- each
table is drawn at its own rate, because a zero-order hold belongs to the
process that caused it, never to the plotting layer. `self.datafiles` is
a dictionary keyed by the exact `Datafile` reference string (fragment
included), one `DataFrame` per file or per group.

**One tab, several files.** A graph sheet is read top to bottom as a
sequence of blocks: a `Height` row opens one, and `Datafile`, `xValue` and
`xLabel` rows apply to every graph below until the next one of that kind
replaces them. A single-block sheet behaves exactly as it always did. This
is what lets one tab compare signals recorded at genuinely different
rates.

**Enumerations.** A column whose values are text (not numeric, not
boolean) is plotted as a state signal: its distinct values are mapped to
integer codes, drawn as a step line (`line.shape = 'hv'`, since a state is
piecewise constant), and the y axis is relabelled with the original names.
Category order is either declared in the config (`Categories`) or taken
from first appearance in the data; a value present in the data but absent
from a declared order is appended, never dropped.

**Page-wide hover and `commonX`**, both in `assets/graphsync.js`, plain
browser JS served automatically from the `assets` folder (replacing the
`visdcc` mechanism that stopped working upstream). Hovering any graph
shows every other graph's readout at that x, each against its own
samples -- nothing interpolated. A tab that sets `commonX` ties every
graph on it to one x range: zoom, pan, click and rubber-band selection on
any of them apply to all of them.

**Typed X/Y range entry**, replacing the range slider that had stopped
working upstream (it depended on a tab-click to trigger a redraw). Plain
text inputs beside each graph (no browser draws chrome on a text input,
which a numeric input's spinner arrows do inconsistently), with Apply and
Reset. On a `commonX` tab, x reaches every graph in the group; y applies
only to the graph whose own boxes were used, because the graphs of a tab
have their own scales and often their own units. Apply patches the
existing figure's axis range (`Patch()`) rather than sending a new figure,
so a large trace is not re-transmitted to change a zoom. A mouse
zoom/pan/autoscale writes the resulting range back into the boxes.

**Compact layout.** Readouts sit beside the graph rather than under it,
with zero vertical space between graph rows and the title drawn inside
the plotting area (`xref/yref: 'paper'`), so a tall stack of small graphs
does not waste page height on Plotly's default margins.

## 3. Critical Implementation Details

Guidance: current behavior that isn't obvious from the code and is worth
not silently forgetting.

- `Height` must resolve to a valid CSS length. The code appends `px`; a
  bare numeric string is invalid CSS and Plotly silently falls back to its
  450 px default with no error.
- On a `commonX` tab, y-range entry deliberately does not fan out: only
  the graph whose own Apply button was pressed gets its y range changed.
  x does fan out to every graph in the group.
- Box Select and Lasso Select report different keys in `selectedData`
  (`range` vs `lassoPoints`); both must be handled or lasso selection
  silently does nothing.
- The hover/zoom sync guard in `graphsync.js` is a per-graph counter, not
  a single page-wide boolean -- `Plotly.relayout` is asynchronous, and a
  boolean cleared on the next line races the echo it is meant to suppress.
- `openpyxl` silently drops workbook parts it does not model (it removed
  `printerSettings` from `dash-config.xlsx` the first time it was
  round-tripped). The workbook is now edited through its own XML, one zip
  entry at a time, when a change must not touch anything else in the
  file.
- pandas 3.x dropped positional fallback when a `Series` is indexed with
  an integer; a frame that has been filtered keeps its original row
  labels, so `series[0]` can raise `KeyError: 0`. Use `.values[0]` or
  `.iloc[0]`.
- Dash 4.x removed `run_server` outright (not merely deprecated); the
  method is `run`.
- `pkill -f dash-lineplot.py` from a shell that is itself running the
  command matches its own process too.

## 4. Standing Constraints

Guidance: decisions marked "do not silently revisit", one line each on
why.

- **The tool knows nothing about any caller's project layout, and that is
  deliberate.** It takes a data directory as `--datadir` and infers
  nothing about data types, sample rates, or time bases from any caller's
  conventions. Resist teaching it about a specific project's telemetry
  fields; `tools/config_from_run.py` plus a hand-edited config is the
  bridge, not code in the tool itself. (`dash-3dof.xlsx` is the one
  deliberate, contained exception -- a ready-made config, not a code
  change.)
- **Never merge or resample tables, ever.** Signals recorded at different
  rates are drawn at their own rates on the same axis. A zero-order hold
  is a property of whatever process caused it and must never be assumed
  by this tool.
- **Cross-platform.** Built and run on both Ubuntu and Windows. No
  hard-coded paths, no drive letters, no user home directories. Prefer
  `pathlib.Path` over hand-built `os.path` joins going forward (see
  `suggestedwork.md` section 5) -- most of the file predates that
  discipline and still uses `os.path`.
- **`environment.yml` pins version floors, never build strings, never a
  `prefix:`.** The 2022 file this replaced was Windows-only for exactly
  those reasons.
- **Never commit to `master`.** Work happens on a feature branch
  (currently `feature/modernise-and-json`); merging is the user's
  decision.
- **`archive-no-commit/` must always be committed, despite its name.** The
  `no-commit` in the folder name is required by the handoff-management
  skill's own naming convention -- it is not an instruction to exclude the
  folder from commits in this repository. This repository is deployed by
  cloning to several PCs, so `handoff.md`, `handoff-history/`, and
  `prompt.md` under this folder must travel with every clone like any other
  tracked file. Stage and commit changes here exactly as any other change;
  do not treat the directory name as a reason to leave it out. (A prior
  session got this wrong and left `prompt.md` uncommitted -- see history.)

## 5. Current Backlog

Guidance: prioritized, currently open items only.

The detailed, line-referenced version of this list is `suggestedwork.md`
in the repository root, with a recommended eight-work-package order
(WP1 deletions, WP2 cell/dispatch defects, WP3 asset and start-up fixes,
WP4 config validation, WP5 structure, WP6 tests/tooling, WP7 performance,
WP8 documentation). **The summary below is frozen at the 2026-09-11
first-pass review and has not been kept in step with `suggestedwork.md`
since** -- items 1 through 6 in particular are substantially addressed by
now (data-reader rewrite, cell helpers, callback-registration fix, dead
code deletions across several sessions); `suggestedwork.md` itself is the
one that has been kept current, session by session. Treat this list as a
pointer to read `suggestedwork.md`, not as the current state itself. Most
severe first, as originally written:

1. **Crash-level defects in the data reader** (`readdatafile`): the
   MATLAB and comma-separated branches are two independent `if`s rather
   than one dispatch, so a header containing both a `%` and a comma runs
   both and silently discards the first result; `dfData` can be returned
   unbound for an unrecognised extension; `skiprows` can reach -1 for a
   `.plt` file with no `%` header.
2. **File-extension dispatch is case-sensitive and substring-based**
   (`.CSV`/`.XLSX` fall through to the wrong reader; any extension
   containing `mat` matches the MATLAB branch).
3. **`np.isnan` called on configuration cells that may hold text** at six
   sites -- one typo in a spreadsheet cell raises an unhelpful numpy
   `TypeError` and takes the whole page down.
4. **Callbacks registered against components that never exist**, because
   `setupCallbacks` iterates sheet names and pre-`Include`-filter tab
   lists rather than the graph ids actually placed on the page; hidden
   only because `suppress_callback_exceptions` is set.
5. **Eleven module-level `global` statements** carry per-instance state
   (`divSets`, `dfPlotterConfig`, `dashApp`, and others) into module
   scope, so two `DashLinePlot` instances in one process overwrite each
   other -- which the module's own docstring advertises as a supported
   use.
6. **Dead code**: the slider callbacks and their six component ids (none
   of which exist in the layout), the `visdcc`-era JS-injection template,
   `allTabUsedIdx`, and the unused `reqStart`/`reqEnd` parameters.
7. **No tests, no `pyproject.toml`, no linter configuration.** This is
   what makes every structural change above riskier than it needs to be.
8. ~~**Repository hygiene**: `dash-lineplot.spec` and the `.bat` launchers
   describe a Qt build that no longer exists; the 122 MB vendored
   `pyInstaller/` tree should be deleted alongside it.~~ **Done** this
   session: `pyInstaller/`, `dash-lineplot.spec`, `runPyInstaller.bat`,
   `startPlotTool.bat`, `pythonSetup/` (redundant with
   `docs/userguide.md`'s own Installation section) and
   `exmple-dash-config.xlsx` (pointed outside this repository) are all
   deleted. `README.md` updated to match.
9. **Stale documentation**: `doc/*.tex` documents the removed slider and
   removed Qt/visdcc dependencies -- every chapter now carries a
   "historical, see `docs/userguide.md`" notice rather than being fixed
   outright; **the user has said they will remove this tree themselves**,
   so leave it alone. The module docstring's 2019-era Dash tutorial
   transcript and its `DashPlotWindow` mistake are both fixed, this
   session and the one before it.

**Left undone, deliberately, not because it is forgotten:**

- Synchronised cross-subplot hover was lost with `visdcc` and reimplemented
  page-wide instead, in `graphsync.js`. Reimplementing anything closer to
  the original subplot-scoped behaviour is a separate decision, worth
  taking only if it turns out to be missed.
- The Matlab reader (`scipy.io.loadmat`) is unexercised by any repository
  data. `scipy` stays in the environment for it regardless.
- HTML copies of every graph are written to `./graphs/` on every run
  whenever a sheet sets its disk-export flag; `suggestedwork.md` section
  4.4 recommends defaulting that off.

## 6. How to Cold-Restart

Guidance: the minimum steps a fresh session needs to resume work
correctly.

1. Read this file and the current (highest-numbered) file under
   `handoff-history/` -- never an older, closed one.
2. `git branch -vv` and `git log --oneline -10` for the actual repository
   state; do not trust a branch name or commit hash quoted in prose here
   without checking.
3. Activate the conda environment: `conda activate dashplot`, or invoke it
   by path if conda is not on `PATH` -- see section 7.
4. `docs/userguide.md` is the maintained reference for how the tool
   behaves today; do not restate its content here.
5. `suggestedwork.md` is the maintained reference for what is wrong and
   what to do about it; work through it in the work-package order it
   gives, starting with WP1 (pure deletions, no behaviour change).
6. If work on this tool is being done from a caller project (as it was
   originally, from `systemCHandbook/CB_3dof`), this tool is reached by
   relative path only (`../dash-lineplot` from that project's own root, or
   whatever sibling relationship applies) and never learns that caller's
   layout -- see section 4.

## 7. Technical Reference

Guidance: config format, key function signatures, dependencies.

**Environment**, as most recently solved by conda-forge (2026-09-10):
Python 3.14.7, Dash 4.4.1, Plotly 7.0.0, pandas 3.0.5, numpy 2.5.3,
openpyxl 3.1.5, scipy 1.18.0. `environment.yml` pins floors matching these
levels of dash/pandas/numpy specifically, since those three broke
something on the jump from the 2022 baseline (`run_server` removed,
`Series[int]` positional fallback removed) and are worth not regressing
past silently.

conda itself lives at `~/miniforge3`, installed in batch mode (no
`conda init`, no shell profile modified). Invoke by path
(`~/miniforge3/bin/conda`, `~/miniforge3/envs/dashplot/bin/python`) if not
activated. Self-contained and removable with `rm -rf ~/miniforge3` if it
is ever no longer wanted.

**Configuration schema** (see `readConfigTables` in `dash-lineplot.py`,
and `tools/xlsx_config_to_json.py` for the converter): a `header`
Variable/Value table, and any number of graph sheets/objects, each a table
of rows carrying `Variable`, `Value`, `Format`, `LineLabel`, `GraphType`,
`Scale`, `Offset`, `Colour`, `Linewidth`, `Dash`, `Mode`,
`MarkerOpacity`, `Categories`, `Datafile` (the full column list is
`CONFIG_COLUMNS` in `dash-lineplot.py`). A JSON config mirrors the
workbook one for one, using the same field names.

**Entry point**:

```bash
python dash-lineplot.py --configfile <path> [--port 8050] [--datadir DIR]
```

`--datadir` resolves any relative `Datafile` reference in the
configuration; a `#group` fragment on a JSON reference selects one named
group inside a multi-rate file.

**Generating a first-pass config for a data directory**:

```bash
python tools/config_from_run.py <directory>
python dash-lineplot.py --configfile <directory-name>.json --datadir <directory>
```

## 8. History Index

Guidance: edit the STATE sections above in place, never append a new
top-level section with a fresh number. Session narrative goes in the
current history file, not here.

- `handoff-history/handoff-history-001-2026-09-onward.md` -- current,
  actively appended. Opens with the consolidated narrative of all the
  `dash-lineplot` work that had previously been recorded inside the
  sibling `systemCHandbook` repository's own handoff and history files
  (its sessions 7 through 10, plus that repository's
  `docs/devplan/wp2-dashboard-fork.md`), carried over here verbatim in
  substance so nothing is lost by the split, then continues with whatever
  happens in this repository from here on.

**Note on the source material.** The narrative folded into history file
001 was originally written into `systemCHandbook`'s
`archive-no-commit/handoff.md`, its `archive-no-commit/handoff-history/`
files, and its `docs/devplan/wp2-dashboard-fork.md`, because the two
repositories were being developed together in one session. Splitting it
out here is additive: nothing was deleted from `systemCHandbook`, and that
project's own handoff still correctly describes WP2 as complete and still
points here for the detail. Anyone maintaining both repositories should
expect a small amount of duplication between `systemCHandbook`'s WP2
record and this file's history, and should treat *this* repository's
history as authoritative for anything that happens to `dash-lineplot`
from this point forward.
