# Handoff History -- 2026-10 onward

Status: current, actively appended. Will be closed and superseded by 003
once it crosses 30 KB -- see `handoff.md` section 8 for the index.

History file 001 holds everything up to and including the hardcopy work
of 2026-10-08 (decisions, review findings, fixes, browser checks). Read it
only for the reasoning behind something; `handoff.md` is self-sufficient
for a cold restart.

## Session, 2026-10-08 -- close-out and cold-restart refresh

State at close: `master` at `8313ec9` ("hardcopy to cwd or ask user"),
in step with `origin/master`. Uncommitted at the time of writing, all
documentation: `handoff.md`, both history files, the hardcopy spec (its
`dash-3dof.xlsx` mention removed) and the `docs/userguide.md` Blocks
example (neutral names in place of `CB_3dof` paths).

`handoff.md` refreshed in place for a cold restart: status line rewritten
without session provenance; inventory gained the test breakdown (15
pytest, 8 node), the spec/plan split (spec maintained, plan a record),
`data/hardcopy-demo.csv` and the git-ignored `.superpowers/` scratch;
section 3's hardcopy bullets untangled (two had been spliced together by
an earlier edit); section 5 gained a list of findings from the hardcopy
work not yet triaged into `suggestedwork.md`; section 6 gained the
browser-testing notes (scratch working directory, wide viewport,
screenshot workaround, stand-in folder picker); section 7 gained the
`HardcopyGraphsPerPage` variable, the `/_hardcopy` routes, and the
Windows tool notes (pytest, node v24). History 001 closed at session
end at 29.7 KB, since the next entry would have crossed the 30 KB
limit, and this file opened.

## Session, 2026-10-08 -- backlog triage

The handoff's untriaged list from the hardcopy work was moved, with the
user's agreement, into `suggestedwork.md` as items 3.6 to 3.11 (priority
rows 14 to 19), and the list deleted from `handoff.md` section 5.
Scoping 3.6 by converting `dash-config.xlsx` afresh and comparing showed
more drift than the `Include` flags: the JSON also still has `UseSubplots`
where the workbook has `commonX` (true on three tabs), and one extra
`UseSubplots` row. That led to a new item, 3.7: `UseSubplots` is read by
nothing yet survives in every shipped config, including
`hardcopy-example.json`, and `tools/config_from_run.py` still emits it.
Item 3.9's list of selection callbacks without a box was re-checked
against both the current code and `ef0bdf0`: identical. The three
accepted hardcopy edge cases went to `closed-history.md` as pass 6, and
`handoff.md` section 5 points there.

## Session, 2026-10-08 -- `dash-config.json` regenerated (item 3.6 closed)

At the user's request, `dash-config.json` regenerated from
`dash-config.xlsx` with `tools/xlsx_config_to_json.py`. Diff exactly the
expected rows (`UseSubplots` -> `commonX`, three `Include` false -> true,
`commonX` true on three tabs, the extra row gone). Pages built from both
formats compared identical (tabs, graph ids, `commonX` groups, boxed
graphs, serialised page and figures); the JSON page served from a
scratch directory loaded all six tabs; tests 15 + 8 pass. Item 3.6 moved
to `closed-history.md` pass 6; priority table renumbered (rows 14-18 now
3.7-3.11).

Recounting for 3.7 corrected it: `dash-config.xlsx` has no graph-sheet
`UseSubplots` row -- both of its occurrences, and two of
`dash-config-sim.xlsx`'s three, are on the `documentation` sheet (row 53
still describes it as live, row 82 says removed); the converter reads
only graph sheets, so the regenerated JSON has none. 3.9's counts updated:
`dash-config.json` now has the workbook's three box-less selection
callbacks, and the `ef0bdf0` code registers the same three for it.
`handoff.md`'s inventory row for `dash-config.json` now says to
regenerate rather than hand-edit.

## Session, 2026-10-08 -- per-trace x column, multi-source demo

