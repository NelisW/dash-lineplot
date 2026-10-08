# Dash Line Plot User Guide

The Python script `dash-lineplot.py` is a general plotting utility that aids
in the visualisation of captured or recorded data. It reads a configuration
file, builds a set of Plotly graphs from the data files that configuration
names, and serves them as a set of tabbed pages through a local Flask
server. The user has full control over which graph sets are rendered on
which page.

This guide covers installation, running the utility, the data formats it
reads, the configuration that drives it, and the browser display,
including hardcopy output. How the tool is built is described in
`docs/SDD.md`.

## Installation

### Requirements

The utility needs a Python environment with Dash, Plotly, pandas, numpy and
openpyxl. Everything it uses is open source.

The environment is defined by `environment.yml` in the repository root. That
file pins version floors rather than exact builds and carries no `prefix`,
so the same file solves on both Linux and Windows.

There is no packaged executable and no desktop-window build. The pages are
served to whichever browser the machine already has.

### Creating the environment

```bash
conda env create -f environment.yml
```

```bash
conda activate dashplot
```

To update the environment after `environment.yml` changes:

```bash
conda env update -f environment.yml --prune
```

To remove it entirely:

```bash
conda env remove --name dashplot
```

To re-export `environment.yml` after changing what the environment has
installed, use `--no-builds --from-history`:

```bash
conda env export --no-builds --from-history -n dashplot
```

A plain `conda env export` writes platform-specific build strings and an
absolute `prefix` naming your own home directory, which would make the
file unusable on any machine but the one that produced it.

### Running without conda init

A conda installation only puts `conda` and its environments on the shell
`PATH` if `conda init` has been run, which edits the shell start-up file. On
a machine where that has deliberately not been done, the environment is
still perfectly usable: every executable inside it can be invoked by its
full path, and doing so activates nothing and changes no shell state.

Assuming a Miniforge installation in the home directory, the environment's
own interpreter is:

```bash
~/miniforge3/envs/dashplot/bin/python
```

Use it in place of `python` in every command in this guide:

```bash
~/miniforge3/envs/dashplot/bin/python dash-lineplot.py --configfile dash-config.xlsx
```

The `conda` executable itself is reached the same way, which is enough to
create the environment in the first place:

```bash
~/miniforge3/bin/conda env create -f environment.yml
```

On Windows the equivalent paths are
`%USERPROFILE%\miniforge3\envs\dashplot\python.exe` and
`%USERPROFILE%\miniforge3\Scripts\conda.exe`.

If a shell variable is more convenient than typing the path each time:

```bash
DASHPY=~/miniforge3/envs/dashplot/bin/python
$DASHPY dash-lineplot.py --configfile dash-config.xlsx
```

Nothing in the utility depends on being run from an activated environment.
The only requirement is that the interpreter running the script is the one
that has the packages.

## Running the utility

Start the server from the directory holding `dash-lineplot.py`:

```bash
python dash-lineplot.py --configfile dash-config.xlsx
```

Then open the address the script prints, by default
`http://127.0.0.1:8050/`, in a browser. When several servers run at
once, each gets its own port, so always use the printed address. Stop the server with Ctrl+C.

The command line takes three options:

| Option | Meaning |
|---|---|
| `-f`, `--configfile` | Configuration file, `.xlsx` or `.json`. Defaults to `./dash-config.xlsx`. |
| `-p`, `--port` | Port for the local Flask server. Defaults to 8050. If that port is not free (another server is using it, or the operating system has reserved it), the ports above it are checked one by one until a free one is found, and the script says which port it used. |
| `-d`, `--datadir` | Directory against which relative data file names in the configuration are resolved. Optional. |

Working in a terminal is recommended rather than launching the script by
double-click. Warning and error messages are written to the console, and
they are the first place to look when a page does not render as expected.

The `--datadir` option exists so that a configuration never has to carry a
path into somebody else's directory tree. Name the data files in the
configuration without a directory, and supply the directory at run time:

```bash
python dash-lineplot.py --configfile run.json --datadir path/to/run-directory
```

If a data file named in the configuration cannot be found, the script
reports the file, builds no page, and exits with status 1 rather than
serving an empty portal.

### Required folders

The script expects two folders beside it, both part of the repository:

| Folder | Contents |
|---|---|
| `assets/` | The style sheets that format the page, and its scripts: `graphsync.js` (linked hover and x ranges) and `hardcopy.js` (Ctrl+Alt+H). Dash serves everything in this folder automatically. |
| `icons/` | Images used on the page. |

A `graphs/` folder is created by the script whenever it builds a page,
whether or not anything is written into it. It receives a standalone
interactive HTML file per graph set whose sheet sets `ToDisk` to `True`.
Those files can be opened directly in a browser, with full Plotly
functionality and without a running server, and are regenerated on every
run. The folder is build output and is not tracked in version control.

