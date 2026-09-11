################################################################
# The contents of this file are subject to the licenses listed below.
# You may not use this file except in compliance with these Licenses. 
# 
# Python, scipy, numpy, pandas, openpyxl and other 'standard' modules are
# licensed under the Python License: https://docs.python.org/3/license.html.
#
# plotly/dash is licensed under MIT https://community.plot.ly/t/pricing-and-license/9714
# https://en.wikipedia.org/wiki/MIT_License
#
# PySide/Qt and visdcc were used by earlier versions and are no longer
# dependencies; their licence notices were removed with them.
#
################################################################

"""

This script reads a config file, in Excel or JSON form, and one or more of
the following data file types:
    * matlab file with data in 'DATA', variable names in 'NAM' and time base in 'TIME'
    * csv files with column names in top row
    * first sheet of an xlsx file with column names in top row
    * json files holding either one record array, a list of flat objects with
      one object per sample, or an object of named groups, one group per
      sample rate, each selected as 'file.json#group'
It the then proceeds to create and serve a Dash portal.
The page served has several elements, all constructed from the
information provided in the config file.

The config file has any number of sheets where each sheet defines
a different set of line graphs to be rendered on a separate tab
(except for the header sheet, which defines the page header.)
Each graph sheet defines the height of the graphs, axes labels,
one x-value column name and any number of sets of y-value column names.
Each line has a number of attributes with default values if not supplied.
Each tab can be switched on/off for display purposes.
Each graph set can be exported to an html file.
A JSON config mirrors that structure one for one, using the same names.

Nothing about the data is inferred. Column names, the time column and the
groups of a multi-rate file are all named in the config, tables are never
merged or resampled against one another, and a column whose values are text
is plotted as an enumeration with its labels on the y axis. Graphs recorded
at different rates therefore keep their own sample density.

Every graph on a page shares the hover readout. A tab that sets commonX
also shares one x range: zoom, pan, click and rubber-band selection on any
of its graphs apply to all of them. See assets/graphsync.js.

In the present script the default config filename is './dash-config.xlsx'.
Any other filename can be provided on the commandline using the -f input flag.

Dash starts a Flask server at the specified port, so the browser must be
pointing to the appropriate port number
localhost:port
The page is served to the system browser; the PySide desktop window used by
earlier versions has been removed.

This module requires the following data in the current directory:
 * icons/logoSet2long.png
 * assets/bWLwgP.css

It will create folder 'graphs' for output. 

There are numerous Dash and Plotly resources on the Internet:
https://dash.plot.ly/integrating-dash
https://plot.ly/python/reference/
https://www.datacamp.com/community/tutorials/learn-build-dash-python
https://github.com/plotly/dash-recipes
https://github.com/plotly/dash-recipes/blob/master/multiple-hover-data.py
https://plot.ly/python/subplots/
https://towardsdatascience.com/creating-an-interactive-data-app-using-plotlys-dash-356428b4699c
https://dash.plot.ly/dash-core-components/tabs
https://dash.plot.ly/getting-started-part-2
https://plot.ly/python/range-slider/
https://plot.ly/python/click-events/

This script requires dash, plotly, pandas, numpy, openpyxl, scipy and some
system modules. Create the environment from the environment.yml shipped
beside this script, which solves on both Linux and Windows:

    conda env create -f environment.yml
    conda activate dashplot

The plots are served to the system browser. There is no desktop-window
build: the PySide2/PyQt5 shell that used to wrap the Flask server was
removed, because PySide2 has no support beyond Python 3.10 and the window
added nothing the browser does not do.

Plotly packages seem to be here:
https://anaconda.org/plotly  
https://anaconda.org/plotly/repo  
There are 17 packages, located under the package name, Files tab:
https://anaconda.org/plotly/plotly/files  
or   
https://anaconda.org/plotly/dash/files 

To use as a module in another application:

1) Import the DashLinePlot and DashPlotWindow classes from the module
            
2) In your code implement something like:

    # create new window
    self.dashWidget = DashPlotWindow(port)
    self.dashWidget.show()

    # do actual plotting
    useCallBacks = True
    plotConfig = './dash-config.xlsx'
    port = '8050' 
    dashlineplotter = DashLinePlot()
    dashlineplotter.runPlotter(port, plotConfig, useCallBacks)

Notes from https://dash.plot.ly/getting-started:
* The layout is composed of a tree of "components" like html.Div and dcc.Graph.
* The dash_html_components library has a component for every HTML tag. 
  Each html.xxx(children='yyy') component generates a <h1>yyy</h1> HTML element in your application.
* Not all components are pure HTML. The dash_core_components describe higher-level components that 
  are interactive and are generated with JavaScript, HTML, and CSS through the React.js library.
* Each component is described entirely through keyword attributes. 
  Dash is declarative: you will primarily describe your application through these attributes.
* The children property is special. By convention, it's always the first attribute which means that you can omit it: 
     html.xxx(children='yyy') is the same as html.xxx('yyy'). 
  Also, it can contain a string, a number, a single component, or a list of components.
* The fonts in the application can be set with a custom CSS stylesheet to modify the default styles of the elements. 
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

https://dash.plot.ly/dash-html-components
The dash layout is composed of a tree of "components" like html.Div and dcc.Graph.
The dash_html_components library contains a component class for every HTML tag as well as keyword arguments 
for all of the HTML arguments.

https://dash.plot.ly/dash-core-components
The dash_core_components includes a set of higher-level components like dropdowns, graphs, markdown blocks, and more.
Graph renders interactive data visualizations using the open source plotly.js JavaScript graphing library. 
Plotly.js supports over 35 chart types and renders charts in both vector-quality SVG and high-performance WebGL.
The figure argument in the dash_core_components.Graph component is the same figure argument that is used by plotly.py, 
Plotly's open source Python graphing library. Check out the plotly.py documentation and gallery to learn more.

Notes on callbacks https://dash.plot.ly/getting-started-part-2:

# https://dash.plot.ly/dash-core-components/tabs
# A Div component is a wrapper for the <div> HTML5 element.
Div(
    [
        # The Tabs component hold a collection of Tab components.
        Tabs
        (
            # children (list of a list of or a singular dash component, string or numbers | a list of or a singular dash component, 
            # string or number; optional): Array that holds Tab components
            children=
            [
                # The Tab component controls the style and value of the individual tab 
                # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
                #                        The ID needs to be unique across all of the components in an app.
                # label (string; optional): The tab's label
                # value (string; optional): Value for determining which Tab is currently selected
                #
                # Possible properties of Tab# ['children', 'id', 'label', 'value', 'disabled', 'disabled_style', 'disabled_className', 'className', 'selected_className', 'style', 'selected_style', 'loading_state']
                
                Tab(id='RelativePosition', label='RelativePosition', value='Tab 0'), 
                Tab(id='Velocity', label='Velocity', value='Tab 1'), 
                Tab(id='MissilePosition', label='MissilePosition', value='Tab 2'), 
                Tab(id='gimbalFromxls', label='gimbalFromxls', value='Tab 3')
            ], 
            
            # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
            # The ID needs to be unique across all of the components in an app.
            id='tabs', 
            
            # value (string; optional): The value of the currently selected Tab
            value='Tab 0'
        ), 
        
        # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
                                 The ID needs to be unique across all of the components in an app.
        Div(id='tabs-content')
    ]
    )
    
"""
__version__= '$Revision: 4633 $'
__author__='CJ & MS Willers'

import sys, os
import json
import math
import threading
import pandas as pd
import openpyxl as oxl
import numpy as np
import datetime
import itertools

import dash
from dash import dcc
from dash import html
from dash import Patch
from dash.dependencies import Input, Output, State
from plotly import subplots

external_stylesheets = ['assets/bWLwgP.css']

pd.set_option('display.max_rows', 500)

# https://stackoverflow.com/questions/55596932/how-can-i-include-assets-of-a-dash-app-into-an-exe-file-created-with-pyinstaller
# when packaging the app with pyInstaller the assets folder is not included correctly
# defining resource_path as below and using
#     dash.Dash(__name__, assets_folder=resource_path('assets'))
# solves the problem 
def resource_path(relative_path):

# get absolute path to resource
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

################################################################
# Columns a graph sheet may carry. Any sheet is reindexed onto these so that
# a column nobody used still exists as NaN: the graph code indexes them by
# name unconditionally, and a JSON config naturally omits what it does not
# set. Extra columns beyond this list are preserved.
CONFIG_COLUMNS = ['Variable', 'Value', 'Format', 'LineLabel', 'GraphType',
                  'Scale', 'Offset', 'Colour', 'Linewidth', 'Dash', 'Mode',
                  'MarkerOpacity', 'Categories', 'Datafile']

