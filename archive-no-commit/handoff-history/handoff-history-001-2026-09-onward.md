# Handoff History -- 2026-09 onward

Status: closed 2026-10-08 at session end, frozen, at 29.7 KB -- just under
the 30 KB cadence limit, which the next entry would have crossed.
Superseded by `handoff-history-002-2026-10-onward.md` -- see
`handoff.md` section 8.

The first four sessions below (labelled by the date they happened rather
than renumbered from scratch) are a consolidation of material that was
originally written into the sibling `systemCHandbook` repository's own
`archive-no-commit/handoff.md`, its `handoff-history/` files, and its
`docs/devplan/wp2-dashboard-fork.md`, because at the time the two
repositories were being developed together in one session. It is carried
over here in substance, condensed rather than trimmed, so a cold start in
this repository does not depend on that project's handoff at all. Sessions
from 2026-09-14 onward are native to this file.

## Decision, 2026-09-09

The dashboard for a colleague project (`systemCHandbook/CB_3dof`, a 3-DOF
missile guidance simulation) needed a way to plot its telemetry
interactively. The decision taken: modernise this existing fork rather
than build a new tool. It already existed at `NelisW/dash-lineplot`
(forked from `rianawillers/dash-lineplot`, last pushed 2026-04-21) and was
cloned as a sibling of that other project's repository, reached by
relative path. Chosen scope: drop the Qt desktop shell entirely and serve
to the browser only, plus a text (JSON) configuration format alongside
the existing Excel workbook.

The tool's own data model turned out to fit almost exactly: `self.datafiles`
was already a dictionary of filename to `DataFrame`, and each plot names
its own data file, so multiple telemetry files at multiple independent
sample rates could stay independent with no merging and no resampling.
The blocking dependency forcing the work was PySide2, which has no Python
3.14 support -- not Dash, which merely needed catching up.

A development plan for the modernisation was written as WP2 of that other
project's six-work-package plan
(`docs/devplan/wp2-dashboard-fork.md` there), eight tasks with checkboxes
and verification gates, written for a developer working through it by
hand.

## Session, 2026-09-10 -- WP2 executed: browser-only, pandas/numpy 2.x, JSON reader

Executed end to end, unattended. Five commits on `feature/modernise-and-json`:
`b5bfdbf` environment, `d614b7e` modernisation, `8d94f07` generated-output
cleanup, `bcef290` JSON configuration, `6acd9d4` documentation.

**conda had to be installed first.** Neither conda nor pip was present on
the machine. Miniforge 26.7.2 went into `~/miniforge3` in batch mode
(no `conda init`, no shell profile touched); invoked by path.

**The environment solved further ahead than the plan assumed, and two of
the differences were real work.** Dash 4.4.1 has removed `run_server`
outright, not merely deprecated it -- the method is now `run`. pandas 3.0.5
no longer falls back to positional lookup when a `Series` is indexed with
an integer, so `dft[...]['Scale'][0]` raised `KeyError: 0` on a frame that
had been filtered and therefore kept its original row labels; fixed with
`.values[0]`, the idiom already present two lines above in the same
function. The plan's predicted pandas 2.x breakages (`DataFrame.append`,
`iteritems`, `sheetname=`) did not appear at all. numpy 2.5.3 and Plotly
7.0.0 needed no work. Python 3.14.7 solved on the first try; the planned
fallback to 3.13 was never needed.

**The plan named a verification target that cannot work.**
`exmple-dash-config.xlsx` (typo in the upstream filename) points its three
`Datafile` entries at `../../../test/TestPoint05/reswin/...`, a tree not
in the repository, so `loadData` fails and no page builds. `dash-config.xlsx`,
the default, references the bundled `data/` folder and is the config that
actually works. Both the plan file (in the other project) and this
repository's own README record this now.