Hardcopy pages (see Hardcopy below) are written into the directory the
script is started from, not into `graphs/`, unless another folder is
chosen.

## Input data file formats

A single configuration may draw on several data files of different types.
The type is chosen from the file extension.

| Extension | Format |
|---|---|
| `.xlsx` | First sheet only, column names in the top row. |
| `.json` | A record array, or an object of named groups. See below. |
| anything else, such as `.csv` or `.txt` | Text with comma, tab or space separated columns. |

In a text file the column names come from the first line. Alternatively
the file may start with comment lines beginning with `%`; the first of
them then supplies the column names (`%time` and `% time` both work) and
the rest are skipped. Any other format is not supported: a file whose
extension is neither `.xlsx` nor `.json` is read as delimited text, and
fails if it is not, a Matlab `.mat` file for example.

The result is one table per file, or per group within a file, and the
configuration refers to columns of that table by name.

### JSON record arrays

The single-rate form is a list of objects. Each object is one sample, and
each of its keys becomes a column:

```json
[
  { "t": 0.000, "eps_y": 0.0279, "eps_z": -0.0551 },
  { "t": 0.020, "eps_y": 0.0274, "eps_z": -0.0547 }
]
```

Keys absent from a given object become empty cells in that row. The time
column has no privileged name; it is chosen in the configuration through
`xValue`, exactly like any other column.

### Multi-rate JSON

Data recorded at several rates goes in one file as an object of named
groups, each group holding its own record array with its own time column:

```json
{
  "gimbal_1ms": [
    { "t": 0.000, "theta_g": -0.0000 },
    { "t": 0.001, "theta_g": -0.0200 }
  ],
  "seeker_10ms": [
    { "t": 0.000, "eps_y": 0.0000, "mode": "Cueing" },
    { "t": 0.010, "eps_y": 0.0010, "mode": "Cueing" }
  ]
}
```

`data/example-multirate.json` holds exactly this, as a working example.

Which of the two shapes a file uses is declared by its own structure, not
guessed from the contents: a top-level list is one record array, a
top-level object is a set of named groups. Rates are never inferred from
timestamps.

A group is selected by appending a `#` fragment to the `Datafile` value:

```text
data/example-multirate.json#gimbal_1ms
```

Naming a group that does not exist, or omitting the fragment for a file
that has groups, is reported with the list of groups the file does contain.

Data recorded at different rates in **separate** files needs no fragment.
One file is one table.

### Enumerations

A column whose values are text, such as a mode or state name, is an
enumeration. It is plotted rather than skipped: the labels are mapped onto
integer codes, and the y axis is relabelled with the names, so the axis
reads `Cueing` and `Tracking` rather than 0 and 1. The hover readout shows
the name too. Any number of states is supported.

Enumeration lines are drawn as steps, because a state signal is piecewise
constant: it holds a value and then jumps. A sloped line between two states
would draw intermediate states that never existed.

By default the states are numbered in order of first appearance in the
data, so a mode sequence reads up the axis in the order it happened. To fix
the axis across runs, including states a particular run never reached,
declare the order with the `Categories` attribute on the `yValue` row:

```json
{ "Variable": "yValue", "Value": "mode",
  "Categories": ["Cueing", "Tracking", "Terminal"] }
```

In a spreadsheet cell, write the same list comma-separated:
`Cueing, Tracking, Terminal`. A value that occurs in the data but is
missing from the declared list is appended to the end of the axis rather
than dropped, so an unexpected state is never hidden.

`Scale` and `Offset` are ignored for an enumeration; they have no meaning
for a state name.

### One table, one time base

Each table keeps its own time column, and tables are never merged onto a
shared time base or resampled against one another. This holds between files
and between groups within a file. A signal recorded every 1 ms and one
recorded every 20 ms are drawn at their true densities, twenty to one, and
neither is interpolated to match the other. A zero-order hold belongs to
the process that causes it, not to the plotting layer, so the display never
invents samples that the recording did not contain.

## Configuration files

The configuration decides everything about the page: which files are read,
which columns are drawn, how they are labelled, and how the graphs are
grouped into tabs.

Two interchangeable formats are accepted.

| Format | When to prefer it |
|---|---|
| `.xlsx` | Editing by hand in a spreadsheet, with the documentation sheet beside the settings. |
| `.json` | Version control, generated configurations, and machines without a spreadsheet program. |

The JSON schema mirrors the workbook one for one and uses the workbook's
own column names verbatim, so the two describe the same plot in the same
words.