################################################################
def splitDataRef(dataref):
    """
    Split a data reference into a file name and an optional group name.

    A reference may carry a '#group' fragment naming one group inside a
    multi-rate JSON file, as in 'out/run.json#gimbal_1ms'. A reference with
    no fragment means the whole file, which is what every non-JSON format
    and every single-rate JSON file uses.

    Args:
        | dataref (string): the Datafile value from the configuration.

    Returns:
        | filename (string): the file name, fragment removed.
        | group (string): the group name, or None if no fragment was given.

    """
    filename, hashmark, group = str(dataref).partition('#')
    return filename, group if hashmark else None

################################################################
def readJsonData(path, group):
    """
    Read a JSON data file into a DataFrame.

    Two shapes are accepted, and which one a file uses is declared by its
    own structure rather than inferred from the data:

    A top-level list is a single record array, one object per sample. This
    is the single-rate form, and a group must not be named.

    A top-level object is a set of named groups, each holding its own record
    array with its own time column. This is the multi-rate form: each group
    becomes a separate DataFrame and nothing is merged, resampled or aligned
    between them. A group must be named, using a '#group' fragment on the
    Datafile value.

    Args:
        | path (string): path to the JSON file.
        | group (string): group name from the reference fragment, or None.

    Returns:
        | df (DataFrame): the requested data.

    """
    with open(path, 'r', encoding='utf-8') as fjson:
        content = json.load(fjson)

    if isinstance(content, list):
        if group is not None:
            raise ValueError(
                f"{path} is a single record array and holds no groups, but "
                f"the configuration asks for group '{group}'. Drop the "
                f"'#{group}' fragment from the Datafile value.")
        return pd.DataFrame.from_records(content)

    if isinstance(content, dict):
        available = ', '.join(content.keys()) if content else 'none'
        if group is None:
            raise ValueError(
                f"{path} holds named groups, so the configuration must say "
                f"which one to plot by appending a fragment to the Datafile "
                f"value, as in '{os.path.basename(path)}#<group>'. "
                f"Groups present: {available}.")
        if group not in content:
            raise ValueError(
                f"{path} has no group '{group}'. Groups present: {available}.")
        return pd.DataFrame.from_records(content[group])

    raise ValueError(
        f'{path} must hold either a list of samples or an object of named '
        f'groups, but holds {type(content).__name__}.')

################################################################
def traceYExtent(traces):
    """
    Smallest and largest y over the traces of one graph.

    Used only for the placeholder text in the Y range boxes, so a reader can
    see what range the graph covers without guessing. Missing values are
    ignored, and a graph with nothing numeric on it yields (None, None).

    Args:
        | traces (list): the trace dicts of one graph.

    Returns:
        | (tuple): (ymin, ymax), either of which may be None.

    """
    lo, hi = None, None
    for trace in traces:
        values = np.asarray([np.nan if v is None else v for v in trace['y']],
                            dtype=float)
        if values.size == 0 or np.all(np.isnan(values)):
            continue
        low, high = float(np.nanmin(values)), float(np.nanmax(values))
        lo = low if lo is None else min(lo, low)
        hi = high if hi is None else max(hi, high)
    return lo, hi

################################################################
def resolveSetContexts(dft):
    """
    The settings in force for each graph on a sheet.

    A sheet is read top to bottom as a sequence of blocks. A Height row opens
    a block, and a Datafile, xValue or xLabel row applies to every graph below
    it until another row of the same kind replaces it. Each Title captures
    whatever is in force at that point, so one tab can carry several data
    files, each with its own time column.

    A sheet with one block behaves exactly as it did before blocks existed:
    its single Datafile and xValue apply to every graph on it.

    Args:
        | dft (DataFrame): the rows of one graph sheet, in sheet order.

    Returns:
        | contexts (dict): set number as '000', '001', ... to a dict of
          datafile, xvalue, xlabel, xformat, xscale, xoffset and height.

    """
    current = {'datafile': None, 'xvalue': None, 'xlabel': '', 'xformat': '.4f',
               'xscale': 1.0, 'xoffset': 0.0, 'height': 300}
    contexts = {}
    setNumber = -1

    for _, row in dft.iterrows():
        variable = row['Variable']

        if variable == 'Height':
            current['height'] = row['Value']
        elif variable == 'Datafile':
            current['datafile'] = row['Value']
        elif variable == 'xLabel':
            current['xlabel'] = row['Value']
            current['xformat'] = row['Format'] if isinstance(row['Format'], str) else '.4f'
        elif variable == 'xValue':
            current['xvalue'] = row['Value']
            # Scale and Offset ride on the xValue row, so they belong to the
            # block that row opened, not to the sheet
            current['xscale'] = (float(row['Scale'])
                                 if not np.isnan(row['Scale']) else 1.0)
            current['xoffset'] = (float(row['Offset'])
                                  if not np.isnan(row['Offset']) else 0.0)
        elif variable == 'Title':
            setNumber += 1
            contexts[f'{setNumber:03d}'] = dict(current)

    return contexts

################################################################
def selectionBounds(selectedData):
    """
    The x and y extent of a Plotly selection, whichever tool made it.

    Box Select reports a 'range'; Lasso Select reports the polygon it drew
    as 'lassoPoints' and no 'range' at all, so handling only the first makes
    the lasso appear silently broken. A lasso is reduced to the bounding box
    of its polygon.

    Args:
        | selectedData (dict): the selectedData property of a Graph.

    Returns:
        | bounds (tuple): (xRange, yRange), each a two-element list, or None
          if nothing was selected.

    """
    if not selectedData:
        return None

    if 'range' in selectedData:
        # for divs where we work with subplots, the number of the subplot is
        # added to the x and y key, so take the keys programmatically
        ranges = selectedData['range']
        keys = list(ranges)
        if len(keys) < 2:
            return None
        return ranges[keys[0]], ranges[keys[1]]

    if 'lassoPoints' in selectedData:
        lasso = selectedData['lassoPoints']
        keys = list(lasso)
        if len(keys) < 2:
            return None
        xs, ys = lasso[keys[0]], lasso[keys[1]]
        if not xs or not ys:
            return None
        return [min(xs), max(xs)], [min(ys), max(ys)]

    return None

################################################################
def nearestSample(xs, x):
    """
    Index of the sample nearest x, or None for an empty series.

    Used to read a graph at an x that was clicked on a different graph. The
    nearest recorded sample is reported rather than an interpolated value,
    because graphs sharing an x axis need not share a sample rate.

    Args:
        | xs (Series or list): the x values of one trace.
        | x (float): the x value to look up.

    Returns:
        | index (int): index of the nearest sample, or None.

    """
    values = np.asarray(xs, dtype=float)
    if values.size == 0:
        return None
    return int(np.abs(values - x).argmin())

################################################################
def isEnumSeries(series):
    """
    True if this column holds enumeration labels rather than numbers.

    Booleans count as numeric: they already plot as 0 and 1. Anything else
    that is not numeric is treated as an enumeration, which is the only way
    a column of state or mode names can be drawn at all.

    Args:
        | series (Series): the data column.

    Returns:
        | (bolean): True for an enumeration column.

    """
    return not (pd.api.types.is_numeric_dtype(series) or
                pd.api.types.is_bool_dtype(series))

################################################################
def parseCategories(value):
    """
    Read a declared category order from a configuration cell.

    Accepts a JSON list, or a comma-separated string as typed into a
    spreadsheet cell. Returns None when nothing was declared, in which case
    the order is taken from the data.

    Args:
        | value: the Categories cell value.

    Returns:
        | categories (list): ordered category names, or None.

    """
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    if isinstance(value, str) and value.strip():
        return [s.strip() for s in value.split(',') if s.strip()]
    return None

################################################################
def enumCategories(series, declared=None):
    """
    Ordered list of the categories in an enumeration column.

    A declared order is used verbatim, so an axis can be held identical
    across runs even when a run does not exercise every state. Otherwise
    the order is order of first appearance in the data, so a mode sequence
    reads up the axis in the order it happened.

    Values present in the data but absent from a declared list are appended
    at the end rather than dropped, because silently discarding a state
    would hide exactly the event worth seeing.

    Args:
        | series (Series): the enumeration column.
        | declared (list): category order from the configuration, or None.

    Returns:
        | categories (list): ordered category names.

    """
    categories = list(declared) if declared else []
    for value in series:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        name = str(value)
        if name not in categories:
            categories.append(name)
    return categories

################################################################
def isJsonConfig(configfile):
    """
    True if this configuration file is JSON rather than an Excel workbook.

    Args:
        | configfile (string): configuration filename.

    Returns:
        | (bolean): True for a .json configuration.

    """
    return os.path.splitext(configfile)[1].lower() == '.json'

