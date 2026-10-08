import dash
import pytest

from conftest import REPO


@pytest.fixture
def wired(dlp, build):
    """Build a page, register its callbacks, and map each output to its inputs."""
    def _wired(configfile):
        plotter = build(configfile)
        dlp.dashApp = dash.Dash('test', assets_folder=str(REPO / 'assets'))
        dlp.dashApp.config['suppress_callback_exceptions'] = True
        plotter.setupCallbacks()

        callbacks = {}
        for key, entry in dlp.dashApp.callback_map.items():
            inputs = [f"{i['id']}.{i['property']}" for i in entry['inputs']]
            # a multi-output key reads '..a.p...b.p..'
            for output in key.strip('.').split('...'):
                callbacks[output] = inputs
        return callbacks

    return _wired


def test_unboxed_graph_has_no_callbacks(wired):
    cb = wired('hardcopy-example.json')
    for out in ['graph-many000.figure', 'click-graph-many000.children',
                'select-graph-many000.children', 'xstart-graph-many000.value']:
        assert out not in cb


def test_mixed_commonx_wiring(wired):
    cb = wired('hardcopy-example.json')
    boxed = ['graph-mixed000', 'graph-mixed001']
    expected = ([f'xapply-{g}.n_clicks' for g in boxed]
                + [f'xreset-{g}.n_clicks' for g in boxed])
    for g in ['graph-mixed000', 'graph-mixed003']:
        assert cb[f'{g}.figure'] == expected
    allSix = [f'graph-mixed00{k}.clickData' for k in range(6)]
    assert cb['click-graph-mixed000.children'] == allSix
    assert 'click-graph-mixed003.children' not in cb


def test_shipped_config_fully_wired(wired):
    cb = wired('commonx-example.json')
    for g in ['graph-linked000', 'graph-linked001', 'graph-linked002']:
        for out in [f'{g}.figure', f'click-{g}.children',
                    f'select-{g}.children', f'xstart-{g}.value']:
            assert out in cb