The shipped `dash-config.xlsx` and `dash-config.json` are the same
configuration in both formats, kept in step by the converter, and both work
against the bundled `data/` folder. The workbook's `documentation` sheet
lists the variables and their defaults beside the settings themselves. Its
`gimbal` and `gimbalFromxls` tabs have `commonX` set, so they also serve as
working examples of linked graphs.

`Include` is `False` on the shipped configuration's `MissilePosition` tab,
so that tab does not appear in the browser until it is set to `True`. A
setting on an excluded tab has no effect on the page.

### Structure

A configuration has a header and any number of graph sheets:

- The **header** carries page-level settings: the page title, the markdown
  blocks at the top and bottom of every page, an optional master data file
  name, and the page density.
- Each **graph sheet** becomes one tab. Its name supplies the tab label,
  with the leading `graph-` removed. A sheet whose name does not contain
  `graph` is ignored, which is how the `documentation` sheet in the shipped
  workbook stays out of the display.

In the workbook, each graph sheet is a table whose first column is
`Variable` and second is `Value`, with further columns carrying the
per-line attributes. In JSON, the same content is a list of row objects:

```json
{
  "header": {
    "Pagetitle": "Dash CSV File Viewer",
    "PageTop": "Markdown rendered at the top of every page.",
    "PageBottom": "Markdown rendered at the bottom of every page.",
    "Datafile": "none"
  },
  "sheets": {
    "graph-Velocity": [
      { "Variable": "Height", "Value": 300 },
      { "Variable": "Datafile", "Value": "data/tp05j2a.rgeo" },
      { "Variable": "xLabel", "Value": "Time [s]", "Format": ".3f" },
      { "Variable": "xValue", "Value": "CurrentSimTime" },
      { "Variable": "Title", "Value": "Relative speed" },
      { "Variable": "yLabel", "Value": "Velocity [m/s]", "Format": ".6f" },
      { "Variable": "yValue", "Value": "Rel-speed" },
      { "Variable": "Include", "Value": true }
    ]
  }
}
```

A row that sets no attribute beyond `Value` simply omits the other keys.

### Graph sheet variables

The `Variable` entries below are read from each graph sheet. Only the first
four and the graph set entries are required; the rest take defaults.

| Variable | Meaning |
|---|---|
| `Height` | Height of each graph in the browser, in pixels. A graph of 200 or less is drawn without the column of boxes beside it. |
| `Datafile` | Path to the data file for this tab. The keyword `master` selects the file named on the header sheet. |
| `xLabel` | Label for the x axis. |
| `xValue` | Name of the data column supplying x values. A `yValue` row may name its own in an `xValue` column; see Several data sources on one graph. |
| `Title` | Title of one graph. Starts a new graph set. |
| `yLabel` | Label for the y axis of the current graph. |
| `yValue` | Name of a data column supplying y values. Repeat it for more lines on the same graph. |
| `GraphTop` | Markdown inserted immediately above the graph. |
| `GraphBottom` | Markdown inserted immediately below the graph. |
| `Include` | `True` or `False`. Whether this tab appears at all. Defaults to `True`. |
| `ToDisk` | `True` or `False`. Whether to write a standalone HTML copy into `graphs/`. Defaults to `False`. |
| `commonX` | `True` or `False`. Tie every graph on this tab to one x scale. Defaults to `False`. |
| `HardcopyGraphsPerPage` | A positive whole number: the number of equal-height graphs on each hardcopy page of this tab. When absent, each graph keeps its own height. See Hardcopy below. |
| `LegendTransparency`, `LegendOrientation`, `LegendX`, `LegendY` | Override the header's legend settings. Before the sheet's first `Title` a row sets the whole tab; after a graph's `Title` (before the next) it sets that graph only. See Legend below. |

Any number of graphs may appear on one tab. A `Title` entry opens a new
graph, and the `yLabel` and `yValue` entries that follow it belong to that
graph until the next `Title`.

### Header variables

| Variable | Meaning |
|---|---|
| `Pagetitle` | Browser tab title. |
| `PageTop`, `PageBottom` | Markdown rendered at the top and bottom of every page. `PageBottom` is prefixed with the date of the run; left blank, it shows the date alone. |
| `Datafile` | Master data file. A graph sheet selects it with the keyword `master`. |
| `Density` | `compact` or `comfortable`. Defaults to `compact`. |
| `LegendTransparency` | A number from 0 to 1: how see-through the legend's white background is, 0 solid white, 1 fully see-through so the plot shows behind the legend. Defaults to 0.4. See Legend below. |
| `LegendOrientation` | `v` (a column, the default) or `h` (a row). See Legend below. |
| `LegendX`, `LegendY` | Numbers from 0 to 1: the legend's position inside the plot, 0 left/bottom, 1 right/top. Default 1 and 1, the top-right corner. See Legend below. |

`Density` controls how tightly the page is packed.

