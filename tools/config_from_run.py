"""
Generate a plot configuration for a directory of JSON telemetry files.

Each telemetry file becomes one tab, and each of its fields becomes one
graph on that tab, with the time column on the x axis. The result is a
first useful page for any run without hand-authoring a configuration; edit
it afterwards to group related signals onto shared axes.

Every file keeps its own time column. Nothing is merged across files and
nothing is resampled onto a common time base: the models that wrote these
files run at different periods, and a zero-order hold belongs to the model
that causes it, never to the plotting layer.

Usage:
    python tools/config_from_run.py <telemetry-dir> [-o out.json] [-x t]

Data files are named in the configuration without a directory, so serve the
result with the matching --datadir:

    python dash-lineplot.py --configfile out.json --datadir <telemetry-dir>
"""

import argparse
import json
import os
import sys

SKIP_FILES = {'manifest.json'}


def fieldsOf(records, xcolumn):
    """
    Split a record array's keys into plottable and non-plottable fields.

    A field is plottable if its first non-null value is numeric or boolean.
    String-valued fields, such as a mode enumeration, are reported rather
    than silently dropped.
    """
    plottable, skipped = [], []
    keys = []
    for record in records:
        for key in record:
            if key not in keys:
                keys.append(key)
    for key in keys:
        if key == xcolumn:
            continue
        value = next((r[key] for r in records if r.get(key) is not None), None)
        if isinstance(value, bool) or isinstance(value, (int, float)):
            plottable.append(key)
        else:
            skipped.append(key)
    return plottable, skipped


def sheetForFile(filename, records, xcolumn, height):
    """Build the row list for one telemetry file's tab."""
    plottable, skipped = fieldsOf(records, xcolumn)

    rows = [
        {'Variable': 'Height', 'Value': height},
        {'Variable': 'Datafile', 'Value': filename},
        {'Variable': 'xLabel', 'Value': 'Time [s]', 'Format': '.4f'},
        {'Variable': 'xValue', 'Value': xcolumn},
    ]

    model = os.path.splitext(filename)[0]
    period = ''
    if len(records) > 1:
        dt = records[1].get(xcolumn, 0) - records[0].get(xcolumn, 0)
        period = f', sampled every {dt * 1000.0:.0f} ms'
    note = f'### {model}\n\n{len(records)} samples{period}.'
    if skipped:
        note += ('\n\nNot plotted, because the values are not numeric: '
                 + ', '.join(f'`{s}`' for s in skipped) + '.')
    rows.append({'Variable': 'GraphTop', 'Value': note})

    for field in plottable:
        rows.append({'Variable': 'Title', 'Value': field})
        rows.append({'Variable': 'yLabel', 'Value': field, 'Format': '.6f'})
        rows.append({'Variable': 'yValue', 'Value': field})

    rows.append({'Variable': 'Include', 'Value': True})
    rows.append({'Variable': 'ToDisk', 'Value': False})
    rows.append({'Variable': 'UseSubplots', 'Value': False})
    return rows, plottable, skipped


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Generate a plot configuration for a telemetry directory.')
    parser.add_argument('datadir', help='Directory holding the JSON telemetry.')
    parser.add_argument('-o', '--output', default=None,
                        help='Output configuration filename (default: '
                             '<directory name>.json in the working directory).')
    parser.add_argument('-x', '--xcolumn', default='t',
                        help='Name of the time column (default: t).')
    parser.add_argument('--height', type=int, default=300,
                        help='Graph height in pixels (default: 300).')
    args = parser.parse_args(argv)

    if not os.path.isdir(args.datadir):
        print(f'not a directory: {args.datadir}')
        return 1

    filenames = sorted(f for f in os.listdir(args.datadir)
                       if f.endswith('.json') and f not in SKIP_FILES)
    if not filenames:
        print(f'no telemetry files found in {args.datadir}')
        return 1

    runName = os.path.basename(os.path.normpath(args.datadir))
    output = args.output
    if output is None:
        output = f'{runName}.json'

    sheets = {}
    totalGraphs = 0
    for filename in filenames:
        with open(os.path.join(args.datadir, filename), 'r',
                  encoding='utf-8') as fjson:
            records = json.load(fjson)
        if not records:
            print(f'  {filename}: empty, skipped')
            continue
        model = os.path.splitext(filename)[0]
        rows, plottable, skipped = sheetForFile(filename, records,
                                                args.xcolumn, args.height)
        sheets[f'graph-{model}'] = rows
        totalGraphs += len(plottable)
        note = f' (skipped {len(skipped)} non-numeric)' if skipped else ''
        print(f'  {filename}: {len(records)} samples, '
              f'{len(plottable)} graphs{note}')

    config = {
        'header': {
            'Pagetitle': f'{runName} telemetry',
            'PageTop': (f'# {runName}\n\nOne tab per model, one graph per '
                        'field. Each file keeps its own time base: the models '
                        'run at different periods, so the sample density '
                        'differs between tabs and is not interpolated.'),
            'PageBottom': f'Generated from `{args.datadir}`.',
            'Datafile': 'none',
        },
        'sheets': sheets,
    }

    with open(output, 'w', encoding='utf-8') as fjson:
        json.dump(config, fjson, indent=2)
        fjson.write('\n')

    print(f'\nwrote {output}: {len(sheets)} tabs, {totalGraphs} graphs')
    print(f'serve with:\n'
          f'  python dash-lineplot.py --configfile {output} '
          f'--datadir {args.datadir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
