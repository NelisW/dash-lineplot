"""
Shared test fixtures for dash-lineplot.

dash-lineplot.py has a hyphen in its name, so it cannot be imported by
name; it is loaded from its path instead. Building a page sets module
globals (divSets, graphTabs, graphList), which the tests read back from the
loaded module.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session')
def dlp():
    spec = importlib.util.spec_from_file_location('dashlineplot',
                                                  REPO / 'dash-lineplot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def build(dlp, monkeypatch):
    # data file references in the shipped configurations are relative to
    # the repository root
    monkeypatch.chdir(REPO)

    def _build(configfile):
        plotter = dlp.DashLinePlot()
        plotter.loadConfig(configfile)
        assert plotter.loadData()
        plotter.prepareGraphs()
        return plotter

    return _build


def walk(component):
    """Yield a component and every component below it."""
    if component is None or isinstance(component, (str, int, float)):
        return
    if isinstance(component, (list, tuple)):
        for child in component:
            yield from walk(child)
        return
    yield component
    yield from walk(getattr(component, 'children', None))


def props(component):
    return component.to_plotly_json()['props']