`compact` reduces the heading sizes, removes the vertical space between one
graph row and the next entirely, and tightens the margins Plotly reserves
around each plot so that the data area fills roughly 70 percent of the
graph rather than 40. The graph title is drawn inside the plotting area,
against its top left corner, rather than in a band of page above the graph,
so a title costs no page height at all. `comfortable` uses roomier
spacing, Plotly's default margins, and the title above the plot.

Measured on a seven-graph page with `Height` set to 240: 1940 px compact
against 4286 px comfortable.

### Legend

Each graph's legend sits inside its plot, by default in the top-right
corner, listed in a column, on a white background drawn partly
see-through so the lines behind it still show. Four settings change
that:

| Variable | Values | Default | Effect |
|---|---|---|---|
| `LegendTransparency` | 0 to 1 | 0.4 | How see-through the background is: 0 solid white, 1 fully see-through, so the plot shows behind the legend. |
| `LegendOrientation` | `v` or `h` | `v` | Entries in a column (`v`) or a row (`h`). |
| `LegendX` | 0 to 1 | 1 | Position across the plot: 0 left edge, 1 right edge. |
| `LegendY` | 0 to 1 | 1 | Position up the plot: 0 bottom edge, 1 top edge. |

The legend anchors on the side nearest its position: at `LegendX` 1 and
`LegendY` 1 its top-right corner sits in the plot's top-right corner, at
0 and 0 its bottom-left corner in the bottom-left, and at 0.5 it is
centred. Positions are limited to 0 to 1, inside the plot, because a
legend outside it makes that graph's plot narrower than its neighbours',
and stacked graphs would no longer line up in x.

Each setting can be given at three levels, each overriding the one
before, and each is resolved on its own, so a tab can, say, move the
legend down without changing its orientation:

| Where | Applies to |
|---|---|
| Header | The whole page. |
| Graph sheet, before its first `Title` | That tab. |
| Graph sheet, after a graph's `Title` and before the next | That graph only. |

On a graph sheet the row's position is what decides: a legend row placed
at the end of a sheet, where `Include` and `ToDisk` often go, belongs to
the last graph, not the tab. A value outside the ones listed above is
reported when the page is built and ignored.

The shipped examples set `LegendTransparency` 0.7 in the header, mostly
see-through. The `independent` tab of `commonx-example.json` shows its
other two levels: a tab value of 0.4 before its first graph, and 0 (solid
white) on its second graph alone. `multisource-example.json` shows the layout settings: the
header puts a horizontal legend (`h`) at 0, 0; the `summary` tab moves it
to the bottom centre (`LegendX` 0.5); and its second graph switches back
to a vertical legend at the bottom right (`LegendOrientation` `v`,
`LegendX` 1).

### Tying the graphs of a tab to one x scale

Set `commonX` to `True` on a graph sheet and every graph on that tab shares
one x range. Two things follow.

**Zoom and pan apply to all of them.** Drag-zooming, panning or autoscaling
any graph applies the same x range to every other graph on the tab, so the
whole tab always shows the same interval. If the x axis is time, the graphs
stay aligned in time whatever the reader does to one of them.

The graphs start on the tab's exact data extent, the smallest to the
largest x of every line on the tab, and Reset, Plotly's Autoscale and
Reset axes all return them there. Plotly's own autorange would not do: it
adds a margin either side of any line drawn with markers, even invisible
ones (`MarkerOpacity` 0), but not of a line drawn without, so graphs of
the two kinds would start on slightly different x ranges.

**A click reads the whole tab.** Clicking any graph fills the Click Data
box of every graph on the tab at that same x, so one click reads all of
them without hunting for the same instant on each. Each box quotes its own
graph's traces:

```text
Previous x: 8.000000
Current  x: 12.500000
Range    x: 4.500000
  eps_y = -0.000081
```

The value quoted is that graph's nearest recorded sample, never an
interpolation. Graphs on one tab may sample at different rates, so the
nearest sample to a given x differs from graph to graph, and inventing a
value between two samples would be a fiction. An enumeration reports its
state name.

**A rubber-band selection reads the whole tab too.** Selecting a region on
any graph, with either the box or the lasso tool, fills the Rectangle Tool
Selection Data box of every graph on the tab.

Only the x window travels between graphs. The graphs of a tab have their
own y scales and often their own units, so a y range selected on one of
them means nothing on another. Each graph therefore reports the extent of
its own data inside the shared x window, which is the quantity actually
worth knowing: what this signal did while that one did that.

```text
Selected x: [2.000000, 5.000000]
Width    x: 3.000000
  SLR pitch: y in [-0.023895, 0.023257]  (601 samples)
  SLR yaw: y in [-0.023712, 0.023847]  (601 samples)
```

