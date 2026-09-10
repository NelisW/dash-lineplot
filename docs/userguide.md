# Dash Line Plot User Guide

The Python script `dash-lineplot.py` is a general plotting utility that aids
in the visualisation of captured or recorded data. It reads a configuration
file, builds a set of Plotly graphs from the data files that configuration
names, and serves them as a set of tabbed pages through a local Flask
server. The user has full control over which graph sets are rendered on
which page.

This is the first revision of this guide, covering installation,
configuration, data formats and use of the browser display. It will be
extended as the tool develops. The older guide in `doc/`, built from LaTeX
sources and dated March 2020, describes the utility as it was when it ran
inside a Qt desktop window; where the two disagree, this document is
current. The section on features not currently available records what was
lost in between.

## Installation

### Requirements

The utility needs a Python environment with Dash, Plotly, pandas, numpy,
openpyxl and scipy. Everything it uses is open source. `scipy` is needed
only by the Matlab data reader and is imported lazily, so it costs nothing
until a `.mat` file is actually read.

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
`http://127.0.0.1:8050/`, in a browser. Stop the server with Ctrl+C.

The command line takes three options:

| Option | Meaning |
|---|---|
| `-f`, `--configfile` | Configuration file, `.xlsx` or `.json`. Defaults to `./dash-config.xlsx`. |
| `-p`, `--port` | Port for the local Flask server. Defaults to 8050. |
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
| `assets/` | The cascading style sheet that formats the page. Dash is unstyled by default. |
| `icons/` | Images used on the page. |

A `graphs/` folder is created by the script whenever it builds a page,
whether or not anything is written into it. It receives a standalone
interactive HTML file per graph set whose sheet sets `ToDisk` to `True`.
Those files can be opened directly in a browser, with full Plotly
functionality and without a running server, and are regenerated on every
run. The folder is build output and is not tracked in version control.

## Input data file formats

A single configuration may draw on several data files of different types.
The type is chosen from the file extension.

| Extension | Format |
|---|---|
| `.csv` and most others | Column names on the top line, one sample per line. |
| `.xlsx` | First sheet only, column names in the top row. |
| `.json` | A record array, or an object of named groups. See below. |
| `.mat` | Matlab file with data in `DATA`, column names in `NAM` and the time base in `TIME`. |

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
top-level object is a set of named groups. Nothing else changes. Existing
single-rate files continue to mean what they have always meant, and rates
are never inferred from timestamps.

A group is selected by appending a `#` fragment to the `Datafile` value:

```text
data/example-multirate.json#gimbal_1ms
```

Naming a group that does not exist, or omitting the fragment for a file
that has groups, is reported with the list of groups the file does contain.

Data recorded at different rates in **separate** files needs no fragment.
One file is one table, as before.

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
| `Height` | Height of each graph in the browser, in pixels. |
| `Datafile` | Path to the data file for this tab. The keyword `master` selects the file named on the header sheet. |
| `xLabel` | Label for the x axis. |
| `xValue` | Name of the data column supplying x values. |
| `Title` | Title of one graph. Starts a new graph set. |
| `yLabel` | Label for the y axis of the current graph. |
| `yValue` | Name of a data column supplying y values. Repeat it for more lines on the same graph. |
| `GraphTop` | Markdown inserted immediately above the graph. |
| `GraphBottom` | Markdown inserted immediately below the graph. |
| `Include` | `True` or `False`. Whether this tab appears at all. Defaults to `True`. |
| `ToDisk` | `True` or `False`. Whether to write a standalone HTML copy into `graphs/`. |
| `commonX` | `True` or `False`. Tie every graph on this tab to one x scale. Defaults to `False`. |
| `UseSubplots` | `True` or `False`. See the note on subplots under features not currently available. |
| `xSliderStep` | Resolution of the x-axis slider. See the note on the slider under features not currently available. |

Any number of graphs may appear on one tab. A `Title` entry opens a new
graph, and the `yLabel` and `yValue` entries that follow it belong to that
graph until the next `Title`.

### Header variables

| Variable | Meaning |
|---|---|
| `Pagetitle` | Browser tab title. |
| `PageTop`, `PageBottom` | Markdown rendered at the top and bottom of every page. |
| `Datafile` | Master data file. A graph sheet selects it with the keyword `master`. |
| `Density` | `compact` or `comfortable`. Defaults to `compact`. |

`Density` controls how tightly the page is packed.

`compact` reduces the heading sizes, removes the vertical space between one
graph row and the next entirely, and tightens the margins Plotly reserves
around each plot so that the data area fills roughly 70 percent of the
graph rather than 40. The graph title is drawn inside the plotting area,
against its top left corner, rather than in a band of page above the graph,
so a title costs no page height at all. `comfortable` restores the roomier
original spacing, leaves Plotly's default margins alone, and puts the title
back above the plot.

Measured on a seven-graph page with `Height` set to 240: 1940 px compact
against 4286 px comfortable.

### Tying the graphs of a tab to one x scale

Set `commonX` to `True` on a graph sheet and every graph on that tab shares
one x range. Two things follow.

