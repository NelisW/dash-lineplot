import json

from conftest import walk, props


def parentOf(root, childId):
    """The component whose children directly include the one with childId."""
    for component in walk(root):
        children = getattr(component, 'children', None)
        if not isinstance(children, (list, tuple)):
            children = [children]
        for child in children:
            if hasattr(child, 'to_plotly_json') and props(child).get('id') == childId:
                return component
    return None


def test_hardcopy_per_page_values(dlp):
    assert dlp.hardcopyPerPage(4) == '4'
    assert dlp.hardcopyPerPage(4.0) == '4'
    assert dlp.hardcopyPerPage('3') == '3'
    for bad in (0, -2, 2.5, 'abc', '', None, float('nan')):
        assert dlp.hardcopyPerPage(bad) == ''


def test_tab_wrapper(dlp, build):
    build('hardcopy-example.json')
    wrappers = [tab[0] for tab in dlp.divSets]
    assert all(len(tab) == 1 for tab in dlp.divSets)
    assert [props(w)['className'] for w in wrappers] == ['graph-tab'] * 3
    assert [props(w)['data-tab-name'] for w in wrappers] == ['many', 'mixed', 'boundary']
    assert [props(w)['data-hardcopy-per-page'] for w in wrappers] == ['4', '', '']


def test_box_threshold(dlp, build):
    plotter = build('hardcopy-example.json')
    ids = {props(c).get('id') for tab in dlp.divSets for c in walk(tab[0])}
    for g in ['graph-many000', 'graph-mixed002', 'graph-boundary001']:
        assert 'xstart-' + g not in ids and 'click-' + g not in ids
    for g in ['graph-mixed000', 'graph-boundary002']:
        assert 'xstart-' + g in ids and 'click-' + g in ids
    assert plotter.boxedGraphs == {'graph-mixed000', 'graph-mixed001', 'graph-boundary002'}


def test_commonx_unboxed_graph_keeps_x_alignment(dlp, build):
    # on a commonX tab with boxed graphs, a short graph keeps the boxed
    # graphs' plot width, with an empty column where their boxes are
    build('hardcopy-example.json')
    root = dlp.divSets
    column = parentOf(root, 'graph-mixed002')
    assert props(column)['className'] == 'nine columns'
    row = next(c for c in walk(root)
               if isinstance(getattr(c, 'children', None), list)
               and any(child is column for child in c.children))
    spacer = [c for c in row.children if c is not column]
    assert [props(c)['className'] for c in spacer] == ['three columns']
    assert not getattr(spacer[0], 'children', None)


def test_commonx_tab_of_only_short_graphs_is_full_width(dlp, build, tmp_path):
    rows = [{'Variable': 'Height', 'Value': 150},
            {'Variable': 'Datafile', 'Value': 'data/hardcopy-demo.csv'},
            {'Variable': 'xValue', 'Value': 'Time'},
            {'Variable': 'commonX', 'Value': True}]
    for signal in ['Sine1Hz', 'Ramp']:
        rows += [{'Variable': 'Title', 'Value': signal},
                 {'Variable': 'yLabel', 'Value': signal},
                 {'Variable': 'yValue', 'Value': signal}]
    config = tmp_path / 'short.json'
    config.write_text(json.dumps({'header': {'Pagetitle': 'short'},
                                  'sheets': {'graph-short': rows}}))
    build(str(config))
    for g in ['graph-short000', 'graph-short001']:
        assert props(parentOf(dlp.divSets, g))['className'] == 'twelve columns'


def test_unboxed_graph_full_width(dlp, build):
    build('hardcopy-example.json')
    root = dlp.divSets
    assert props(parentOf(root, 'graph-many000'))['className'] == 'twelve columns'
    assert props(parentOf(root, 'graph-mixed000'))['className'] == 'nine columns'