################################################################
def readConfigTables(configfile):
    """
    Read a configuration from .xlsx or .json into a common table form.

    The JSON schema mirrors the workbook one for one: a 'header' object of
    Variable/Value pairs, and a 'sheets' object mapping each graph sheet
    name to the list of row objects that sheet held. Field names are the
    workbook's column names verbatim, so a workbook and its converted JSON
    describe the same plot in the same words.

    Args:
        | configfile (string): configuration filename, .xlsx or .json.

    Returns:
        | dfHeader (DataFrame): the header table, columns Variable and Value.
        | sheets (dict): sheet name to DataFrame, in file order.

    """
    def onCanonicalColumns(df):
        extras = [c for c in df.columns if c not in CONFIG_COLUMNS]
        return df.reindex(columns=CONFIG_COLUMNS + extras)

    if isJsonConfig(configfile):
        with open(configfile, 'r', encoding='utf-8') as fjson:
            cfg = json.load(fjson)
        dfHeader = pd.DataFrame([{'Variable': k, 'Value': v}
                                 for k, v in cfg['header'].items()])
        sheets = {name: onCanonicalColumns(pd.DataFrame(rows))
                  for name, rows in cfg['sheets'].items() if 'graph' in name}
        return dfHeader, sheets

    cxls = pd.ExcelFile(configfile)
    dfHeader = pd.read_excel(cxls, 'header')
    # openpyxl rather than pd.ExcelFile.sheet_names, to keep the workbook's
    # own sheet order
    cwb = oxl.load_workbook(configfile)
    sheets = {sn: onCanonicalColumns(pd.read_excel(cxls, sn))
              for sn in cwb.sheetnames if 'graph' in sn}
    return dfHeader, sheets

################################################################
def readPageTitle(configfile):
    """
    Read the page title from the configuration file's header.

    Used as the browser tab title. Before the Qt shell was removed this was
    the native window's title.

    Args:
        | configfile (string): configuration filename.

    Returns:
        | pagetitle (string): the configured title, or a default.

    """
    default = 'Dash flask server for plotting'
    dfHeader, _ = readConfigTables(configfile)
    dfHeader = dfHeader.set_index('Variable')
    if 'Pagetitle' in dfHeader.index:
        return str(dfHeader.loc['Pagetitle', 'Value'])
    return default