An enumeration lists the states it visited inside the window rather than a
minimum and maximum, which would be meaningless for a state name:

```text
  mode: playback, dynamic  (3 samples)
```

A graph with no samples in the window says so rather than reporting an
empty range.

Without `commonX`, each graph zooms independently, and its two readout
boxes report only what happened on that graph, in the forms described under
measurements below.

`commonX` links the graphs of one tab. Graphs on different tabs are never
linked, since only one tab is on screen at a time. Worked examples ship
with the tool: the `gimbal` and `gimbalFromxls` tabs of `dash-config.xlsx`
(and its JSON twin), and `commonx-example.json`, which puts the same three
graphs on a linked tab and an unlinked tab for comparison.

### Blocks: several data files on one tab

A graph sheet is read top to bottom as a sequence of **blocks**. A `Height`
row opens a block, and a `Datafile`, `xValue` or `xLabel` row applies to
every graph below it until another row of the same kind replaces it. Each
`Title` starts a graph, which takes whatever settings are in force at that
point.

A sheet with one `Height` at the top is therefore a single block: its
`Datafile` and `xValue` apply to every graph on the tab.
Adding a second `Height` starts a second block, which is how one tab carries
several data files:

| Variable | Value | Effect |
|---|---|---|
| `Height` | 260 | opens the first block |
| `Datafile` | `run/actuator.json` | applies from here down |
| `xLabel` | `Time [s]` | applies from here down |
| `xValue` | `t` | applies from here down |
| `Title` | Actuator position | first graph, drawn from `actuator.json` |
| `yLabel` | Position [m] | |
| `yValue` | `position` | |
| `Height` | 260 | opens the second block |
| `Datafile` | `run/sensor.json` | replaces the first file from here down |
| `Title` | Sensor error | second graph, drawn from `sensor.json` |
| `yLabel` | Error [m] | |
| `yValue` | `error` | |

The second block inherits `xValue` and `xLabel` from the first because it
does not set them. It may set either, which matters when two files name
their time column differently: one file might call it `t`, while the
bundled `.rgeo` files call it `CurrentSimTime`.

Nothing is aligned or resampled between blocks. Each graph is drawn from its
own file at the rate that file was recorded, and `commonX` ties their x axes
together if you want them read as one.

A single `yValue` row may also name its own `Datafile` in the `Datafile`
**column**, which overrides its block for that one line. Use a block when a
whole graph comes from another file, and the column when one line does.

### Mixing sample rates on one tab

The `Datafile` on a graph sheet sets the default for that tab. A single
`yValue` row may override it, in the `Datafile` **column**, which is what
lets one tab carry signals recorded at different rates:

```json
[
  { "Variable": "Datafile", "Value": "run.json#gimbal_1ms" },
  { "Variable": "xValue", "Value": "t" },
  { "Variable": "Title", "Value": "Gimbal pitch" },
  { "Variable": "yLabel", "Value": "theta_g [rad]" },
  { "Variable": "yValue", "Value": "theta_g" },
  { "Variable": "Title", "Value": "Seeker error" },
  { "Variable": "yLabel", "Value": "eps_y [rad]" },
  { "Variable": "yValue", "Value": "eps_y",
    "Datafile": "run.json#seeker_10ms" }
]
```

Each trace resolves its x and y against its own table, using the time
column named by the sheet's `xValue`. The tables are not aligned, padded or
resampled against one another; each line is simply drawn at the rate it was
recorded.

### Several data sources on one graph

The same per-row override gives one graph a line from each of several
files, for example the same quantity from several runs or instruments.
When the files name their time column differently, a `yValue` row may
also name its own x column, in the `xValue` **column**, beside its
`Datafile` cell:

| Variable | Value | Datafile | xValue | LineLabel |
|---|---|---|---|---|
| `xValue` | `t` | | | |
| `xLabel` | `Time [s]` | | | |
| `Title` | value1 from three sources | | | |
| `yLabel` | `value1 [-]` | | | |
| `yValue` | `value1` | `data/multisource-a.json` | | A |
| `yValue` | `value1` | `data/multisource-b.json` | `time` | B |
| `yValue` | `value1` | `data/multisource-c.csv` | `CurrentSimTime` | C |

A blank `xValue` cell keeps the block's `xValue` row, here `t`. Each line
takes x and y from its own file and is drawn at that file's own samples;
nothing is interpolated or resampled. The graph keeps one x axis: the x
label, format, `Scale` and `Offset` are the block's, set on its `xLabel`
and `xValue` rows, and apply to every line alike, so all the time
columns should be in the same unit. Give each line a `LineLabel`, or the
legend repeats the column name once per file. Hover and the click and
selection readouts report each line's own recorded values.