The user asked whether one graph can plot the same variable from several
files: yes, already, through the per-row `Datafile` override, with each
trace's x read from its own file -- but only if every file names its time
column the same. Asked to lift that, the bounded design was approved
(x scale/offset stay per block, at the user's choice): a new optional
`xValue` column on `yValue` rows, in `CONFIG_COLUMNS`, read with
`cellText(row['xValue'], ctx['xvalue'])` in `makeGraphSet`; the existing
missing-column error now names whichever column was asked for.

Test first: `tests/test_multisource.py` (per-trace column used, missing
column reported, blank falls back to the block, demo builds) -- 3 RED for
the missing feature, the fallback test green throughout as a guard; all
19 pytest + 8 node green after. New demo: `multisource-example.json` and
`tools/make_multisource_demo_data.py` writing `data/multisource-a.json`
(`t`, 0.1 s), `-b.json` (`time`, 0.25 s from 0.05 s), `-c.csv`
(`CurrentSimTime`, 0.5 s). Checked: an `.xlsx` form of the demo builds
identical traces and the converter keeps the `xValue` cells; in the
browser the two graphs carry 201/81/41-point traces on their own grids,
and a `commonX` click at 0.55 s reports each source's own nearest
sample. Docs: userguide (new "Several data sources on one graph"
subsection, line-attribute and sheet-variable rows), SDD (traces,
`CONFIG_COLUMNS`, tests table, tools, code map regenerated), README demo
paragraph, `suggestedwork.md` citations remapped (by number against
`8313ec9`, each cited line's text checked unchanged).

Found on the way, added as `suggestedwork.md` 3.12 (Medium): a blank
`PageBottom` header cell (workbook blank, or JSON `null`) crashes the
page build with a `TypeError`; `""`, a missing row and a blank `PageTop`
are fine.

## Session, 2026-10-08 -- blank `PageBottom` fixed (item 3.12 closed)

At the user's request. Two tests first, in `tests/test_layout.py`: a JSON
header with `"PageBottom": null`, and a workbook with a blank
`PageBottom` cell; both failed with the `TypeError`. Fix in
`makeGraphSet`: the cell is read through `cellText`, so a blank gives
the date alone (non-blank text is now trimmed at its ends; harmless for
the markdown footer). 21 pytest + 8 node pass. `suggestedwork.md` 3.12
and its table row removed, write-up in `closed-history.md` pass 6; SDD
code map regenerated and `suggestedwork.md` citations remapped (one,
the changed footer line, fixed by hand to `makeGraphSet:931,933`).

## Session, 2026-10-08 -- docs sweep and cold-restart refresh

`docs/SDD.md` brought level with the day's changes: run-time sequence
(hardcopy routes registered in `runDash`), header variables (blank
`PageBottom` gives the date alone), state (`boxedGraphs`), error
handling (hardcopy route refusals, browser-side hardcopy failures),
scope (multi-source graphs, hardcopy), dependencies (direct Flask
import, node for the JS tests), known limitations (Chromium-only folder
dialog, one x unit per graph), tests table (`test_layout.py` coverage).
`docs/userguide.md`: header table (blank `PageBottom`), and where
hardcopy pages are written, under Required folders.

`handoff.md` refreshed in place: the status now separates what is
committed (`8313ec9`) from what is not; section 3 gained the NaN-cell
rule and the converter's graph-sheets-only reading; section 5's summary
corrected ("four" follow-ups) and its citation-refresh method written
down; section 6 step 7 gained `multisource-example.json` and the advice
to run `ToDisk` configs from a scratch directory (`dash-config.*` export
`RelativePosition` and `gimbalFromxls`); the `systemCHandbook` origin
notes condensed, the detail being in history 001.

## Session, 2026-10-08 -- `commonX` start range, `LegendOpacity`

Asked for: fix the marker x padding on `commonX` tabs (item 3.8), add a
legend-transparency setting, put it in every example, update the docs.

Design taken with the user: `LegendOpacity`, 0 to 1 (alpha of the white
legend background, default 0.6 = today's look), at three levels -- header
for the page, a sheet row before the first `Title` for the tab, a row
after a graph's `Title` for that graph (position decides, the user's
choice over a `LegendOpacity` column on the `Title` row); examples at 0.3;
`commonx-example.json`'s `independent` tab demonstrates the tab (0.6) and
graph (1) levels; `tools/config_from_run.py` left unchanged.

3.8, test first (`tests/test_commonx_range.py`: 3 RED, 2 guards green):
on a `commonX` tab every figure starts on `[xmin, xmax]` of the tab with
`autorange` off (`self.commonXExtent`), the wrapper carries
`data-x-extent`, `apply_ranges`'s Reset restores the extent instead of
an autorange, and `graphsync.js` turns an Autoscale into the extent for
every graph of the group, the source included. The Reset tests drive the
real callback through Dash's `/_dash-update-component` endpoint with the
Flask test client. Browser: with the committed `graphsync.js` swapped in,
Autoscale on a marker graph left two graphs at -1.26..21.26 and four at
0..20 (RED); with the new one, start, Autoscale on a marker and on a
lines graph, Reset axes and box Reset all give 0..20 on all six.

`LegendOpacity`, test first (`tests/test_legend.py`, 9 RED, the default
test green as a guard): `legendOpacityValue`,
`resolveLegendOpacities(dft, pageOpacity, sheetName)`,
`self.legendOpacity` from the header in `loadConfig` (warning like
`Density`), `LEGEND_OPACITY_DEFAULT = 0.6`. Examples: the three JSON
examples via a load/dump that round-trips byte-identically (each file's
line endings kept); both workbooks through their XML (header row 7,
`documentation` rows 86-89: a "Changed 2026-10-08" block for
`LegendOpacity`, `HardcopyGraphsPerPage` and the `xValue` column; only
those two zip entries changed); `dash-config.json` regenerated. Browser:
legend SVG fill-opacity 0.3 on `linked`, 0.6/1/0.6 on `independent`; the
workbook page shows 0.3 on all six tabs and both gimbal `commonX` tabs
start at exactly 0..7.2. 36 pytest + 8 node pass.

Docs: userguide (commonX start range, header and sheet `LegendOpacity`
rows, new "Legend background" subsection), SDD (figures, page rows,
callbacks, browser side, header variables, state, tests table, code map
regenerated with the new helpers), README (`commonx-example` paragraph),
`graphsync.js` header comment; `suggestedwork.md` 3.8 removed (table
renumbered 15-17), write-up in `closed-history.md` pass 6, citations
remapped from the post-`PageBottom` file (54, none unmappable).
`handoff.md` updated in place (status, inventory, design, section 3,
section 5 summary, test counts, schema).

## Session, 2026-10-08 -- `LegendOrientation`, `LegendX`, `LegendY`

Asked for: legend orientation and position settings, with the same three
levels as `LegendOpacity`. Design approved with the user: `v`/`h`
orientation; `LegendX`/`LegendY` limited to 0..1 so the legend stays
inside the plot (outside, Plotly widens that graph's margin and stacked
graphs lose x alignment); Plotly `auto` anchors, which reproduce today's
top-right look at the default (1, 1); a demo in `multisource-example.json`
only (page `h` at 0, 0; tab `LegendX` 0.5; second graph `v` at `LegendX`
1).

Test first (`tests/test_legend.py`, 11 RED; the 5 opacity tests green
throughout). `resolveLegendOpacities` became `resolveLegendSettings`,
resolving each of the four settings on its own; `LEGEND_DEFAULTS` and
`LEGEND_CHECKS` (checker plus wording for the warning) replace
`LEGEND_OPACITY_DEFAULT`; new `legendOrientationValue` and
`legendPositionValue`; `self.legend` (a dict) replaces
`self.legendOpacity`, and one existing test was moved to it; the legend
dict now carries `x`, `y`, `orientation` and `auto` anchors. 42 pytest +
8 node pass.

Browser, at 1400 px: demo graph 1 legend horizontal, centred (249 px
from each side), against the bottom; graph 2 vertical in the bottom-right
corner; both plot areas still 68-1012 px. Default pages
(`hardcopy-example.json` `mixed`) still show the legend flush in the
top-right corner. Workbooks: three more rows (90-92) in each
`documentation` change log, through the XML, only that entry changed;
`dash-config.json` still matches its workbook.

Docs: userguide "Legend background" became "Legend" (settings table,
anchoring, levels, both demos) plus table rows; SDD (figures paragraph,
header variables, state, tests table, code map regenerated); README
`multisource-example` paragraph; `handoff.md` in place. `suggestedwork.md`
citations remapped by pairing each with its `ef0bdf0` original (33
groups, 54 numbers), the one changed footer line located by content.

## Session, 2026-10-08 -- `LegendOpacity` renamed `LegendTransparency`

The user reported the legend setting as reversed: 0 must give solid
white, 1 the plot background. Checked first: the code drew
`rgba(255, 255, 255, LegendOpacity)`, so 0 was see-through and 1 solid
white -- exactly the meaning agreed earlier ("LegendOpacity, 0 fully
see-through, 1 solid white"), but the opposite of what the user wants.
At the user's choice the setting was renamed `LegendTransparency`, 0 solid
white, 1 fully see-through, default 0.4 (today's look, alpha 0.6), and
the examples converted so they look exactly as before: header 0.3 -> 0.7,
`commonx-example.json`'s tab 0.6 -> 0.4 and graph 1 -> 0.

Test first: `tests/test_legend.py` rewritten in transparency terms plus a
new `test_zero_is_solid_white_and_one_shows_the_plot`; 9 RED against the
old code (the example-look tests stayed green, as they assert the drawn
alpha). Code: `legendOpacityValue` -> `legendTransparencyValue`,
`LEGEND_DEFAULTS`/`LEGEND_CHECKS` keys renamed, `bgcolor` alpha
`1 - LegendTransparency`. Examples: three JSON files (look-preserving
values, line endings kept); both workbooks through their XML (header row
7 renamed and 0.7; `documentation` row 87 rewritten for the new meaning,
row 90's "Same three levels as" reference renamed; only `sheet1.xml` and
the `documentation` sheet changed); `dash-config.json` regenerated. 43
pytest + 8 node pass; in the browser the `commonx-example` legends still
draw at 0.3 (`linked`) and 0.6/1/0.6 (`independent`). Docs: userguide,
README, SDD (with code map), `handoff.md` (including a section 3 note so
the meaning is not flipped back).

## Session, 2026-10-08 -- SDD and user guide brought to current status

At the user's request, history, legacy and stale text removed from
docs/SDD.md and docs/userguide.md. User guide: the opening no longer
points at the 2020 LaTeX guide; the "Features not currently available"
section (slider, subplots, visdcc, Qt executable, Matlab) and the
range-slider comparison removed; the stale claim that plain CSV files
need a % header line (and raise AttributeError) replaced by the actual
rule (first line, or the first % comment line), which the plain-CSV demo
files confirm; Include now false only on MissilePosition, commonX on
gimbal and gimbalFromxls; config_from_run.py described as plotting text
columns as enumerations, as its docstring says; readout boxes are beside
the graph, not below; range boxes on a commonX tab show the extent after
an autoscale; assets/ described with its scripts; wording such as
"as before" and "behaves exactly as it always did" rewritten. SDD:
dated sentence in the orientation dropped, front-matter date 2026-10-08,
"(removed)" and "as before" dropped, the context diagram gained
hardcopy.js and the hardcopy PNG output, row labelling and blocks mention
the per-row xValue and legend rows, the % header no longer called
Matlab-style. Both files ASCII, line endings unchanged.

## Session, 2026-10-08 -- handoff refreshed for a cold restart

handoff.md rewritten in place, all eight sections and their Guidance
lines kept, from 34 KB to 21 KB: history and provenance removed from the
state sections (the narrative is in history 001 and this file); the
status lists what is committed (8313ec9) and what is not, including the
untracked test files and the two user-owned working-tree items
(archive-no-commit/prompt.md modified, engagementproforma.json
untracked); section 4 gained the standing decisions taken today
(dash-config.json generated from the workbook, LegendTransparency's
meaning, legend positions inside 0..1, tests from scratch directories);
section 5 is a pointer plus a one-line summary and the citation-refresh
method; section 6 states 43 pytest + 8 node tests and the browser-pane
testing workarounds. The previous version is kept only in the
scratchpad.

## Session, 2026-10-08 -- user committed bc35d1a

The user committed all of the day's remaining work as bc35d1a (legend
settings, per-trace x column, commonX start range, PageBottom fix,
dash-config.json regeneration, documentation rewrite, handoff refresh,
the new tests); the working tree was then clean, and 43 pytest + 8 node
tests passed on it. The two workbooks shrank by about 4 KB each in the
commit: the XML edits rewrote each zip with Python's own deflate level,
while every entry other than the edited sheets was checked byte-identical
at the time, so the difference is compression only. handoff.md status
updated in place.
