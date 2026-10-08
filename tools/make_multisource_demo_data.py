"""
Generate the dummy data plotted by multisource-example.json.

Three sources record the same two quantities, value1 and value2, but each
names its time column differently and samples on its own grid, as files
from different simulations or instruments do:

    data/multisource-a.json   't'               0.1 s steps from 0 s
    data/multisource-b.json   'time'            0.25 s steps from 0.05 s
    data/multisource-c.csv    'CurrentSimTime'  0.5 s steps from 0 s

Each source differs slightly in gain and phase, so the lines on a graph
are distinguishable. Nothing is random, so the files are the same on every
run.

Usage:
    python tools/make_multisource_demo_data.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / 'data'


def signals(t, gain, lag, tau):
    return {
        'value1': np.round(gain * np.sin(2 * np.pi * 0.2 * (t - lag)), 6),
        'value2': np.round(gain * (1 - np.exp(-t / tau)), 6),
    }


def main():
    tA = np.round(np.arange(201) * 0.1, 3)
    a = pd.DataFrame({'t': tA, **signals(tA, 1.0, 0.0, 4.0)})
    a.to_json(DATA / 'multisource-a.json', orient='records', indent=1)

    tB = np.round(0.05 + np.arange(81) * 0.25, 3)
    b = pd.DataFrame({'time': tB, **signals(tB, 0.9, 0.3, 5.0)})
    b.to_json(DATA / 'multisource-b.json', orient='records', indent=1)

    tC = np.round(np.arange(41) * 0.5, 3)
    c = pd.DataFrame({'CurrentSimTime': tC, **signals(tC, 1.1, -0.2, 3.0)})
    c.to_csv(DATA / 'multisource-c.csv', index=False, lineterminator='\n')

    for name, frame in [('a', a), ('b', b), ('c', c)]:
        print(f'multisource-{name}: {len(frame)} rows, columns {list(frame.columns)}')


if __name__ == '__main__':
    main()