`multisource-example.json` demonstrates this on dummy data, three files
with time columns `t`, `time` and `CurrentSimTime` on 0.1 s, 0.25 s and
0.5 s grids:

```bash
python dash-lineplot.py --configfile multisource-example.json
```

`tools/make_multisource_demo_data.py` regenerates the data files.

### Line attributes

These are set in additional columns on a `yValue` row, or on the `xLabel`
and `yLabel` rows in the case of `Format`.

| Attribute | Meaning |
|---|---|
| `LineLabel` | Legend entry for the line. Defaults to the column name. |
| `Colour` | Line colour, in any CSS or RGB form, such as `rgb(67,67,67)` or `rgba(0,100,80,0.2)`. Plotly chooses if unset. |
| `Linewidth` | Line width in points. Defaults to 2. |
| `Dash` | One of `solid`, `dash`, `longdash`, `dot`, `dashdot`, `longdashdot`. Defaults to a solid line. |
| `Mode` | `lines` or `markers+lines`. Defaults to `lines`. Markers are required for box selection. |
| `MarkerOpacity` | Marker opacity. Set it to 0 to enable box selection without cluttering the graph. |
| `GraphType` | `line` or `bar`. Defaults to `line`. |
| `Scale` | Multiplier applied to the values before plotting. Defaults to 1. |
| `Offset` | Value added before plotting. Defaults to 0. |
| `Format` | Number format for the hover text, such as `.4f`. Set on the `xLabel` and `yLabel` rows, and applies to the whole graph. |
| `Categories` | Ordered state names for an enumeration column. A comma-separated list in a spreadsheet cell, a JSON list in a JSON config. Defaults to order of first appearance. |
| `Datafile` | Data file for this line only, overriding the sheet's. This is how one tab carries several sample rates. |
| `xValue` | x column for this line only, in its own data file, overriding the block's `xValue` row. For files that name their time column differently; the x scale and offset stay the block's. |

`Scale` and `Offset` (and the `xValue` row's own `Scale`/`Offset`, which
apply to the x axis) only move where a line is *drawn*, so that signals of
very different magnitude -- microvolts and megavolts, say -- can share one
axis. **They never change a value the reader reads off.** The hover
tooltip, the Click Data box and the Rectangle Tool Selection Data box all
report the true value as it stands in the data file, regardless of any
Scale or Offset applied to the line for display. A line plotted at
`Scale=0.01` still reports its unscaled, original value when clicked or
hovered over, not the scaled plot position.

When a workbook renders incorrectly, the first thing to check is stray
content in cells below the intended range. Clearing the contents of every
cell below the last real row is a reliable precaution.

### Converting and generating configurations

An existing workbook is converted to the JSON form with:

```bash
python tools/xlsx_config_to_json.py dash-config.xlsx
```

The result is written beside the workbook with a `.json` suffix. The
conversion is faithful: the converted file produces the same page.

A configuration can also be generated from a directory of JSON data files,
which is the quickest way to see a new data set:

```bash
python tools/config_from_run.py path/to/run-directory -o run.json
```

This writes one tab per data file, or per group of a multi-rate file, and
one graph per column, with the time column on the x axis. A column of text,
such as a mode or state name, is configured as an enumeration and plotted
as steps (see Enumerations). The generated file is a starting point meant
to be edited, typically to group related signals onto shared axes.

## Using the browser display

### Page layout

Every page carries, from top to bottom: the row of tabs, the header
markdown from `PageTop`, then the `GraphTop` markdown, then one row per
graph, then the `GraphBottom` and `PageBottom` markdown.

Each graph occupies a row of its own, with the graph on the left and its
controls and readouts stacked in a narrow column on the right:

```text
+-------------------------------------------+  +-----------------+
|                                           |  | X range         |
|                  graph                    |  | Y range         |
|                                           |  | Apply   Reset   |
|                                           |  +-----------------+
|                                           |  | Click Data      |
|                                           |  +-----------------+
|                                           |  | Rectangle Tool  |
+-------------------------------------------+  +-----------------+
```

Keeping the readouts beside the graph rather than beneath it is what lets
consecutive graphs sit directly against one another. In the compact
density there is no vertical space at all between one graph row and the
next, so a page is exactly as tall as its graphs.

The height of each graph is the sheet's `Height` value, in pixels.

A graph whose `Height` is 200 or less has no range entry, Click Data or
Rectangle Tool box beside it: on a graph that short the boxes would be
taller than the plot itself. It takes the full width of the row, except
on a `commonX` tab that also has taller, boxed graphs: there it keeps
their width, with an empty column where their boxes are, so that every
graph on the tab has the same x axis length and a time reads at the same
horizontal position on all of them. Zoom, pan, hover and `commonX`
linking still work, and on a `commonX` tab a range typed beside one of
the taller graphs reaches the short ones too. The rule is applied per
block, so one tab can mix both kinds.