################################################################
class DashLinePlot():

    def __init__(self):
        """
        Initialise class variables.
        """
        self.useCallbacks = True

        # storage for last 2 clicked point all graphs
        self.clickedData = {}

        # traces per graph id, so a click on one graph of a commonX group can
        # report the values of every graph in that group at the clicked x
        self.graphTraces = {}

        # graph id to the list of graph ids sharing its x axis, for tabs that
        # set commonX. Graphs on other tabs do not appear here at all.
        self.commonXGroups = {}

        # last two clicked x values per graph, for the commonX readout
        self.clickedX = {}

    ##########################################
    def commonClickMessage(self, grID, xClicked):
        """
        Readout for one graph of a commonX group, at the clicked x.

        Every graph of the group reports at the same x, whichever graph was
        actually clicked, so one click reads the whole tab. The value quoted
        for each line is its nearest recorded sample, never an interpolation:
        graphs in a group may sample at different rates, and inventing a
        value between two samples would be a fiction.

        Args:
            | grID (string): the graph this readout belongs to.
            | xClicked (float): x value of the click, on any graph of the group.

        Returns:
            | msg (string): the text for this graph's Click Data box.

        """
        history = self.clickedX.setdefault(grID, [])
        history.append(xClicked)
        del history[:-2]

        lines = []
        if len(history) == 2:
            lines.append(f'Previous x: {history[0]:.6f}')
        lines.append(f'Current  x: {xClicked:.6f}')
        if len(history) == 2:
            lines.append(f'Range    x: {abs(history[1] - history[0]):.6f}')

        for name, xs, ys, texts in self.graphTraces.get(grID, []):
            index = nearestSample(xs, xClicked)
            if index is None:
                continue
            if texts is not None and index < len(texts):
                shown = str(texts[index])
            else:
                value = list(ys)[index]
                shown = 'n/a' if value is None else f'{float(value):.6f}'
            lines.append(f'  {name} = {shown}')

        return '\n'.join(lines)

    ##########################################
    def commonSelectMessage(self, grID, xRange):
        """
        Selection readout for one graph of a commonX group.

        Only the x window is shared. The graphs of a group have their own y
        scales, and often their own units, so a y range selected on one of
        them means nothing on another. Each graph therefore reports the
        extent of its own data inside the shared x window, which is the
        useful quantity: what this signal did while that one did that.

        Args:
            | grID (string): the graph this readout belongs to.
            | xRange (list): [x0, x1] of the selection, on any graph of the group.

        Returns:
            | msg (string): the text for this graph's selection box.

        """
        x0, x1 = min(xRange), max(xRange)
        lines = [f'Selected x: [{x0:.6f}, {x1:.6f}]',
                 f'Width    x: {abs(x1 - x0):.6f}']

        for name, xs, ys, texts in self.graphTraces.get(grID, []):
            values = np.asarray(xs, dtype=float)
            inWindow = (values >= x0) & (values <= x1)
            count = int(inWindow.sum())
            if count == 0:
                lines.append(f'  {name}: no samples in range')
                continue

            if texts is not None:
                # an enumeration has no meaningful minimum: report the states
                # it actually visited inside the window, in order of occurrence
                seen = []
                for keep, label in zip(inWindow, texts):
                    if keep and str(label) not in seen:
                        seen.append(str(label))
                lines.append(f'  {name}: {", ".join(seen)}  ({count} samples)')
                continue

            yValues = np.asarray([np.nan if v is None else v for v in ys],
                                 dtype=float)[inWindow]
            if np.all(np.isnan(yValues)):
                lines.append(f'  {name}: no values in range')
                continue
            lines.append(f'  {name}: y in [{np.nanmin(yValues):.6f}, '
                         f'{np.nanmax(yValues):.6f}]  ({count} samples)')

        return '\n'.join(lines)

    ##########################################
    def generateFeedbackBoxes(self, id, isMarkers, xmin=None, xmax=None,
                              ymin=None, ymax=None):
        """
        Builds the column beside a graph: x-range entry and the readout boxes

        The x-range boxes replace the range slider of earlier versions, which
        depended on the reader clicking the current tab to trigger a redraw
        and stopped working when that mechanism changed. Typing a start and
        an end is the capability the slider provided; the slider itself was
        only ever the means.

        Args:
            | id (string): id string.
            | isMarkers (bolean): whether any line carries markers, which is
                             what makes a selection possible at all.
            | xmin (double): smallest x in the data, shown as a placeholder.
            | xmax (double): largest x in the data, shown as a placeholder.
            | ymin (double): smallest y on this graph, shown as a placeholder.
            | ymax (double): largest y on this graph, shown as a placeholder.

        Returns:
            | thisDivList (list): list of html Divs.

        """

        # style definition for the data display boxes
        boxStyle = {
            'border': 'thin lightgrey solid',
            'overflowX': 'scroll'
        }

        # Divs for click data and rectangle tool data feedback
        # https://dash.plot.ly/interactive-graphing
        # https://dash.plot.ly/dash-html-components/pre

        # The boxes sit in a narrow column beside the graph, so they stack
        # vertically rather than sharing a row of their own.
        clickDiv = html.Div(
                        [
                            dcc.Markdown(""" **Click Data** """),
                            html.Pre(id='click-'+ id, style=boxStyle),
                        ],
                        className='feedback-box'
                    )

        rectangleDiv =  html.Div(
                            [
                                dcc.Markdown(""" **Rectangle Tool Selection Data** """),
                                html.Pre(id='select-'+ id, style=boxStyle),
                            ],
                            className='feedback-box'
                        )

        # Axis range entry: type a start and an end on either axis, Apply to
        # zoom, Reset to go back to the full data range. One pair of buttons
        # drives both axes.
        #
        # On a commonX tab the x range applies to every graph on the tab,
        # while the y range applies only to the graph whose boxes were used:
        # the graphs of a tab have their own y scales and often their own
        # units, so a y range from one means nothing on another.
        def bound(value):
            return '' if value is None else f'{float(value):.6g}'

        xrangeDiv = html.Div(
                        [
                            dcc.Markdown(""" **X range** """),
                            dcc.Input(id='xstart-' + id, type='text', inputMode='decimal',
                                      placeholder=bound(xmin),
                                      className='xrange-input'),
                            dcc.Input(id='xend-' + id, type='text', inputMode='decimal',
                                      placeholder=bound(xmax),
                                      className='xrange-input'),
                            dcc.Markdown(""" **Y range** """),
                            dcc.Input(id='ystart-' + id, type='text', inputMode='decimal',
                                      placeholder=bound(ymin),
                                      className='xrange-input'),
                            dcc.Input(id='yend-' + id, type='text', inputMode='decimal',
                                      placeholder=bound(ymax),
                                      className='xrange-input'),
                            html.Button('Apply', id='xapply-' + id,
                                        className='xrange-button'),
                            html.Button('Reset', id='xreset-' + id,
                                        className='xrange-button'),
                        ],
                        className='feedback-box xrange-box'
                    )

        boxes = [xrangeDiv, clickDiv]
        if isMarkers:
            boxes.append(rectangleDiv)
        return html.Div(className='feedback-column', children=boxes)
                

    def graphToDisk(self, figdict, fbasename):
        """
        Save the figure to disk as html

        Args:
            | figdict (dict): figure data
            | fbasename (string): file base name.

        Returns:
            | None.


        """
        # Save the figure to disk as html
        import plotly.offline as offline
        offline.plot(figdict,
            auto_open=False, 
            output_type='file', filename=f'{fbasename}.html', validate=False)


    ##########################################
    def makeGraphSet(self, dft, graph, reqStart = 0, reqEnd = 0):
        """
        Builds the set of graphs on this tab (requested from one sheet in xls) 

        Args:
            | dft (pd.dataframe): info for this graph set.
            | graph (string): graph set name, i.e. text following "graph-" in the sheet name.
            | reqStart (double): starting x-value, default the beginning.
            | reqEnd (double): ending x-value, default the end. 

        Returns:
            | thisDivList (list): list of html Divs.
            | grList (list): list of the symbolic names of all graphs in this set.
            | xmin (double): minimum x value
            | xmax (double): maximum x value

        """
        #  colors
        backgroundColor = 'aliceblue'
        gridColour = 'lightgrey'

        # get the header info from the header sheet in the config file
        pagetop = dfPlotterHeader.loc['PageTop','Value'] if 'PageTop' in dfPlotterHeader.index else ''
        pagebottom = self.dateCreated + ' ' + dfPlotterHeader.loc['PageBottom','Value'] if 'PageBottom' in dfPlotterHeader.index else ''
        
        # create graphs output folder if not exist
        grDir = './graphs'
        if not os.path.exists(grDir):
            os.mkdir(grDir)

        # graphs to disk requested?
        toDisk = True
        if 'ToDisk' in dft.index:
            if not np.isnan(dft[(dft['Variable']=='ToDisk')]['Value'].values[0]):
                toDisk = dft[(dft['Variable']=='ToDisk')]['Value'].values[0]

        # commonX ties every graph on this tab to one x scale: zooming or
        # panning any of them applies the same range to all, and a click on
        # any of them reports the values of all at that x.
        commonX = False
        if 'commonX' in dft.index:
            requested = dft[(dft['Variable']=='commonX')]['Value'].values[0]
            commonX = bool(requested) and str(requested).strip().lower() not in ('false', '0', 'nan', '')

        # list of all graph names created here [passed back to calling function]
        # these names are the id of a Graph Div on the page, used in callback functions to update the figure
        grList = []

        # list of all the line entries for this graph set
        #  before building the page, all lines are first created and stored here
        graphData = []

        # Settings in force for each graph, resolved by walking the sheet in
        # order: a Height row opens a block, and a Datafile, xValue or xLabel
        # row applies to every graph below it until the next one. A sheet with
        # a single block behaves exactly as it always did.
        setContexts = resolveSetContexts(dft)

        # widest x range over every graph on the tab, for the x-range boxes
        xmin, xmax = None, None

        # ------- y data preparation

        # list of yValue values from config, i.e. the name of each variable to plot
        yVariableList = []

        # category labels per trace, aligned with yVariableList: a list of
        # names for an enumeration column, None for a numeric one
        enumCatsList = []

        # build the traces for all required variables in this graph set
        for index, row in dft[(dft['Variable']=='yValue')].iterrows():

            # add to yValue line list
            yVariableList.append(index)

            # y scale
            if 'Scale' in row:
                if not np.isnan(row['Scale']):
                    yscale = row['Scale']
                else:
                    yscale = 1.0

            # y offset
            if 'Offset' in row:
                if not np.isnan(row['Offset']):
                    yoffset = row['Offset']
                else:
                    yoffset = 0.
                    
            # each line in each graph must be a dict as follows:
            plotMode = 'lines'
            if 'Mode' in row:
                #  a sting and not empty
                if isinstance(row['Mode'], str) and not row['Mode'] == "":
                    plotMode = row['Mode']

            opacity = 0
            if 'MarkerOpacity' in row:
                if not np.isnan(row['MarkerOpacity']):
                    opacity = row['MarkerOpacity']
                    
            markerDict = { 'opacity': opacity }

            # An enumeration column holds state names and cannot be plotted as
            # a number. Map it onto integer codes and keep the labels, so the
            # axis can be relabelled with the names further down. Scale and
            # Offset are deliberately not applied to an enumeration: they have
            # no meaning for a state name.
            # Each trace resolves its x and y against the data file its own
            # block named, and a Datafile cell on this very row overrides even
            # that. Nothing is aligned or resampled between files: a tab may
            # carry signals recorded at different rates, and each is drawn at
            # the rate it was recorded.
            setStr = str(index).split('#')[1].split('-')[0]
            ctx = setContexts[setStr]

            dataref = ctx['datafile']
            if isinstance(row['Datafile'], str) and row['Datafile'].strip():
                dataref = row['Datafile'].strip()

            traceDf = self.datafiles[dataref]
            traceX = traceDf[ctx['xvalue']] * ctx['xscale'] + ctx['xoffset']

            xlo, xhi = traceX.min(), traceX.max()
            xmin = xlo if xmin is None else min(xmin, xlo)
            xmax = xhi if xmax is None else max(xmax, xhi)

            ySeries = traceDf[row['Value']]
            traceCategories = None

            if isEnumSeries(ySeries):
                traceCategories = enumCategories(ySeries,
                                                 parseCategories(row['Categories']))
                codeOf = {name: number for number, name in enumerate(traceCategories)}
                yValues = [codeOf.get(str(value)) for value in ySeries]
                hoverText = [str(value) for value in ySeries]
            else:
                yValues = ySeries * yscale + yoffset
                hoverText = None

            enumCatsList.append(traceCategories)

            dLines = {
                'x':traceX,
                'y':yValues,
                'line':{},
                'mode': plotMode,
                'marker': markerDict,   # we do not want markers but need them for the rectangle tool to appear
            }

            if traceCategories is not None:
                # A state signal is piecewise constant: it holds a value, then
                # jumps. A sloped line between two states would draw
                # intermediate states that never existed.
                dLines['line']['shape'] = 'hv'
                dLines['text'] = hoverText
                dLines['hovertemplate'] = '%{text}<extra></extra>'

            # fill in non-default values
            if not np.isnan(row['Linewidth']):
                dLines['line']['width'] = row['Linewidth']

            if isinstance(row['Colour'], str):
                dLines['line']['color'] = row['Colour']

            if isinstance(row['Dash'], str):
                dLines['line']['dash'] = row['Dash']

            if isinstance(row['GraphType'], str):
                dLines['type'] = row['GraphType']

            if isinstance(row['LineLabel'], str):
                dLines['name'] = row['LineLabel']
            else:
                dLines['name'] = row['Value']

            dLines['showlegend'] = True

            # add this line to other lines in this graph
            graphData.append(dLines)

        # ------- html Div's preparation
        thisDivList = []

        # 1) Div header: append the header text at the top of the page
        thisDivList.append(
            html.Div([dcc.Markdown(id=f'headerMarkdown-{graph}',children=pagetop)]),
        )  

        # 2) Div top text: if supplied, append the sheet top text  
        if 'GraphTop' in dft.index:
            thisDivList.append(
                html.Div([dcc.Markdown(id=f'topMarkdown-{graph}',children=dft.loc['GraphTop','Value'])])
            )            

        # 4) Graph and data feedback Divs

        # title rows
        titleRows = dft[(dft['Variable']=='Title')]

        #  collect the data for the graphs by running through each set
        for index, row in titleRows.iterrows():

            # get the set number as a string
            setStr = str(index).split('#')[1]

            # the settings this graph's block put in force
            ctx = setContexts[setStr]

            #  current graph title and ylabel for the plot
            grTitle = row['Value']
            yLabel = dft.loc['yLabel#'+setStr,'Value']

            #  graph set y hover text format 
            hfmt_y = '.4f' 
            if isinstance(dft.loc['yLabel#'+setStr,'Format'], str):
                hfmt_y = dft.loc['yLabel#'+setStr,'Format']

            #  determine if the rectangle tool is present
            #  this will be the case if in any line is using markers
            isMarkers = False

            #  category labels contributed by every enumeration trace in this
            #  set, in order, so one axis can carry several state signals
            setCategories = []

            # pack the graph data in
            #  * either a list to be used in the Graph Div
            #  * or in the relevant subplot 
            thisGraphData = []

            # run through all variables in the trace set
            for traceNum, value in enumerate(yVariableList):
                # identity the specific trace
                if 'yValue#'+setStr in value:

                    # add to plot set
                    thisGraphData.append(graphData[traceNum])

                    # check for usage of markers
                    # at least one trace with markers will trigger the rectangle tool
                    # with associated Rectangle Tool Selection Data box
                    if 'markers' in graphData[traceNum]['mode']:
                        isMarkers = True

                    # collect the category labels of any enumeration trace
                    for category in enumCatsList[traceNum] or []:
                        if category not in setCategories:
                            setCategories.append(category)


            # y axis: an enumeration set gets its codes relabelled with the
            # state names, so the reader sees 'Tracking' and not 1
            yAxisDict = {'title': yLabel, 'hoverformat': hfmt_y}
            if setCategories:
                yAxisDict['tickmode'] = 'array'
                yAxisDict['tickvals'] = list(range(len(setCategories)))
                yAxisDict['ticktext'] = setCategories
                yAxisDict['range'] = [-0.5, len(setCategories) - 0.5]

            # create dictionary with the layout and data
            figdict = {'layout':{'title': grTitle,
                                'xaxis':{'title': ctx['xlabel'], 'hoverformat': ctx['xformat']},
                                'yaxis':yAxisDict,
                                'clickmode': 'event+select',
                                'hovermode': 'x',           # set compare data on hover
                                'plot_bgcolor': backgroundColor,
                                },
                        'data':thisGraphData}

            # Plotly's default margins reserve about 100 px above and 80 px
            # below the plot area. On a short graph that leaves a thin strip
            # of data between two bands of white, so the compact layout
            # claims that space back: just enough for the title and the
            # axis labels.
            # The title is drawn inside the plotting area rather than in a
            # band above it: 'paper' places it against the top of the axes,
            # so it costs no page height at all.
            if pageDensity == 'compact':
                figdict['layout']['margin'] = {'l': 60, 'r': 20,
                                               't': 8, 'b': 38}
                figdict['layout']['title'] = {'text': grTitle,
                                              'font': {'size': 13},
                                              'xref': 'paper', 'yref': 'paper',
                                              'x': 0.01, 'xanchor': 'left',
                                              'y': 1.0, 'yanchor': 'top',
                                              'pad': {'t': 4, 'l': 4}}
       
            #  store the id of this set - to be used in callback function generation
            #  we mark all relevant Divs with this string
            grID = graph+setStr
            grList.append(grID)

            # One row per graph: the graph on the left, its click and
            # selection readouts stacked in a narrow column on the right.
            # Keeping them side by side is what lets successive graphs sit
            # almost touching, since the readouts no longer consume a band
            # of page width-wise between one graph and the next.
            # Height needs a CSS unit. It used to be emitted as a bare
            # string, e.g. '240', which is not valid CSS: the browser
            # dropped it and every graph silently fell back to Plotly's
            # 450 px default, whatever the configuration asked for.
            graphStyle = {'padding': 0 if pageDensity == 'compact' else 20}
            try:
                graphStyle['height'] = f"{int(float(ctx['height']))}px"
            except (TypeError, ValueError):
                pass

            # the common-x class is what assets/graphsync.js keys on to
            # decide which graphs share an x range
            rowClass = 'row graph-row common-x' if commonX else 'row graph-row'

            # keep the traces so a click on any graph of a commonX group
            # can report every graph's values at that x
            self.graphTraces[grID] = [
                (trace.get('name', ''), trace['x'], trace['y'],
                 trace.get('text'))
                for trace in thisGraphData]

            thisDivList.append(
                html.Div(className=rowClass, children=[
                    html.Div(className='nine columns', children=[
                        dcc.Graph
                        (
                            id=grID,
                            figure=figdict,
                            style=graphStyle,
                        )
                    ]),
                    html.Div(className='three columns', children=[
                        self.generateFeedbackBoxes(grID, isMarkers, xmin, xmax,
                                                   *traceYExtent(thisGraphData))
                    ]),
                ])
            )

            if toDisk:
                self.graphToDisk(figdict, f'{grDir}/{graph}#{setStr}')

        # 5) Div bottom text: if supplied, append the sheet bottom text
        if 'GraphBottom' in dft.index:
            thisDivList.append(
                html.Div([dcc.Markdown(id=f'botMarkdown-{graph}',children=dft.loc['GraphBottom','Value'])])
            )

        # 6) Div page footer: append the footer text at the bottom of the graph
        thisDivList.append(
            html.Div([dcc.Markdown(id=f'footerMarkdown-{graph}',children=pagebottom)]),
        ) 

        # 7) Div with license logos
        import base64
        encoded_image = base64.b64encode(open('icons/logoSet2long.png', 'rb').read())
        thisDivList.append(
            html.Div([
                        html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                        height=50)
                    ], 
                    style = {'text-align':'right'}
                    )
        )

        # every graph of a commonX tab knows the whole group it belongs to
        if commonX:
            for grID in grList:
                self.commonXGroups[grID] = list(grList)

        return thisDivList, grList, xmin, xmax

    ##########################################
    def prepareGraphs(self):
        """
        Controls preparation of all required graph sets

        Args:
            | None. 

        Returns:
            | None.

        """
        #  declare global to enable changing
        global divSets
        global graphTabs
        global graphList
        global sliderMinValues
        global sliderMaxValues

        # divSets to be used when constructing the page
        # each entry in this list is a different tab containing several graphs
        divSets = []

        # list with the names of the tabs on the page
        graphTabs = []

        #  List of all the unique graph names for which we need to register callback functions
        graphList = []

        # slider limits
        sliderMinValues = []
        sliderMaxValues = []
        
        # make a list of all possible graph tabs and graphs sets in dataframe dfg
        # to be used in generating all possible callbacks
        global allTabs, allTabUsedIdx
        allTabs = dfPlotterConfig['Graph'].unique()
        allTabUsedIdx = [-1] * len(allTabs)

        global allGraphs
        allGraphs = []

        # counter for active tabs
        tabIndex = 0

        # for each graph tab in the input data, i.e. each sheet starting with 'graph-'
        for i, graphTab in enumerate(allTabs):

            # extract info for this graph set
            dft = dfPlotterConfig[(dfPlotterConfig['Graph']==graphTab)]        
            
            # extract all graph names for this tab    
            titleRows = dft[(dft['Variable']=='Title')]
            for index, row in titleRows.iterrows():
                setStr = str(index).split('#')[1]
                grID = graphTab+setStr
                allGraphs.append(grID)
            
            # First check exclude flag
            toInclude = True
            if 'Include' in dft.index:
                if not np.isnan(dft[(dft['Variable']=='Include')]['Value'].values[0]):
                    toInclude = dft[(dft['Variable']=='Include')]['Value'].values[0]
            
            # collect data and build the data for the sheet
            if toInclude:
                allTabUsedIdx[i] = tabIndex
                tabIndex = tabIndex + 1

                divSet, grList, xmin, xmax = self.makeGraphSet(dft, graphTab)

                divSets.append(divSet)
                graphList.append(grList)
                sliderMinValues.append(xmin)
                sliderMaxValues.append(xmax)
                graphTabs.append(graphTab.split('-')[1])

    ##########################################
    def makePage(self):
        """
        Create the page to be displayed in the browser

        Args:
            | None.

        Returns:
            | page (html Div): created page.

        """

        # each entry in this list is a different tab containing several graphs
        lsttabs = []

        # create each tab in the page
        # lsttabs will now have for each active tab: label & value
        #    e.g. [Tab(id='RelativePosition', label='RelativePosition', value='Tab 0'), 
        #          Tab(id='Velocity', label='Velocity', value='Tab 1'), 
        #          Tab(id='xyPlot', label='xyPlot', value='Tab 2'), 
        #          Tab(id='MissilePosition', label='MissilePosition', value='Tab 3'), 
        #          Tab(id='Attitude', label='Attitude', value='Tab 4'), 
        #          Tab(id='gimbalFromxls', label='gimbalFromxls', value='Tab 5')]
        for tabNum, tabSet in enumerate(divSets):

            tabLabel = graphTabs[tabNum]

            # if we use callbacks only the tab is created, i.e. no data added
            # the graphs are only added to the tab when the user clicks on the tab
            # callbacks are preferred for large datasets 
            if self.useCallbacks:
                lsttabs.append(
                    dcc.Tab(value='Tab ' + str(tabNum), label=tabLabel, id=tabLabel))

            # no callbacks, add the graphs on all tabs
            else:
                lsttabs.append(
                    dcc.Tab(value='Tab ' + str(tabNum), label=tabLabel, id=tabLabel, children=[
                        *tabSet,
                    ]))

        # create the page to be rendered in the browser, using all active tabs as requested via config
        # the density class drives the spacing rules in assets/density.css
        page = html.Div(
        [
            dcc.Tabs(
                id='tabs',
                value='Tab 0',
                children=[
                # following is a list of all tabs with their content
                *lsttabs,
                ]
            ),

            html.Div(id='tabs-content'),
        ],
        className=f'density-{pageDensity}'
        )

        # the page now has for example:
        # Div([Tabs(
        #       children=[
        #         Tab(label='RelativePosition', value='Tab 0'), 
        #         Tab(label='Velocity', value='Tab 1'), 
        #         Tab(label='MissilePosition', value='Tab 2'), 
        #         Tab(label='gimbalFromxls', value='Tab 3')], 
        #       id='tabs', value='Tab 0'
        #      ),
        #      Div(id='tabs-content')
        #    ])
        # 
        #  If we are using callbacks to populate the tabs, we pass as input: value of the clicked tab, i.e. 
        #    Input(component_id='tabs', component_property='value'), value is one of Tab 0, Tab 1, Tab 2 or Tab 3
        #  and the page gets the output from the callback:
        #    Output(component_id='tabs-content', component_property='children'), passing back the graph set for this tab divSets[tabNum]
        #  This set includes all headers, graphs & footers for the selected tab

        return page

    ##########################################
    def loadConfig(self, configfile):
        """
        Loads the graph configuration from an .xlsx or .json file

        Args:
            | configfile (string): filename of the file that defines the plots.

        Returns:
            | None.

        """

        # read the config file, whichever of the two formats it is in
        dfHeader, sheets = readConfigTables(configfile)

        # header dataframe, i.e the data on the 'header' tab in the xlsx file
        global dfPlotterHeader
        dfPlotterHeader = dfHeader.set_index('Variable')
        masterDataFile =  dfPlotterHeader.loc['Datafile','Value']

        # page density: 'compact' packs the widgets together, 'comfortable'
        # restores the original roomier spacing. Compact is the default.
        global pageDensity
        pageDensity = 'compact'
        if 'Density' in dfPlotterHeader.index:
            requested = str(dfPlotterHeader.loc['Density','Value']).strip().lower()
            if requested in ('compact', 'comfortable'):
                pageDensity = requested
            else:
                print(f"Density '{requested}' not recognised, using 'compact'. "
                      f"Valid values are 'compact' and 'comfortable'.")

        # dataframe to contain ALL the sheets' info
        global dfPlotterConfig
        dfPlotterConfig = pd.DataFrame()

        for shtnum,(sheetname,dft) in enumerate(sheets.items()):
            dft = dft.copy()
            # add info to identify the lines associated with this sheet
            dft['Graph'] = sheetname
            dft['ShtNum'] = shtnum
            dft['Index'] = dft['Variable']

            # Check the file to be used and
            # determine the number of graphs on this tab
            i = 0
            theSet = -1
            for index,row in dft.iterrows():
                if 'Datafile' in row['Variable']:
                    if dft.loc[index,'Value'] == 'master':
                        dft.loc[index,'Value'] = masterDataFile
                # a yValue row may name its own data file in the Datafile
                # column, which is how one tab carries several sample rates
                if dft.loc[index,'Datafile'] == 'master':
                    dft.loc[index,'Datafile'] = masterDataFile
                if 'Title' in row['Variable']:
                    theSet = theSet + 1
                    dft.loc[index,'Index'] = f"{row['Variable']}#{theSet:03d}"
                if 'yLabel' in row['Variable']:
                    dft.loc[index,'Index'] = f"{row['Variable']}#{theSet:03d}"
                    i = 0
                if 'yValue' in row['Variable']:
                    dft.loc[index,'Index'] = f"{row['Variable']}#{theSet:03d}-{i:03d}"
                    i = i + 1

            # make 'Index' column the index
            dft = dft.set_index('Index')
            # append this sheet to the master data frame
            dfPlotterConfig = pd.concat([dfPlotterConfig, dft])

