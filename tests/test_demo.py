def test_demo_builds(dlp, build):
    build('hardcopy-example.json')
    assert dlp.graphTabs == ['many', 'mixed', 'boundary']
    assert [len(g) for g in dlp.graphList] == [10, 6, 3]
    assert dlp.graphList[1][0] == 'graph-mixed000'