**Zoom and pan apply to all of them.** Drag-zooming, panning or autoscaling
any graph applies the same x range to every other graph on the tab, so the
whole tab always shows the same interval. If the x axis is time, the graphs
stay aligned in time whatever the reader does to one of them.

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

Without `commonX`, each graph zooms independently and its Click Data box
reports only clicks on that graph, in the two-point form described under
measurements below.

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

This writes one tab per data file and one graph per column, with the time
column on the x axis. Columns whose values are not numeric, such as a text
mode or state name, cannot be plotted as lines; they are listed in the
tab's own markdown rather than dropped without notice. The generated file
is a starting point meant to be edited, typically to group related signals
onto shared axes.

## Using the browser display

### Page layout

Every page carries, from top to bottom: the row of tabs, the header
markdown from `PageTop`, then the `GraphTop` markdown, then one row per
graph, then the `GraphBottom` and `PageBottom` markdown.

Each graph occupies a row of its own, with the graph on the left and its
two readout boxes stacked in a narrow column on the right:

```text
+-------------------------------------------+  +-----------------+
|                                           |  | Click Data      |
|                  graph                    |  +-----------------+
|                                           |  | Rectangle Tool  |
+-------------------------------------------+  +-----------------+
```

Keeping the readouts beside the graph rather than beneath it is what lets
consecutive graphs sit directly against one another. In the compact
density there is no vertical space at all between one graph row and the
next, so a page is exactly as tall as its graphs.

The height of each graph is the sheet's `Height` value, in pixels.

Select a tab to display its graphs. Graphs are drawn when the tab is first
selected rather than when the page loads, so the first selection of a tab
carrying a large data set takes a moment.

### Hover

Moving the pointer across a graph displays the values of every line in that
graph at the hovered x position, each in its line colour, together with the
x value. The numbers are formatted according to the `Format` attribute set
on the `xLabel` and `yLabel` rows. An enumeration shows its state name.

**The readout is shared by every graph on the page.** Hovering any one
graph makes all the others display their own values at the same x position
at the same time, so a whole page of signals can be read at one instant
without clicking anything.

Each graph resolves that x position against its own samples. Graphs
recorded at different rates therefore show their own nearest sample rather
than an interpolated one, and a graph whose x range does not cover the
hovered position simply shows nothing.

### Zoom, pan and the Plotly toolbar

The toolbar appears at the top right of a graph when the pointer is over
it. It carries the standard Plotly controls:

| Control | Effect |
|---|---|
| Zoom | Drag a rectangle to zoom into it. |
| Pan | Drag to move the visible window. |
| Box Select, Lasso Select | Select points, feeding the selection box below the graph. |
| Zoom in, Zoom out | Step the zoom about the centre. |
| Autoscale, Reset axes | Return to the full data range. |
| Download plot as a PNG | Save the current view as an image. |

Double-clicking inside a graph also resets the axes.

### Measurements on a graph

Two feedback boxes sit below each graph, and both work alongside zooming.

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
1. Drag across the region of interest. The box then reports the top-left
   and bottom-right corners and the extent in x and y.

If the box still reads `none selected`, the selection enclosed no data
points. Selecting an empty region of the plot area is the usual cause.

Markers slow rendering noticeably on large data sets, which is why they are
not the default.

## Features not currently available

These are documented in the older guide and are absent from the current
version. They are recorded here so their absence is not mistaken for a
fault.

- **The x-axis range slider.** The original version placed a range slider
  above each page, with text boxes and a reset button, to restrict the
  graphs to a chosen x interval. Its layout is commented out in the source.
  The reason given there is that the slider depended on the user clicking
  the current tab to trigger a redraw, and that mechanism stopped working
  with newer versions of the underlying modules. Use the Plotly zoom
  controls instead. The `xSliderStep` configuration variable is still read
  but currently has no effect.
- **Subplots.** `UseSubplots` grouped the graph sets of one sheet into a
  single Plotly figure with shared axes. The path is disabled and the
  script reports `Subplots functionality disabled` on start-up.
- **Hover synchronised through subplots.** The original mechanism grouped
  a sheet's graph sets into one Plotly figure and relied on the `visdcc`
  package to inject the linking JavaScript. Both are gone. Synchronised
  hover itself is not: it now covers every graph on the page rather than
  only the subplots of one figure, and is implemented in
  `assets/graphsync.js`, which Dash serves automatically and which needs no
  package at all. The same file links the x axes of a `commonX` tab.
- **The packaged executable and its Windows launcher.** `dash-lineplot.exe`,
  `startPlotTool.bat` and the PyInstaller configuration package a Qt
  desktop application that no longer exists. Start the script directly.

TODO: the Matlab reader is carried forward unchanged from the original
version and has not been exercised against a current Matlab file. It is
documented here as designed, not as verified.

## Further reading

- Dash documentation, [https://dash.plotly.com/](https://dash.plotly.com/)
- Plotly Python reference,
  [https://plotly.com/python/reference/](https://plotly.com/python/reference/)
- Plotly colour names,
  [https://www.w3schools.com/cssref/css_colors.asp](https://www.w3schools.com/cssref/css_colors.asp)
- The style sheet in `assets/` is adapted from
  [https://codepen.io/chriddyp/pen/bWLwgP](https://codepen.io/chriddyp/pen/bWLwgP)