Select a tab to display its graphs. Graphs are drawn when the tab is first
selected rather than when the page loads, so the first selection of a tab
carrying a large data set takes a moment.

### Hover

Moving the pointer across a graph displays the values of every line in that
graph at the hovered x position, each in its line colour. The x value
itself is not repeated in the tooltip, since it is already shown on the x
axis below the graph via the vertical hover line. The numbers are formatted
according to the `Format` attribute set on the `xLabel` and `yLabel` rows.
An enumeration shows its state name.

**The readout is shared by every graph on the page.** Hovering any one
graph makes all the others display their own values at the same x position
at the same time, so a whole page of signals can be read at one instant
without clicking anything.

Each graph resolves that x position against its own samples. Graphs
recorded at different rates therefore show their own nearest sample rather
than an interpolated one, and a graph whose x range does not cover the
hovered position simply shows nothing.

### Setting the axis ranges by typing them

The column beside each graph starts with a range box: a start and an end for
**X range**, the same for **Y range**, and one **Apply** and **Reset** pair
serving both. Each field shows that graph's own first and last value as
placeholder text, so the available range is visible without guessing.

Fill in either pair, or both, and press Apply. A pair left blank is left
alone, so the y range can be set without disturbing the x range and the
other way round. Reset returns both axes to the full data range.

**The boxes follow the mouse.** Drag-zooming, panning or double-clicking a
graph writes the resulting range back into its boxes, so what they show is
always what the axis is actually set to rather than whatever was last typed.
An axis the gesture did not touch is left alone: zooming in x does not
disturb the y boxes. Autoscaling, by double-click or the toolbar, blanks the
pair, since blank means the full data range and the placeholder says what
that is. On a `commonX` tab the full x range is the tab's data extent, set
as an explicit range, so the x boxes show those numbers instead; the
graphs dragged along with a zoom update their x boxes too.

The fields are plain text boxes rather than spin boxes, so no browser draws
increment arrows beside them: a step of one is either nothing or everything
depending on the signal, and the arrows only ate width. Anything a number
can be written as is accepted, including a decimal point, a leading minus
and scientific notation such as `1.9e1`. Text that is not a number is
ignored rather than reported as an error.

**The two axes behave differently on a `commonX` tab**, and deliberately so:

| Axis | Reach |
|---|---|
| X | Every graph on the tab, so the whole tab moves to the same interval |
| Y | Only the graph whose boxes were used |

The graphs of a tab have their own y scales and often their own units, so a
y range taken from one would be meaningless on another. X is the only axis
they share. Reset follows the same rule: it returns x on the whole tab and y
on the graph whose button was pressed.

Only the axis ranges are changed. The data already in the browser is reused
rather than re-sent, which is what makes this instant even on a trace of
19000 points. A start greater than or equal to its end is ignored rather
than producing an inverted axis, and the other axis still applies.

### Zoom, pan and the Plotly toolbar

The toolbar appears at the top right of a graph when the pointer is over
it. It carries the standard Plotly controls:

| Control | Effect |
|---|---|
| Zoom | Drag a rectangle to zoom into it. |
| Pan | Drag to move the visible window. |
| Box Select, Lasso Select | Select points, feeding the selection box beside the graph. |
| Zoom in, Zoom out | Step the zoom about the centre. |
| Autoscale, Reset axes | Return to the full data range. |
| Download plot as a PNG | Save the current view as an image. |

Double-clicking inside a graph also resets the axes.

### Measurements on a graph

Two readout boxes sit beside each graph, under its range box, and both
work alongside zooming.

**Click Data.** Click any point on a line to record it. Click a second
point and the box reports both positions and the difference between them:

```text
Previous [x, y]: [1.742000, -625.599006]
Current [x, y]: [2.001000, -595.207728]
Range [x, y]: [0.259000, 30.391278]
```

Each further click replaces the older of the two recorded points, so
successive clicks always measure between the two most recent.

**Rectangle Tool Selection Data.** This box reports the extent of a
selection made with either of the two Plotly selection tools. Both are
supported: Box Select reports the rectangle drawn, and Lasso Select reports
the bounding box of the polygon drawn.

The box reports the selected x window and, for every line on the graph,
that line's own true y extent inside it -- the same format the `commonX`
section above shows for a linked tab, since a selection box's corners are a
single scaled plot position and cannot be converted back to a true value
when different lines on the same graph carry different `Scale`/`Offset`:

```text
Selected x: [2.000000, 5.000000]
Width    x: 3.000000
  Distance: y in [102.400000, 388.150000]  (301 samples)
  X: y in [-40.200000, 55.900000]  (301 samples)
```