**Two bugs found that the plan did not anticipate.** The new argparse
entry point ignored `runPlotter`'s return value and printed
"serving on ..." even when no server had started -- which is how a
missing-data-file case first presented as a mystery rather than an error.
`sys.argv.append("--disable-web-security")` appeared twice, a Chromium
flag meant for the now-removed Qt WebEngine, which was only polluting the
argv that argparse reads. Both fixed.

**Verification went beyond "it renders".** Figures were read back out of
the live page and checked against the source telemetry: gimbal pitch/yaw
angles matched recorded limits, a constant-speed signal was flat at the
expected value, and the two data files at 1 ms and 20 ms sample periods
drew at a verified 20:1 point-count ratio with no interpolation anywhere
-- the multi-rate honesty the design intended. One apparent anomaly (a
tracking-error signal spiking to over 100 deg) was chased down to being
correct: the spike occurred exactly at the run's closest-approach time and
is the line of sight swinging past the target, not a tracking failure.

**Left undone, deliberately:** synchronised cross-subplot hover, lost with
the `visdcc` dependency and worth reimplementing only if missed; the
Matlab reader, untouched and unexercised; `pyInstaller/`,
`dash-lineplot.spec` and the two `.bat` launchers, all of which package a
Qt application that no longer exists, left alone rather than half-fixed.

## Session, 2026-09-10 -- second round: page-wide hover, multi-rate JSON, enumerations, commonX

All work in this fork; the closing state from the previous session was
"telemetry renders in a browser" and this made it actually usable on that
telemetry, in several user-directed rounds. Thirteen commits ending at
`e086b32`.

**A user guide was written** (`docs/userguide.md`), following the markdown
house style, LaTeX-conversion-safe flavour, structured after a March-2020
LaTeX guide but with its variable tables rebuilt from the workbook's own
documentation sheet rather than the old guide, which described a Qt
application that no longer existed.

**Features added, all user-requested:**

- Page-wide synchronised hover, `assets/graphsync.js`, replacing what
  `visdcc` used to do and covering a whole page rather than one figure's
  subplots.
- Multi-rate JSON: a top-level object means named groups, one per sample
  rate, each its own table, selected as `file.json#group`; a top-level
  list still means one table.
- A per-`yValue` `Datafile` override, without which the multi-rate reader
  would have been theoretical -- a tab could otherwise only ever show one
  rate.
- Enumerations: text columns mapped to codes with the labels on the y axis,
  drawn as steps.
- `commonX`: every graph on a tab tied to one x range for zoom, pan, click
  and rubber-band selection.
- A compact layout, readouts beside the graph, title inside the plotting
  area.

**Four bugs surfaced in the tool, none in the caller project:**

- Lasso selection was silently dead -- Box Select sends a `range`, Lasso
  sends `lassoPoints`, and only the first was handled.
- `Height` was never applied at all: emitted as a bare `240`, invalid CSS,
  so every graph had always used Plotly's 450 px default regardless of
  configuration.
- The hover/zoom sync guard was a single page-wide boolean cleared on the
  line after it was set, while `Plotly.relayout` is asynchronous, so
  echoes arrived after the flag was already clear and one wedged graph
  disabled syncing everywhere.
- `openpyxl` silently drops workbook parts it does not model -- saving the
  shipped workbook through it removed the `printerSettings` parts. Fixed
  by editing the workbook's own XML directly, one zip entry at a time,
  which preserves everything else byte for byte.

**A mistake worth not repeating:** a `commonX` demonstration was first put
on a tab with `Include` set to `False`, which never renders at all, so the
setting appeared to do nothing. A setting on an excluded tab has no
effect -- an easy trap when a page has several tabs and only some are
switched on.

**On verification methodology:** the Dash callback interface over HTTP
proved a far better test harness than driving the browser directly -- it
exercises the real server-side logic with no rendering involved.
Browser-side behaviour (drag-zoom propagation, rubber-band selection)
needed the user's own confirmation by hand. Two lessons kept from this:
prefer the callback interface for anything server-side, and expect to
hand genuinely browser-side behaviour to the user.

