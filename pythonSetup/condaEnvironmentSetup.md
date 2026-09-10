## conda dashplot environment

The `dashplot` conda environment is used for dash-plotly work. It is
defined by `environment.yml` in the repository root, which pins version
floors only and carries no `prefix`, so the same file solves on Linux and
on Windows.

Create and activate it:

    conda env create -f environment.yml
    conda activate dashplot

Update it after `environment.yml` changes:

    conda env update -f environment.yml --prune

Terminate with:

    conda deactivate

Remove it entirely:

    conda env remove --name dashplot

### What is in it, and what is not

The environment carries dash, plotly, pandas, numpy, openpyxl and scipy.
`scipy` is present only for `scipy.io.loadmat`, used by the Matlab data
reader, and is a lazy import that costs nothing until a `.mat` file is
actually read.

Three packages that earlier versions of this document installed are
deliberately absent:

- **PyQt5 / PyQtWebEngine**, and their PySide2 alternative. These wrapped
  the Flask server in a native desktop window. PySide2 has no support
  beyond Python 3.10, and the window offered nothing a browser does not.
  The page is now served to the system browser.
- **visdcc**, which provided synchronised hover across subplots. It is
  unmaintained, and its callback was already commented out in this script
  as broken before the package was removed.

### Exporting

Prefer `--no-builds --from-history` when refreshing the file. A plain
`conda env export` writes platform-specific build strings and an absolute
`prefix` naming your own home directory, which is what made the previous
`dashplotenv.yml` unusable anywhere but the machine that produced it:

    conda env export --no-builds --from-history -n dashplot

### Verified solve

On 2026-09-10, conda-forge solved `environment.yml` to Python 3.14.7,
Dash 4.4.1, Plotly 7.0.0, pandas 3.0.5, numpy 2.5.3, openpyxl 3.1.5 and
scipy 1.18.0.

Two of those are breaking changes relative to the 2022 environment, and the
script was updated for both: Dash 4 removed `run_server` in favour of
`run`, and pandas 3 no longer falls back to positional lookup when a Series
is indexed with an integer.
