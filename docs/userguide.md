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
| `.json` | A record array: a list of flat objects, one object per sample. |
| `.mat` | Matlab file with data in `DATA`, column names in `NAM` and the time base in `TIME`. |

Whatever the format, the result is one table per file, and the
configuration refers to columns of that table by name.

### JSON record arrays

A JSON data file holds a list of objects. Each object is one sample, and
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

### One file, one time base

Each data file keeps its own time column, and files are never merged onto a
shared time base or resampled against one another. This matters when
plotting data produced by processes that sample at different rates: a signal
recorded every 1 ms and one recorded every 20 ms are drawn at their true
densities, twenty to one, and neither is interpolated to match the other.
A zero-order hold belongs to the process that causes it, not to the plotting
layer, so the display never invents samples that the recording did not
contain.

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
  blocks at the top and bottom of every page, and an optional master data
  file name.
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
| `UseSubplots` | `True` or `False`. See the note on subplots under features not currently available. |
| `xSliderStep` | Resolution of the x-axis slider. See the note on the slider under features not currently available. |

Any number of graphs may appear on one tab. A `Title` entry opens a new
graph, and the `yLabel` and `yValue` entries that follow it belong to that
graph until the next `Title`.

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
markdown from `PageTop`, then for each graph its `GraphTop` markdown, the
graph itself, the two data feedback boxes, and its `GraphBottom` markdown.
The `PageBottom` markdown closes the page.

Select a tab to display its graphs. Graphs are drawn when the tab is first
selected rather than when the page loads, so the first selection of a tab
carrying a large data set takes a moment.

### Hover

Moving the pointer across a graph displays the values of every line in that
graph at the hovered x position, each in its line colour, together with the
x value. The numbers are formatted according to the `Format` attribute set
on the `xLabel` and `yLabel` rows.

Hover readout is shared by the lines within one graph. It is not shared
across separate graphs.

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

**Rectangle Tool Selection Data.** Select Box Select in the toolbar, then
drag a rectangle across the graph. The box reports the corners of the
selection and its extent in x and y.

Box selection acts on data points, so it needs markers: a graph whose lines
are drawn in the default `lines` mode has no points to select and the box
continues to read `none selected`. Set `Mode` to `markers+lines` on the
lines being measured. For a large data set, also set `MarkerOpacity` to 0,
which keeps the selection working without drawing thousands of markers.
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
- **Hover synchronised across subplots.** This depended on the subplot
  path and on the `visdcc` package, which is no longer maintained and has
  been removed. Hover remains shared between the lines within one graph.
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
