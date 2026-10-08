import json

import pytest


def writeSources(folder):
    """Two sources naming their time column differently, on different grids."""
    a = folder / 'a.json'
    b = folder / 'b.json'
    a.write_text(json.dumps([{'t': 0.1 * i, 'v': i} for i in range(11)]))
    b.write_text(json.dumps([{'time': 0.05 + 0.25 * i, 'v': -i} for i in range(5)]))
    return a.as_posix(), b.as_posix()


def writeConfig(folder, a, b, xForB):
    rowB = {'Variable': 'yValue', 'Value': 'v', 'Datafile': b, 'LineLabel': 'b'}
    if xForB is not None:
        rowB['xValue'] = xForB
    rows = [{'Variable': 'Height', 'Value': 300},
            {'Variable': 'Datafile', 'Value': a},
            {'Variable': 'xValue', 'Value': 't'},
            {'Variable': 'Title', 'Value': 'v from both'},
            {'Variable': 'yLabel', 'Value': 'v'},
            {'Variable': 'yValue', 'Value': 'v', 'LineLabel': 'a'},
            rowB]
    config = folder / 'cfg.json'
    config.write_text(json.dumps({'header': {'Pagetitle': 'multi'},
                                  'sheets': {'graph-multi': rows}}))
    return str(config)


def test_per_trace_x_column(build, tmp_path):
    a, b = writeSources(tmp_path)
    plotter = build(writeConfig(tmp_path, a, b, 'time'))
    traces = {name: (x, custom) for name, x, custom, _ in plotter.graphTraces['graph-multi000']}
    # trace a keeps the block's 't', trace b reads its own 'time'
    assert len(traces['a'][0]) == 11 and len(traces['b'][0]) == 5
    assert traces['a'][0].iloc[-1] == pytest.approx(1.0)
    assert traces['b'][0].iloc[0] == pytest.approx(0.05)
    assert traces['b'][0].iloc[-1] == pytest.approx(1.05)
    # the readouts' true x comes from the trace's own column too
    assert traces['b'][1][0][0] == pytest.approx(0.05)


def test_missing_per_trace_x_column_is_reported(build, tmp_path):
    a, b = writeSources(tmp_path)
    with pytest.raises(ValueError, match=r"xValue 'nope' is not a column of .*b\.json"):
        build(writeConfig(tmp_path, a, b, 'nope'))


def test_blank_per_trace_x_column_uses_the_block(build, tmp_path):
    # without an override, b is looked up by the block's 't', which it lacks
    a, b = writeSources(tmp_path)
    with pytest.raises(ValueError, match=r"xValue 't' is not a column of .*b\.json"):
        build(writeConfig(tmp_path, a, b, None))


def test_multisource_demo_builds(dlp, build):
    plotter = build('multisource-example.json')
    assert dlp.graphTabs == ['summary']
    assert dlp.graphList == [['graph-summary000', 'graph-summary001']]
    for graph in dlp.graphList[0]:
        lengths = [len(x) for _, x, _, _ in plotter.graphTraces[graph]]
        assert lengths == [201, 81, 41]
