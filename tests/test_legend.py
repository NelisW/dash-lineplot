import json
import math
import re

import pytest

from conftest import walk, props


def alphaOf(dlp, graphId):
    for tab in dlp.divSets:
        for component in walk(tab[0]):
            if props(component).get('id') == graphId:
                bgcolor = props(component)['figure']['layout']['legend']['bgcolor']
                return float(re.fullmatch(r'rgba\(255, 255, 255, ([0-9.]+)\)', bgcolor).group(1))
    raise KeyError(graphId)


def graphRows(title):
    return [{'Variable': 'Title', 'Value': title},
            {'Variable': 'yLabel', 'Value': 'Ramp'},
            {'Variable': 'yValue', 'Value': 'Ramp'}]


def writeConfig(folder, header, sheets):
    """sheets: {name: rows placed between the block rows and the graphs}"""
    config = {'header': dict({'Pagetitle': 'legend'}, **header), 'sheets': {}}
    for name, rows in sheets.items():
        config['sheets'][name] = ([{'Variable': 'Height', 'Value': 300},
                                   {'Variable': 'Datafile', 'Value': 'data/hardcopy-demo.csv'},
                                   {'Variable': 'xValue', 'Value': 'Time'}] + rows)
    path = folder / 'legend.json'
    path.write_text(json.dumps(config))
    return str(path)


# alphaOf reads the alpha of the drawn background: 1 is solid white, 0 lets
# the plot show through. LegendTransparency is the other way round.

def test_legend_transparency_values(dlp):
    assert dlp.legendTransparencyValue(0.3) == 0.3
    assert dlp.legendTransparencyValue('0.3') == 0.3
    assert dlp.legendTransparencyValue(0) == 0.0
    assert dlp.legendTransparencyValue(1) == 1.0
    for bad in (None, '', float('nan'), -0.1, 1.5, 'abc'):
        assert dlp.legendTransparencyValue(bad) is None


def test_zero_is_solid_white_and_one_shows_the_plot(dlp, build, tmp_path):
    build(writeConfig(tmp_path, {'LegendTransparency': 0}, {
        'graph-a': graphRows('white') + graphRows('clear')
                   + [{'Variable': 'LegendTransparency', 'Value': 1}],
    }))
    assert alphaOf(dlp, 'graph-a000') == 1.0
    assert alphaOf(dlp, 'graph-a001') == 0.0


def test_default_is_today_s_look(dlp, build, tmp_path):
    build(writeConfig(tmp_path, {}, {'graph-a': graphRows('one')}))
    assert alphaOf(dlp, 'graph-a000') == pytest.approx(0.6)


def test_three_levels(dlp, build, tmp_path):
    # header for the page; a row before the first Title for its tab; a row
    # after a graph's Title for that graph alone
    build(writeConfig(tmp_path, {'LegendTransparency': 0.7}, {
        'graph-plain': graphRows('p1') + graphRows('p2'),
        'graph-tabbed': ([{'Variable': 'LegendTransparency', 'Value': 0.2}]
                         + graphRows('t1')
                         + graphRows('t2') + [{'Variable': 'LegendTransparency', 'Value': 0}]
                         + graphRows('t3')),
    }))
    assert [alphaOf(dlp, f'graph-plain00{k}') for k in range(2)] == pytest.approx([0.3, 0.3])
    assert [alphaOf(dlp, f'graph-tabbed00{k}') for k in range(3)] == pytest.approx([0.8, 1.0, 0.8])


def test_bad_values_warn_and_fall_back(dlp, build, tmp_path, capsys):
    build(writeConfig(tmp_path, {'LegendTransparency': 'abc'}, {
        'graph-a': ([{'Variable': 'LegendTransparency', 'Value': 1.5}]
                    + graphRows('one')),
    }))
    assert alphaOf(dlp, 'graph-a000') == pytest.approx(0.6)
    printed = capsys.readouterr().out
    assert "LegendTransparency 'abc'" in printed and "LegendTransparency '1.5'" in printed