`pkill -f dash-lineplot.py`, run from a shell that is itself running the
command, matches its own process too -- kill by PID instead.

## Session, 2026-09-11 -- third round: axis range entry, blocks, dash-3dof.xlsx

Seven commits ending at `31cd73d`, all pushed.

**Axis range entry, replacing the slider.** The original tool had a range
slider, commented out upstream because it depended on a tab-click to
trigger a redraw and that mechanism had stopped working. The user did not
want the widget revived, only the capability -- "if not a slider widget,
then at least the capability to enter a start x-axis and end x-axis
value" -- so it came back as typed **X range** / **Y range** boxes beside
each graph, with one Apply and one Reset serving both:

| Aspect | Behaviour |
|---|---|
| Reach of x on a `commonX` tab | every graph on the tab |
| Reach of y on a `commonX` tab | only the graph whose boxes were used |
| Blank pair | that axis left alone |
| Mouse zoom | writes the resulting range back into the boxes |
| Autoscale | blanks the pair; blank means the full range |

Apply patches the axis range into the figure already in the browser
(`Patch()`) rather than returning a new figure, so a large trace is not
re-sent to change a zoom.

**Blocks: several data files on one tab.** A graph sheet is now read as a
sequence of blocks -- a `Height` row opens one, `Datafile`/`xValue`/`xLabel`
apply to every graph below until replaced, each `Title` captures what is
in force. A sheet with one block behaves exactly as before, so no
existing sheet broke. `UseSubplots` was removed outright, along with the
subplot figure path and the commented-out slider layout it had been
tangled with -- it had been disabled and announcing itself on every run
for some time.

**`dash-3dof.xlsx`** was rebuilt as a proper viewer for the caller
project's telemetry (eight sheets, one per file, signals grouped rather
than one graph per column). It had arrived plotting nothing -- a copy of
`dash-config` with one sheet repointed at the wrong data file but still
naming the old file's column names.

**Two more bugs found:**

- Suppressing the numeric-input spinner arrows with WebKit-only CSS
  pseudo-elements looked done but did not work in every browser -- one
  browser drew its own stepper as stacked plus/minus controls the rules
  never touched. Fixed properly: the fields are plain text inputs, which
  no browser decorates, and the callback parses strings instead of
  assuming numeric input.
- A broad `git add -A` committed a LibreOffice lock file, which also
  revealed the workbook was open in LibreOffice while it was being rebuilt
  underneath the user. Untracked, and the pattern is now ignored.

**A verification-tooling limitation, recorded honestly:** the in-app
browser pane used for testing stopped rendering partway through this
stretch of work and then became unresponsive entirely, so drag-zoom and
rubber-band selection could not be driven or checked from inside the
session at all -- the user confirmed both by hand instead.

## Session, 2026-09-11 -- header-string generalisation and spectral-reader removal

Two small, user-directed changes to `readdatafile`, the space/comma-file
reader.

The header-stripping code tested three hardcoded column names
(`%Time`, `%CurrentSimTime`, `%t`) individually to remove a leading `%`.
Replaced with one generic pass that strips a leading `%` from whichever
column actually carries it, so the fix works for any column name rather
than three specific ones, and also corrects two latent bugs the old form
had: the old test only inspected the *first* column, so `%Time` in any
other position was missed and a name like `%TimeStamp` matched by
accident; and the old rename appended the corrected column at the end of
the frame instead of preserving its position.

The `.scd`/`.spc` spectral-data reading branch (wavelength/wavenumber/
transmission columns) was removed at the user's request -- unrelated to
the header fix, done as a separate, deliberate deletion in the same
commit.

Commit: `ad4bda8` on `feature/modernise-and-json`, pushed.

## Session, 2026-09-11 -- read-verified repository review

A full read-through review of the repository -- `dash-lineplot.py`, the
two `tools/` scripts, `assets/graphsync.js`, the repository layout -- for
defects, dead code, structural problems and modernisation opportunities.
No code was changed. Written up as `suggestedwork.md` in the repository
root, with a priority-summary table of 25 items and an eight-work-package
recommended order (WP1 deletions through WP8 documentation, with a tests/
tooling package deliberately sequenced early, ahead of the riskiest
structural changes).

