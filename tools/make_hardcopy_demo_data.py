"""
Generate the dummy data plotted by hardcopy-example.json.

Writes data/hardcopy-demo.csv: a Time column, 0 to 20 s at 0.01 s, and
twelve synthetic signals of different shapes, so that a page of many small
graphs is easy to tell apart at a glance. The noise uses a fixed seed, so
the file is the same on every run.

Usage:
    python tools/make_hardcopy_demo_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUTFILE = Path(__file__).resolve().parents[1] / 'data' / 'hardcopy-demo.csv'


def main():
    t = np.round(np.arange(0, 2001) * 0.01, 2)
    rng = np.random.default_rng(1)

    df = pd.DataFrame({
        'Time': t,
        'Sine1Hz': np.sin(2 * np.pi * 1 * t),
        'Sine3Hz': np.sin(2 * np.pi * 3 * t),
        'Sine7Hz': np.sin(2 * np.pi * 7 * t),
        'Cosine2Hz': np.cos(2 * np.pi * 2 * t),
        'Ramp': t / 20,
        'Square': np.sign(np.sin(2 * np.pi * 0.5 * t)),
        'Step': (t >= 5).astype(float),
        'Noise': rng.normal(0, 1, t.size),
        'Sawtooth': (t % 2) / 2,
        'Damped': np.exp(-t / 5) * np.sin(2 * np.pi * 1.5 * t),
        'Chirp': np.sin(2 * np.pi * (0.1 + 0.1 * t) * t),
        'Triangle': 2 * np.abs((t % 4) / 4 - 0.5),
    })
    df.to_csv(OUTFILE, index=False, float_format='%.6f')
    print(f'wrote {OUTFILE}: {len(df)} rows')


if __name__ == '__main__':
    main()
