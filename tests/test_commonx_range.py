import dash
import pytest

from conftest import REPO, walk, props


def figureOf(dlp, graphId):
    for tab in dlp.divSets:
        for component in walk(tab[0]):
            if props(component).get('id') == graphId:
                return props(component)['figure']
    raise KeyError(graphId)


def test_commonx_graphs_start_at_the_tab_extent(dlp, build):
    # markers pad Plotly's automatic range, lines do not; an explicit start
    # range keeps every graph of a commonX tab on the same x
    build('hardcopy-example.json')
    for k in range(6):
        xaxis = figureOf(dlp, f'graph-mixed00{k}')['layout']['xaxis']
        assert xaxis['range'] == [0.0, 20.0]
        assert xaxis['autorange'] is False


def test_other_tabs_keep_the_automatic_range(dlp, build):
    build('hardcopy-example.json')
    for graphId in ['graph-many000', 'graph-boundary002']:
        assert 'range' not in figureOf(dlp, graphId)['layout']['xaxis']


def test_tab_wrapper_carries_the_extent_for_commonx_only(dlp, build):
    build('hardcopy-example.json')
    extents = {props(tab[0])['data-tab-name']: props(tab[0])['data-x-extent']
               for tab in dlp.divSets}
    assert [float(v) for v in extents['mixed'].split(',')] == [0.0, 20.0]
    assert extents['many'] == '' and extents['boundary'] == ''


@pytest.fixture
def reset(dlp, build):
    """Press Reset beside one graph; return what the server patches into another.

    Goes through Dash's own update endpoint, so the registered callback runs
    exactly as it does for a browser.
    """
    def _reset(configfile, pressed, target):
        plotter = build(configfile)
        dlp.dashApp = dash.Dash('t', assets_folder=str(REPO / 'assets'))
        dlp.dashApp.layout = dash.html.Div()
        dlp.dashApp.config['suppress_callback_exceptions'] = True
        plotter.setupCallbacks()

        entry = dlp.dashApp.callback_map[f'{target}.figure']
        trigger = f'xreset-{pressed}'
        inputs = [{'id': i['id'], 'property': i['property'],
                   'value': 1 if i['id'] == trigger else None}
                  for i in entry['inputs']]
        state = [{'id': s['id'], 'property': s['property'], 'value': None}
                 for s in entry['state']]
        reply = dlp.dashApp.server.test_client().post('/_dash-update-component', json={
            'output': f'{target}.figure',
            'outputs': {'id': target, 'property': 'figure'},
            'inputs': inputs, 'state': state,
            'changedPropIds': [f'{trigger}.n_clicks']})
        assert reply.status_code == 200, reply.get_data(as_text=True)
        operations = reply.get_json()['response'][target]['figure']['operations']
        return {tuple(op['location']): op['params'].get('value')
                for op in operations if op['operation'] == 'Assign'}
    return _reset


def test_reset_on_a_commonx_tab_restores_the_extent(reset):
    # Reset beside a boxed graph reaches an unboxed sibling with the extent,
    # not an autorange, which would bring the marker padding back
    patch = reset('hardcopy-example.json', 'graph-mixed000', 'graph-mixed003')
    assert patch[('layout', 'xaxis', 'range')] == [0.0, 20.0]
    assert patch[('layout', 'xaxis', 'autorange')] is False


def test_reset_elsewhere_still_autoranges(reset):
    patch = reset('hardcopy-example.json', 'graph-boundary002', 'graph-boundary002')
    assert patch[('layout', 'xaxis', 'autorange')] is True
    assert ('layout', 'xaxis', 'range') not in patch