**Explicitly flagged as read-verified only, not run-verified**: the
reviewing machine had no `pandas`, `dash`, `plotly` or `scipy` installed
and no conda environment for the project, so nothing in the review could
actually be executed. Every finding states the input that reaches it, so
each is checkable once an environment exists; building that environment
and adding the regression tests the review recommends (its WP6) is what
would turn the list from read-verified to run-verified.

Headline findings, most severe first: `readdatafile` runs its MATLAB and
comma-separated branches as two independent `if`s rather than one
dispatch, so a header carrying both a `%` and a comma silently discards
the first result; `dfData` can be returned unbound for an unrecognised
extension; `skiprows` can reach -1; extension dispatch is neither
case-folded nor exact-matched; six sites call `np.isnan` on configuration
cells that may hold text, so a single spreadsheet typo crashes the whole
page with an unhelpful numpy error; roughly half the registered Dash
callbacks target components that were never actually placed on the page,
hidden only by `suppress_callback_exceptions`; and eleven module-level
`global` statements carry per-instance state into module scope, which
makes the "use as a module" API the file's own docstring advertises unsafe
to use twice in one process.

Also flagged: the entire slider-callback block is dead code (the slider it
served was removed two sessions earlier); `dash-lineplot.spec` and its
`.bat` launchers describe a PySide2/PyQt5/visdcc build that no longer
exists; the vendored `pyInstaller/` tree is 122 MB and 3012 of the
repository's 3064 tracked files, including 1229 tracked `.pyc` files
compiled for Python 3.7; and `doc/*.tex` still documents the removed range
slider at length, with figures.

Commit: `3bc7304` on `feature/modernise-and-json`, pushed.

## Session, 2026-09-14 -- work history split into this repository's own handoff

The dash-lineplot work recorded above had been living entirely inside the
sibling `systemCHandbook` repository's own handoff, history files and
`docs/devplan/wp2-dashboard-fork.md`, because the two repositories were
being developed together in one session. At the user's request, that
material was consolidated and moved here -- this file and `handoff.md` --
plus a matching `prompt.md` capturing the original request, so work on
this tool can continue independently of that other project from now on.

Nothing was removed from `systemCHandbook`: it still correctly records WP2
as complete and points to this repository for detail. This is additive,
not a migration of record -- see the note at the end of `handoff.md`
section 8. Both new files are untracked in git as of this entry; whether
and how to commit them is the user's call. (Corrected 2026-10-07: this
entry originally said `archive-no-commit/` is excluded from version
control by convention. That is wrong -- the folder must always be
committed, despite its name; see the standing constraint in
`handoff.md` section 4.)

## Session, 2026-10-07 -- handoff brought in line with the merged state