An enumeration line lists the states it visited inside the window rather
than a minimum and maximum, which would be meaningless for a state name,
exactly as under `commonX` above.

It is easy to conclude that the tool is broken, because two conditions must
both hold before anything appears. Step by step:

1. The graph must have **markers**. Selection acts on data points, and a
   line drawn in the default `lines` mode has no points to select. Set
   `Mode` to `markers+lines` on the lines being measured. Without markers
   the box does not even appear on the page.
1. Set `MarkerOpacity` to 0 at the same time, unless the markers are wanted
   visually. Selection then works with nothing drawn. This is what the
   shipped configuration does, which is why its graphs look like plain
   lines yet are selectable.
1. Hover the graph so the Plotly toolbar appears at its top right, and
   click **Box Select** or **Lasso Select**. Until a selection tool is
   chosen, dragging pans or zooms instead of selecting.
1. Drag across the region of interest.

If the box still reads `none selected`, the selection enclosed no data
points. Selecting an empty region of the plot area is the usual cause.

On a tab with `commonX` this box behaves differently: a selection on any
graph fills every box on the tab, reporting the shared x window and each
graph's own y extent within it. See the `commonX` section above.

Markers slow rendering noticeably on large data sets, which is why they are
not the default.

### Hardcopy

Press **Ctrl+Alt+H** to write the graphs of the tab on screen to one or
more A4 portrait pages, each a 300 dpi PNG file. Only that tab is printed,
and only its graphs: the tab strip, the markdown, the boxes beside the
graphs and the logo are left out. Each graph prints as it is on screen,
including the current zoom.

1. Press Ctrl+Alt+H. A small box opens with a file name, filled in with the
   tab name. Change it if wanted; a trailing `.png` is ignored, and a name
   containing any of `< > : " / \ | ? *` is refused.
1. Press Enter or Save. The pages are written into the directory
   `dash-lineplot.py` was started from; the box shows which one. No
   dialog opens. To save somewhere else instead, press **Choose
   folder...**: the system folder dialog opens, reopening in the folder
   used last time, and the browser may also ask whether the page may save
   files there.
1. The pages are written as `name.png` for a single page, or
   `name-p1.png`, `name-p2.png`, and so on. If any of those files already
   exists, the browser asks before overwriting it. Pages of an earlier
   hardcopy under the same name that this one does not replace -- the
   higher pages of a longer run, or `name.png` beside a numbered set --
   are left in place, and the closing message names them so they are not
   mistaken for part of the new copy.

Escape or Cancel closes the box without writing anything, as does
cancelling the folder dialog.

Each page has 10 mm margins and is 2480 by 3508 pixels; the resolution is
recorded in the file, so word processors place it at its true A4 size.
Graphs take the full printable width. Their heights follow one of two
rules:

- **`HardcopyGraphsPerPage` set.** Each page is divided into that many
  equal slots, filled in order. The last page keeps the same slot height
  and leaves its unused slots blank.
- **Not set.** Each graph keeps its `Height`, at 96 pixels to the inch, so
  graphs print at the size they appear on screen and keep their relative
  heights. A graph that does not fit in what is left of a page starts the
  next one.

Text and lines print at the same physical size as on screen.

Save works in any browser: the page hands the finished pages to the
`dash-lineplot` server, which writes them. The server accepts only PNG
files with a plain file name, writes nowhere but that one directory, and
accepts them only from its own page, never from another web site.

**Choose folder...** needs Chrome or Edge, with the page opened at a
localhost address (`http://127.0.0.1:...` or `http://localhost:...`),
because it uses the browser's own file-system access, which other
browsers do not provide; elsewhere the button is greyed out. The folder
dialog cannot be made to open in the working directory: a browser lets a
page start it only in a folder used before or in one of a few fixed
places such as Documents, which is why Save goes through the server
instead.

`hardcopy-example.json` demonstrates all of this on dummy data from
`data/hardcopy-demo.csv`:

```bash
python dash-lineplot.py --configfile hardcopy-example.json
```

Its tab `many` holds ten short graphs at four per page (three pages),
`mixed` mixes graph heights on a `commonX` tab with no per-page setting
(two pages), and `boundary` shows the 200 pixel threshold on a single page.
`tools/make_hardcopy_demo_data.py` regenerates the data file.

## Further reading

- Dash documentation, [https://dash.plotly.com/](https://dash.plotly.com/)
- Plotly Python reference,
  [https://plotly.com/python/reference/](https://plotly.com/python/reference/)
- Plotly colour names,
  [https://www.w3schools.com/cssref/css_colors.asp](https://www.w3schools.com/cssref/css_colors.asp)
- The style sheet in `assets/` is adapted from
  [https://codepen.io/chriddyp/pen/bWLwgP](https://codepen.io/chriddyp/pen/bWLwgP)