###########################################################################
    def readdatafile(self, filename):
        """Read a comma or space separated data file into a dataframe.

        OSSIM data files can use comma or space separated data files.
        These files normally have one comma or one or more space separators. 
        The header line for space separated files start with a percentage to allow
        loading of the file with Matlab. There might be a space between the % en the 
        name of the first column, e.g. '%time' or '% time'. Using pandas.read_csv() 
        will not work if a space is present between the % and the column name.

        This function tries to read the different styles of files into a 
        Pandas dataframe, removing the percentage and any spaces before the first column 
        heading (rest as in data file).
            
        The number of header lines may vary, discard all lines that starts with %
        using the last as header.
            
        Args:
            | filename (string): csv filename. 

        Returns:
            | dfData (pandas.DataFrame): dataframe with loaded data.
        
        """
        # empty dataframe
        dfData = None
            
        # determine if there are lines to skip before header line
        skiprows = 0
        headerDone = False
        with open(filename,'r') as fin:
            while not headerDone:
                line=fin.readline()
                if '%' in line:
                    skiprows = skiprows + 1
                else:
                    headerDone = True
                    
        # leave the last line as header  
        skiprows = skiprows - 1
    
        # identify the file type
        with open(filename,'r') as fin:
            line = fin.readline()
            if len(line) > 0:
                matlab = True if '%' in line else False
                matlabspace = True if ' ' == line[1] else False
                comma = True if ',' in line else False
            else:
                print('File {} has no contents, returning None'.format(filename))
                return None
        
        # load the data if matlab or space separated

        if matlab or '.plt' in filename:
            df = pd.read_csv(filename, sep=r'\s+',engine='python',header=0,skiprows=skiprows)
            
            # the leading '% ' in header messes up the column headings, fix:
            if matlabspace:
                dfData = df[df.columns[:-1]]
                dfData.columns = df.columns[1:]
            else:
                dfData = df

            if '%Time' in dfData.columns.values[0]:
                dfData['Time'] = dfData['%Time']
                dfData.drop(['%Time'], axis=1,inplace=True)
            if '%CurrentSimTime' in dfData.columns.values[0]:
                dfData['CurrentSimTime'] = dfData['%CurrentSimTime']
                dfData.drop(['%CurrentSimTime'], axis=1,inplace=True)
            if '%t' in dfData.columns:
                dfData['t'] = dfData['%t']
                dfData.drop(['%t'], axis=1,inplace=True)
                
        # load comma separated data
        if comma or '.csv' in filename:
            dfData = pd.read_csv(filename, sep=',',header=0)

        # load spectral data
        if '.scd' in filename or '.spc' in filename:
            dfData = pd.read_csv(filename, delimiter=r'\s+',header=None)
            if dfData.shape[1] == 3:
                dfData.columns=['wavelen','wavenum','trans']
            else:
                dfData.columns=['wavelen','wavenum','emis','trans','refl']

        return dfData

    ##########################################
    def loadData(self, datadir=None):
        """
        Load all the data from all files supplied

        Args:
            | datadir (string): directory to resolve relative data file names
                             against, or None to use the working directory.

        Returns:
            | success (bolean): True if the file load was successful.

        """

        # get data filenames from all sheets: the per-sheet Datafile rows,
        # plus any per-trace override named in the Datafile column
        datafilenames = list(
            dfPlotterConfig[(dfPlotterConfig['Variable']=='Datafile')]['Value'].unique())
        if 'Datafile' in dfPlotterConfig.columns:
            for override in dfPlotterConfig['Datafile'].dropna().unique():
                if (isinstance(override, str) and override.strip()
                        and override not in datafilenames):
                    datafilenames.append(override)

        self.datafiles = {}
        self.dateCreated = str(datetime.date.today())

        # run through all unique file names

        success = True
        for datafilename in datafilenames:

            # A reference may carry a '#group' fragment naming one rate group
            # inside a multi-rate JSON file. Resolve the file part against
            # datadir, but keep the whole reference, fragment included, as the
            # dictionary key: prepareGraphs looks the frame up by exactly the
            # string the config carries, and two groups of one file are two
            # separate frames.
            filepart, group = splitDataRef(datafilename)

            datapath = filepart
            if datadir is not None and not os.path.isabs(filepart):
                datapath = os.path.join(datadir, filepart)

            if os.path.isfile(datapath):

                # determine what type of file is this by looking at the file extension
                extension = os.path.splitext(datapath)[1]

                # matlab format files
                # note that here we rely on the Denel GTV matlab file which has 
                #  * the data stored in 'DATA'
                #  * the data column names in 'NAM'
                #  * the time variable is called 'TIME'
                # if other applications need matlab file capability this must be generalised
                if 'mat' in extension:

                    # load the gtv telemetry data in matlab format file
                    # scipy reads in structures as structured numpy arrays of dtype object
                    # returns a dictionary with variable names as keys, and loaded matrices as values.
                    from scipy.io import loadmat
                    dataMat = loadmat(datapath)

                    # create the dataframe
                    self.datafiles[datafilename] = pd.DataFrame(dataMat['DATA'], columns=dataMat['NAM'])

                    # set beginning of data set as time zero
                    self.datafiles[datafilename]['TIME'] = self.datafiles[datafilename]['TIME'] - self.datafiles[datafilename]['TIME'].values[0]
                    
                    # get date 
                    self.dateCreated = dataMat['Date_Created'][0]

                # Excel data files
                # top row is data column names
                # Only the first sheet is loaded
                # To be generalised to specify the sheet from the config file
                elif 'xls' in extension:
                    self.datafiles[datafilename] = pd.read_excel(datapath, index_col=None)

                # JSON files: either one record array, or an object of named
                # groups for multi-rate data. See readJsonData.
                elif 'json' in extension:
                    self.datafiles[datafilename] = readJsonData(datapath, group)

                #  csv files
                #  top line is column names
                else:
                    self.datafiles[datafilename] = self.readdatafile(datapath)
                    # pd.read_csv(datapath, sep="\s+|,|;", index_col=None,engine='python')

            else:
                print(f'Data file {datapath} for plotting not found, please provide a valid file name in the config file!\n ')
                success = False

        return success

    ##########################################
    #
    def run_dash(self, pageLayout, port, pagetitle=None):
        """
        Initiate the Dash server and serve the page

        Args:
            | pageLayout (dash layout): info the be served in Plotly data format
            | port (int): port number to be used
            | pagetitle (string): browser tab title, or None for the Dash default

        Returns:
            | None.

        """
        # start a dash app, which also starts a Flask server
        # it is important to set the name parameter of the Dash instance to the value __name__, 
        # so that Dash can correctly detect the location of any static assets inside an assets 
        # directory for this Dash app
        # this must be global to stay in scope in applications that use the plotter as a module
        global dashApp
        dashApp = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                            assets_folder=resource_path('assets'),
                            title=pagetitle if pagetitle else 'Dash')

        # override security restrictions: allow the serving of local pages
        dashApp.css.config.serve_locally = True
        dashApp.scripts.config.serve_locally = True
        dashApp.layout = pageLayout

        # We have a dynamic layout, so we can ignore the exception
        dashApp.config['suppress_callback_exceptions']=True

        # generate all callback functions for all possible graph sets & tabs
        self.setupCallbacks()

        # run the server on the specified port
        # set debug mode to False, no hot reloading
        # From https://dash.plot.ly/devtools
        # dev_tools features are activated by default when you run the app with app.run_server(debug=True)
        # By default, Dash includes "hot-reloading". This means that Dash will automatically refresh your browser 
        # when you make a change in your Python or CSS code.
        dashApp.run(debug=False, port=port, use_reloader=False)

    def setupCallbacks(self):
        """
        Generate all callback functions required

        Args:
            | None.

        Returns:
            | None.
            
        """
        # prepare for hover labels accross shared axes
        #   * can only be done when doing subplots
        #   * used the tricks from here
        #        https://github.com/plotly/plotly.js/issues/2114#issuecomment-535259328
        #  The main tricks are
        #    1) dynamically get plot names
        #    2) use visdcc.Runjs to reload the javasript on graph change, to reattach the event handler to 
        #       the re-created plot. 
        # 
        # generate javascript strings to run in the render callback
        # the plotid in this javascript string will be replaced with the graph id's
        JS_STR_template = '''

            var plotid = 'theplotname'
            var plot = document.getElementById(plotid)

            plot.on(
            'plotly_hover',
            function (eventdata) {
                Plotly.Fx.hover(
                plotid,
                { xval: eventdata.xvals[0] },
                Object.keys(plot._fullLayout._plots) // ["xy", "xy2", ...]
                );
            });
            '''
            
        jsString = []
        for gr in allTabs:
            theGraph = str(gr)
            gr_js = JS_STR_template.replace('theplotname',theGraph)
            jsString.append(gr_js)

        # ----------------------------------------------------------------------------------------------
        # now define all the callback functions:

        # It seems that with the latest python modules, the visdcc module is not compatibl any more
        # We need to solve this issue
        # For the time being the subplot functionality will be disabled
        # callback used for rendering of tabs
        # @dashApp.callback(
        #     [Output('tabs-content', 'children'),
        #     Output('hover-js', 'run'),  # <-- add this to get hover on all subplot traces
        #     ],
        #     [Input('tabs','value')]
        #     # INPUTS
        # )
        # def render_content(tab):
        # # def render_content(tab, *args):
        #     tabNum = int(tab.split(' ')[1])
        #     # get the correct tab number for the js_str in complete list
        #     jsIndex = allTabUsedIdx.index(tabNum)
        #     js_str = jsString[jsIndex]
        #     print(f'js_string = {js_str}\n')
        #     return [divSets[tabNum]], js_str
            
        @dashApp.callback(
            [Output('tabs-content', 'children')],
            [Input('tabs','value')]
        )
        def render_content(tab):
            tabNum = int(tab.split(' ')[1])
            return [divSets[tabNum]]
    
        # generate data clicked and selected callback functions for all possible graphs in the config
        # i.e. subplots as well as individual graph sets
        # must be able to handle changed config input from the user
        for gr in itertools.chain(allTabs,allGraphs):
            theGraph = str(gr)

            # initialise the clicked data storage
            # current click index, click1, click2, range
            data = [1, [0,0], [0,0], [0,0]]
            self.clickedData[theGraph] = data

            # ---- x-range entry -------------------------------------------
            # Apply patches only the axis range into the figure already in the
            # browser rather than returning a new one, so the data is not sent
            # again; on a 19000-point trace that matters.
            #
            # On a commonX tab every graph listens to every graph's buttons, so
            # one entry zooms the whole tab. _group is a default argument and
            # not a closure, because the loop variable would otherwise be
            # rebound long before the callback ever fires.
            xGroup = self.commonXGroups.get(theGraph, [theGraph])

            @dashApp.callback(
                Output(theGraph, 'figure'),
                [Input('xapply-' + sibling, 'n_clicks') for sibling in xGroup]
                + [Input('xreset-' + sibling, 'n_clicks') for sibling in xGroup],
                [State('xstart-' + sibling, 'value') for sibling in xGroup]
                + [State('xend-' + sibling, 'value') for sibling in xGroup]
                + [State('ystart-' + sibling, 'value') for sibling in xGroup]
                + [State('yend-' + sibling, 'value') for sibling in xGroup],
                prevent_initial_call=True
            )
            def apply_ranges(*args, _group=xGroup, _self=theGraph):
                fired = dash.callback_context.triggered
                if not fired or fired[0]['value'] is None:
                    return dash.no_update

                widgetId = fired[0]['prop_id'].split('.')[0]
                action, _, sourceGraph = widgetId.partition('-')
                if sourceGraph not in _group:
                    return dash.no_update

                # y belongs to the graph whose boxes were used and to no
                # other: the graphs of a commonX tab have their own y scales,
                # and often their own units, so one graph's y range is
                # meaningless on another. x is the only axis they share.
                mine = sourceGraph == _self

                patched = Patch()
                if action == 'xreset':
                    patched['layout']['xaxis']['autorange'] = True
                    if mine:
                        patched['layout']['yaxis']['autorange'] = True
                    return patched

                # args arrive as inputs then states: 2n n_clicks, then n of
                # each of xstart, xend, ystart, yend
                count = len(_group)
                which = _group.index(sourceGraph)
                xStart, xEnd = args[2 * count + which], args[3 * count + which]
                yStart, yEnd = args[4 * count + which], args[5 * count + which]

                # The boxes are plain text inputs, so that no browser draws
                # spinner arrows on them. The values therefore arrive as
                # strings, and anything that is not a number is ignored
                # rather than raising.
                def number(value):
                    try:
                        return float(str(value).strip())
                    except (TypeError, ValueError):
                        return None

                def span(start, end):
                    low, high = number(start), number(end)
                    if low is None or high is None or low >= high:
                        return None
                    return [low, high]

                changed = False
                xSpan = span(xStart, xEnd)
                if xSpan is not None:
                    patched['layout']['xaxis']['autorange'] = False
                    patched['layout']['xaxis']['range'] = xSpan
                    changed = True

                ySpan = span(yStart, yEnd) if mine else None
                if ySpan is not None:
                    patched['layout']['yaxis']['autorange'] = False
                    patched['layout']['yaxis']['range'] = ySpan
                    changed = True

                return patched if changed else dash.no_update

            # On a commonX tab every graph's readout listens to every graph in
            # the group, so one click fills them all at the same x. The State
            # carries the id of the graph this particular box belongs to,
            # which is also what keeps the loop variable out of the closure.
            if theGraph in self.commonXGroups:

                @dashApp.callback(
                    Output('click-'+theGraph, 'children'),
                    [Input(sibling, 'clickData')
                     for sibling in self.commonXGroups[theGraph]],
                    [State(theGraph, 'id')]
                )
                def display_common_click_data(*args):
                    targetId = args[-1]
                    fired = dash.callback_context.triggered
                    if not fired or not fired[0]['value']:
                        return 'none clicked'
                    clicked = fired[0]['value']
                    return self.commonClickMessage(
                        targetId, clicked['points'][0]['x'])

            else:

                @dashApp.callback(
                  Output('click-'+theGraph, 'children'), # display box id and children
                  [Input(theGraph, 'clickData')],   # graph id and clickdata
                  [State(theGraph,'id')]
                )
                def display_click_data(clickData, id):
                  msg = 'none clicked'
                  if clickData:
                      # get clicked data
                      x = clickData['points'][0]['x']
                      y = clickData['points'][0]['y']

                      # Index of new click data
                      index = self.clickedData[id][0]

                      # store the new data here
                      self.clickedData[id][index][0] = x
                      self.clickedData[id][index][1] = y

                      # Calc the delta and set the index to be valid for next click
                    
                      indCur = index
                      if index == 1:
                          index = 2
                      else:
                          index = 1
                      indexPrev = index
                      self.clickedData[id][0] = index

                      # calc delta
                      self.clickedData[id][3][0] = abs(self.clickedData[id][indCur][0] - self.clickedData[id][indexPrev][0])
                      self.clickedData[id][3][1] = abs(self.clickedData[id][indCur][1] - self.clickedData[id][indexPrev][1])

                      msg =  (
                              f'Previous [x, y]: [{self.clickedData[id][indexPrev][0]:.6f}, {self.clickedData[id][indexPrev][1]:.6f}]\n'  
                              f'Current [x, y]: [{self.clickedData[id][indCur][0]:.6f}, {self.clickedData[id][indCur][1]:.6f}]\n'  
                              f'Range [x, y]: [{self.clickedData[id][3][0]:.6f}, {self.clickedData[id][3][1]:.6f}]' 
                      )

                  return msg 

            # As with the click readout, a commonX tab fans the selection out:
            # a rubber-band on any graph fills every selection box on the tab.
            # Only the x window travels. The graphs have their own y scales and
            # often their own units, so a y range selected on one means nothing
            # on another; each graph reports its own y extent inside that x
            # window instead.
            if theGraph in self.commonXGroups:

                @dashApp.callback(
                    Output('select-'+theGraph, 'children'),
                    [Input(sibling, 'selectedData')
                     for sibling in self.commonXGroups[theGraph]],
                    [State(theGraph, 'id')]
                )
                def display_common_selected_data(*args):
                    targetId = args[-1]
                    fired = dash.callback_context.triggered
                    if not fired:
                        return 'none selected'
                    bounds = selectionBounds(fired[0]['value'])
                    if bounds is None:
                        return 'none selected'
                    return self.commonSelectMessage(targetId, bounds[0])

                continue

            @dashApp.callback(
                Output('select-'+theGraph, 'children'), # display box id and children
                [Input(theGraph, 'selectedData')]   # graph id and selectedData
            )
            def display_selected_data(selectedData):

                msg = 'none selected'

                bounds = selectionBounds(selectedData)

                if bounds is not None:

                    xRange, yRange = bounds

                    x1eft = xRange[0]
                    xright = xRange[1]
                    dx = abs(xright - x1eft)

                    ytop = yRange[1]
                    ybottom = yRange[0]
                    dy = abs(ybottom - ytop)
                    
                    msg = (
                        f'Top left [x, y]: [{x1eft:.6f}, {ytop:.6f}]\n'  
                        f'Bottom right [x, y]: [{xright:.6f}, {ybottom:.6f}]\n'  
                        f'Range in [x, y]: [{dx:.6f}, {dy:.6f}]' 
                    )

                return msg 

        # time slider callback for each tab - display selected values of the slider
        for gr in allTabs:
            theGraph = str(gr)

            @dashApp.callback(
                Output('output-container-xSlider-'+ theGraph, 'children'),
                [Input('xSlider-'+theGraph, 'value'),
                 Input('submit-button-'+theGraph, 'n_clicks'), 
                ],    
                [State('tabs', 'value'),
                 State('minVal-'+theGraph, 'value'), State('maxVal-'+theGraph, 'value'),
                ]             
            )
            def process_xSlider_data(value, nclicks, tab, mini, maxi):
                # tab number in the current page layout
                tabNum = int(tab.split(' ')[1])
                graphSetName = 'graph-'+graphTabs[tabNum]
                # select the graph data
                dft = dfPlotterConfig[(dfPlotterConfig['Graph']==graphSetName)] 
                # determine which input triggered the callback
                ctx = dash.callback_context
                clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # Get slider limits from input fields
                if 'submit' in clicked_id:
                    start = mini
                    if start < sliderMinValues[tabNum]:
                        start = sliderMinValues[tabNum]
                    end = maxi
                    if end > sliderMaxValues[tabNum]:
                        end = sliderMaxValues[tabNum] 
                    value[0] = start
                    value[1] = end

                # update the graph set
                global divSets
                divSets[tabNum], _, _, _ = self.makeGraphSet(dft, graphSetName, value[0], value[1]) 
                msg = f'Selected range [{value[0]:.6f}, {value[1]:.6f}]'
                return msg
            
            @dashApp.callback(
                [Output('xSlider-'+theGraph, 'value'), 
                 Output('minVal-'+theGraph, 'value'), 
                 Output('maxVal-'+theGraph, 'value'), 
                ],
                [Input('resetSlider-'+theGraph, 'n_clicks')],
                [State('tabs', 'value')] 
            )
            def reset_xSlider(nclicks, tab):
                tabNum = int(tab.split(' ')[1])
                low = sliderMinValues[tabNum]
                hi = sliderMaxValues[tabNum]
                limit = [low, hi]
                return limit, '', ''

    ##########################################
    def runPlotter(self, port, configfile, cback = True, flaskServerRunning=False,
                   datadir=None, pagetitle=None):
        """
        main control plotter function

        Args:
            | configfile (string): configuration file defining the graphs.
            | cback (bolean): use callbacks to populate the data on the tabs (default True)
                             (recommended for large data sets)
            | flaskServerRunning (bolean): entry state of the flask server (default False)
            | datadir (string): directory to resolve relative data file names against,
                             or None to resolve them against the working directory
            | pagetitle (string): browser tab title, or None for the Dash default

        Returns:
            | flaskServerRunning (bolean): running state of flask server at the end of this function.
        """

        # set callbacks flag as requested
        self.useCallbacks = cback

        self.loadConfig(configfile)

        # load all data to be available in the class
        # all the data files, but only once into a dict with filename as key

        if self.loadData(datadir):
            # prepare all required graph sets
            self.prepareGraphs()

        
            # now create the page we want to render
            pageLayout = self.makePage() 

            # The Python threading API defines two kinds of threads: daemons and non-daemons. 
            # A Python program is defined to end when all non-daemons are done. 
            # So, if your thread is infinite, which they often are, they will never be done and your program is hard to exit.
            # Make the thread a daemon, i.e. process running in the background, so that we can easily kill the program.
            # A daemon thread will shut down immediately when the program exits. One way to think about these definitions is to 
            # consider the daemon thread a thread that runs in the background without worrying about shutting it down.

            # the first entry to this function starts the thread as a daemon
            # this means that the user can close the dash window, change the configuration in the
            # setup file, open a new dash window, then only render the page with the updated information 
            # as implemented in the else section here.
            if not flaskServerRunning:
                threading.Thread(target=self.run_dash,
                                 args=(pageLayout, port, pagetitle),
                                 daemon=True).start()
                flaskServerRunning = True
            else:
                # serve new page
                dashApp.layout = pageLayout

        return flaskServerRunning       
    