`feature/modernise-and-json` had been squash-merged into `master` as PRs
#1 and #2 (`58e48e8`, `cd395b8`); `git diff master
feature/modernise-and-json` is empty, so the two trees are identical. The
user removed the untracked `data/ds010/` and `dlp.json` from the working
tree, leaving it clean. At the user's direction, work now continues on
`master`; the "never commit to `master`" constraint in `handoff.md`
section 4 was replaced accordingly.

`handoff.md` updated in place: status line, branch constraint, file
inventory (added `dash-config-sim.xlsx` and `README.md`, completed the
`data/` listing), and the conda note in section 7 (the `~/miniforge3`
paths are the Ubuntu machine's; the Windows location is not recorded).

## Session, 2026-10-07 -- second server no longer shares a port

User started two servers on the same data in two command windows; both
reported `127.0.0.1:8050` and the browser kept showing the first one's
page. Cause: Werkzeug sets `SO_REUSEADDR`, which on Windows allows a
second bind to a listening port. Added `freePort` (connect probe, up to
100 consecutive ports) and call it from the CLI entry point before
`runPlotter`; a moved port is announced and the printed URL uses it.
Verified with two servers started on 8120: second reported "port 8120 is
already in use, using port 8121 instead", and `netstat` showed separate
PIDs on 8120 and 8121. `docs/userguide.md` `--port` row and `README.md`
(quick start, plus a module-usage note that `runPlotter` does not probe
and `freePort` can be passed in) updated.

During the first test run the cleanup step also killed a pre-existing
listener on 8050 (PID 52656) that this session had not started -- the
user was told. Cleanup in later tests killed only the test ports.

## Session, 2026-10-07 -- free-port search hardened

User asked that the port search not assume the next port is available
but keep iterating until a verified free port is found. The first
`freePort` stopped after 100 ports and accepted any port that refused a
connect, which would also accept a port that is bound but not listening,
or reserved by Windows, and the server would then fail to bind. Now it
iterates to 65535 and requires an exclusive bind to succeed and then no
answer to a connect. An intermediate version that probed connect first
took minutes inside a reserved range (each refused loopback connect on
Windows costs the 0.5 s timeout), so the bind test now runs first.
Verified: listening x2 plus bound-not-listening at 8130..8132 -> 8133;
start inside reserved 57769..58168 -> 58169; reserved 5357 -> 5358; each
about 0.5 s. Three real servers started on 8120 came up on 8120, 8121 and
8122 as separate PIDs. Startup message now reads "port N is not free".

## Session, 2026-10-07 -- software design description

Wrote `docs/SDD.md` from a full read of `dash-lineplot.py`,
`assets/graphsync.js`, `assets/density.css` and both tools. User chose
LaTeX-conversion-safe flavour and asked for the Pandoc/Puppeteer front
matter as well (the house rule says that flavour normally carries none;
the user's choice was followed). ASCII and CR check: 0 and 0.

While writing it, one inconsistency surfaced and is recorded in the SDD's
known limitations as a TODO: `makeGraphSet` treats a sheet with *no*
`ToDisk` row as export-on, while a blank `ToDisk` cell means export-off.

Also brought `docs/userguide.md` (`--port` row) and `README.md` in line
with the hardened port search: "not free" now covers reserved ports and
ports that are taken but not serving, not only a running server.

## Session, 2026-10-07 -- ToDisk defaults to off

User confirmed that a sheet with no `ToDisk` row should not export.
`makeGraphSet` now treats a missing row as off, matching a blank cell.
This closed `suggestedwork.md` item 2.4 (moved to `closed-history.md` as
pass 5; 2.5 keeps its number so older references stay valid; the
priority table was renumbered). `.gitignore` comment corrected from
`GraphToDisk` to `ToDisk`. `docs/userguide.md`, `docs/SDD.md` and
`handoff.md` section 5 updated. Verified with scratch-directory variants:
no row / blank / False -> 0 files, True -> 6.

## Session, 2026-10-07 -- port check moved into runPlotter; backlog citations

`suggestedwork.md`: all 20 stale `dash-lineplot.py` line citations
refreshed, then refreshed again after this session's `runPlotter` change
(49 cited lines checked by printing each one). Item 1.1 now says seven
`global` statements (it said six; the table under it always listed
seven), reworded so it no longer implies 11 - 5 = 7.

History entry of 2026-09-14 corrected in place, with a dated note: it had
said `archive-no-commit/` is excluded from version control by convention.

`freePort` was only called from the CLI, so a program calling
`runPlotter` directly could still share a busy port. `runPlotter` now
calls `freePort(int(port))` just before starting the server thread
(accepting the string port the README example passes), stores the result
in `self.port`, and prints the notice; the CLI no longer calls `freePort`
itself and prints its URL from `dashlineplotter.port`. Verified: module
use with 8150 held by another socket and port given as `'8150'` ->
notice, `p.port == 8151`, HTTP 200 on 8151; three CLI servers on 8120 ->
8120, 8121, 8122 as separate PIDs. README module note, `docs/SDD.md`
(sequence, component table, port selection, state, code map) and
`handoff.md` section 3 updated.

## Session, 2026-10-07 -- click-history backlog item

Added `suggestedwork.md` item 3.5 (priority row 13): the Click Data
history lives in the `DashLinePlot` instance (`self.clickedData`,
`self.clickedX`), so every browser viewing one server shares it. Marked
as found by reading the source, not yet reproduced live. Proposed fix: a
`dcc.Store` per graph, folding in the 3.4 click-history shape cleanup.

## Session, 2026-10-08 -- handoff refreshed for a cold restart

User had committed all 2026-10-07 work (`360cf0f`, `eeca2c7`,
`ef0bdf0`); working tree clean, `master` one commit ahead of
`origin/master` (unpushed) at the time of this entry. `handoff.md`
updated in place: status line; file inventory (`icons/logoSet2long.png`,
which an earlier reply this session wrongly called an empty untracked
folder; `archive-no-commit/prompt.md`; `graphs/`); section 2 gained the
port and `ToDisk` behaviour; section 3 reflowed; section 4's
`prompt.md` note moved back under the `archive-no-commit/` bullet it
belongs to (an earlier edit had left it under the no-commit bullet);
section 5's one-line backlog summary refreshed; section 6 now points at
`docs/SDD.md` and gains a verification step with the test-port lesson;
section 7 records the Windows `dashplot` environment path and versions
(numpy 2.4.4 is below the `environment.yml` floor of 2.5).

## Session, 2026-10-08 -- hardcopy output

User asked for a hardcopy of one tab's graphs: PNG at 300 dpi, a
keystroke trigger, a user-chosen file name, graphs only (no tab names),
several pages per tab, a per-tab graphs-per-page setting in the config,
the text-entry boxes hidden on graphs of `Height` 200 or less, and a demo.
Brainstormed, then a spec and a plan were written and approved
(`docs/superpowers/specs/2026-10-08-hardcopy-design.md`,
`docs/superpowers/plans/2026-10-08-hardcopy.md`), then implemented in
this session task by task, test first. Nothing committed.

Decisions taken with the user: browser-side rendering
(`Plotly.toImage` + canvas + File System Access API) rather than kaleido
on the server; Chrome/Edge only; A4 portrait; one dialog with numbered
files, which forced a folder picker plus an in-page name box (a Save-As
handle cannot write sibling files); with no `HardcopyGraphsPerPage` row,
graphs keep their on-screen heights (changed from an earlier "scale to
page width with aspect kept", which would print 150 px graphs a few
millimetres tall); tests kept in a new `tests/` folder (pytest + node).

Implemented: `BOXES_MIN_HEIGHT`, `hardcopyPerPage`, `self.boxedGraphs`,
the `graph-tab` wrapper in `makeGraphSet`; `setupCallbacks` registers
callbacks only where their components exist (x groups filtered to boxed
graphs); `assets/hardcopy.js`; `hardcopy-example.json`,
`data/hardcopy-demo.csv`, `tools/make_hardcopy_demo_data.py`;
`tests/` (9 pytest, 6 node). Docs: userguide (Hardcopy section, `Height`
and `HardcopyGraphsPerPage` rows, page layout), SDD (component table,
page rows, callbacks, browser side, new Tests section, code map),
README paragraph, `suggestedwork.md` line citations refreshed and its
section 4 opening corrected (tests now exist, for this work only).

Verified: all tests pass; in the built-in browser with a stand-in folder
object, `many` -> 3 pages, `mixed` -> 2, `boundary` -> `b.png`, all
2480 x 3508 with `pHYs` 11811/11811/1 and valid CRCs (`tests/pngcheck.py`);
pages inspected as images (graphs only, zoom kept); declined overwrite,
Cancel, Escape, cancelled folder dialog, invalid name and a second
keypress all write nothing. Shipped configs: `dash-config.xlsx`,
`dash-config-sim.xlsx`, `dash-config.json`, `commonx-example.json` load
and their Apply/Reset/click/select readouts work; `gimbal` in
`dash-config.xlsx` is now full-width without boxes. `dash-3dof.xlsx`
could not be started: its data lives in the sibling `systemCHandbook`
repository, absent on this machine. Not verified: the real native folder
dialog, which only the user can drive -- left for the user.

Noticed, not changed: `dash-config.json` has `Include` false on
`xyPlot`, `Attitude` and `gimbal`, which `dash-config.xlsx` includes,
although section 1 says the two should behave identically. On a
`commonX` tab, graphs drawn with markers autorange x with padding
(-1..21) while line-only graphs autorange to 0..20, so the tab is not
x-aligned until the first zoom.

Addendum, same session: a fresh whole-change review found nothing
critical. Fixed after it, test first: Escape now closes the box after a
failure (focus moved to Cancel); pages of an earlier, longer hardcopy of
the same name are named in the closing message, never deleted
(`findLeftovers`, a 7th node test); the `suggestedwork.md` section 1.1
`function:line` table refreshed (my first pass had missed that format).
Deferred minors: a 3 px white seam between equal slots, an unreachable
non-numeric-height fallback, the stale layout comment in
`assets/density.css`. Open question for the user: on a mixed `commonX`
tab the full-width short graphs no longer line up in x with the boxed
ones on screen (the printed pages do).

Follow-up, same session: at the user's request, short graphs on a
`commonX` tab that also has boxed graphs now keep the `nine columns`
width with an empty `three columns` spacer, so the shared x axis lines up
on screen (measured at 1400 px: all six `mixed` plot areas span the same
68-1001 px); elsewhere they stay full width. New `hasBoxColumn` helper,
two tests (11 pytest now). Spec R1, userguide, SDD (page rows, code map),
`density.css` comment, `suggestedwork.md` citations (remapped from HEAD
by diff and verified against HEAD's source lines) updated. The user also
asked for the folder dialog to open in the working directory: not
possible with the File System Access API (`startIn` takes only a handle
or one of desktop/documents/downloads/music/pictures/videos, per MDN),
so alternatives were put to the user.

Second follow-up, same session (after the user's commit `8d89405`):
the user chose "save straight into the working directory, folder dialog
optional". `setupHardcopyRoutes` adds `GET /_hardcopy/folder`,
`HEAD|GET /_hardcopy/files/<name>` and `PUT /_hardcopy/files/<name>` to
the Flask server (names checked by `HARDCOPY_NAME`, PNG signature,
`image/png` only); `serverFolder` in `hardcopy.js` presents them as a
folder handle, so the writer is unchanged. The box gained a target line
and a Choose folder button (disabled where the dialog does not exist).
Tests: `tests/test_hardcopy_routes.py` (4) and a `serverFolder` node test
-> 15 pytest, 8 node. Browser checks with the server started from an
empty scratch directory: Save wrote `many-p1..3.png` there (pngcheck
good), overwrite prompt, leftovers note, Choose folder via a stand-in,
and Save with no folder dialog available all behaved; from
`http://localhost:8120` a cross-origin `PUT` never left the browser
(only its OPTIONS preflight reached the server) and a `POST` got 405.
Spec R3 amended, userguide, SDD (Hardcopy routes subsection, regenerated
code map), README, `suggestedwork.md` citations (remapped from
`ef0bdf0`, verified) updated. Noticed: the user had staged the deletion
of `dash-3dof.xlsx`; left alone.

At the user's request, `dash-3dof.xlsx` references removed from
`handoff.md` (inventory row, section 4 aside, section 6 verification
list) and from the spec's verification list; history files,
`closed-history.md`, the executed plan and `prompt.md` left as records.
The userguide's Blocks example was then rewritten with neutral names
(`run/actuator.json`, `run/sensor.json`) in place of the `CB_3dof`
telemetry paths; the multi-rate example stays, as it describes the
bundled `data/example-multirate.json`.