def test_commonx_example_shows_all_three_levels(dlp, build):
    # the same look as before the rename: alpha 0.3, then 0.6, 1, 0.6
    build('commonx-example.json')
    assert [alphaOf(dlp, f'graph-linked00{k}') for k in range(3)] == pytest.approx([0.3, 0.3, 0.3])
    assert [alphaOf(dlp, f'graph-independent00{k}') for k in range(3)] == pytest.approx([0.6, 1.0, 0.6])


@pytest.mark.parametrize('configfile', ['dash-config.xlsx', 'dash-config-sim.xlsx',
                                        'dash-config.json', 'hardcopy-example.json',
                                        'multisource-example.json'])
def test_every_example_sets_the_page_value(dlp, build, configfile):
    plotter = build(configfile)
    assert plotter.legend['LegendTransparency'] == 0.7
    assert 'LegendOpacity' not in plotter.legend


def legendOf(dlp, graphId):
    for tab in dlp.divSets:
        for component in walk(tab[0]):
            if props(component).get('id') == graphId:
                legend = props(component)['figure']['layout']['legend']
                return (legend['orientation'], legend['x'], legend['y'])
    raise KeyError(graphId)


def test_legend_orientation_values(dlp):
    for good, expected in [('v', 'v'), ('h', 'h'), ('V', 'v'), (' H ', 'h')]:
        assert dlp.legendOrientationValue(good) == expected
    for bad in ('x', 'horizontal', '', None, 1):
        assert dlp.legendOrientationValue(bad) is None


def test_legend_position_values(dlp):
    assert dlp.legendPositionValue(0) == 0.0
    assert dlp.legendPositionValue(1) == 1.0
    assert dlp.legendPositionValue('0.25') == 0.25
    for bad in (-0.1, 1.1, 2, 'abc', '', None):
        assert dlp.legendPositionValue(bad) is None


def test_default_legend_is_today_s_top_right(dlp, build, tmp_path):
    build(writeConfig(tmp_path, {}, {'graph-a': graphRows('one')}))
    for tab in dlp.divSets:
        for component in walk(tab[0]):
            if props(component).get('id') == 'graph-a000':
                legend = props(component)['figure']['layout']['legend']
    assert (legend['orientation'], legend['x'], legend['y']) == ('v', 1.0, 1.0)
    # 'auto' anchors a legend at (1, 1) by its top-right corner, as before
    assert (legend['xanchor'], legend['yanchor']) == ('auto', 'auto')


def test_each_legend_setting_resolves_on_its_own(dlp, build, tmp_path):
    build(writeConfig(tmp_path, {'LegendOrientation': 'h', 'LegendX': 0, 'LegendY': 0}, {
        'graph-plain': graphRows('p1'),
        'graph-tabbed': ([{'Variable': 'LegendX', 'Value': 0.5}]
                         + graphRows('t1')
                         + graphRows('t2') + [{'Variable': 'LegendOrientation', 'Value': 'v'},
                                              {'Variable': 'LegendX', 'Value': 1}]),
    }))
    assert legendOf(dlp, 'graph-plain000') == ('h', 0.0, 0.0)
    assert legendOf(dlp, 'graph-tabbed000') == ('h', 0.5, 0.0)
    assert legendOf(dlp, 'graph-tabbed001') == ('v', 1.0, 0.0)


def test_bad_legend_layout_values_warn_and_fall_back(dlp, build, tmp_path, capsys):
    build(writeConfig(tmp_path, {'LegendX': 2}, {
        'graph-a': ([{'Variable': 'LegendOrientation', 'Value': 'diagonal'}]
                    + graphRows('one')),
    }))
    assert legendOf(dlp, 'graph-a000') == ('v', 1.0, 1.0)
    printed = capsys.readouterr().out
    assert "LegendX '2'" in printed and "LegendOrientation 'diagonal'" in printed


def test_multisource_example_demonstrates_the_legend_layout(dlp, build):
    build('multisource-example.json')
    assert legendOf(dlp, 'graph-summary000') == ('h', 0.5, 0.0)
    assert legendOf(dlp, 'graph-summary001') == ('v', 1.0, 0.0)