##########################################
# when run on the commandline this code will be executed
#
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description='dash-lineplot: Plotly Dash line plotting utility.')
    parser.add_argument('-f', '--configfile', default='./dash-config.xlsx',
                        help='Plot configuration file (default: ./dash-config.xlsx).')
    parser.add_argument('-p', '--port', type=int, default=8050,
                        help='Port for the local Flask server (default: 8050).')
    parser.add_argument('-d', '--datadir', default=None,
                        help='Directory holding the data files named in the '
                             'configuration. Relative data file names are '
                             'resolved against it.')
    args = parser.parse_args()

    pagetitle = readPageTitle(args.configfile)

    # always use callbacks: required for the slider, click data and the
    # rectangle tool to work
    dashlineplotter = DashLinePlot()
    serving = dashlineplotter.runPlotter(args.port, args.configfile, cback=True,
                                         datadir=args.datadir, pagetitle=pagetitle)

    # loadData returns False when a data file named in the config is missing,
    # in which case no page was ever built and no server was started.
    if not serving:
        print('\nnothing served: a data file named in the configuration was '
              'not found. Fix the Datafile entries, or pass --datadir.\n')
        sys.exit(1)

    # run_dash runs in a daemon thread, so the main thread has to stay alive
    # for the server to keep serving.
    print(f'\nserving on http://127.0.0.1:{args.port}/   (Ctrl+C to stop)\n')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print('\nstopped')
