import dash
import pytest

PNG = b'\x89PNG\r\n\x1a\n' + b'rest of a page'


@pytest.fixture
def client(dlp, tmp_path):
    app = dash.Dash('routes')
    # Dash refuses every request, its own or not, until a layout is set
    app.layout = dash.html.Div()
    dlp.DashLinePlot().setupHardcopyRoutes(app.server, tmp_path)
    return app.server.test_client()


def test_folder_reports_the_target_directory(client, tmp_path):
    assert client.get('/_hardcopy/folder').get_json() == {'path': str(tmp_path)}


def test_write_then_exists(client, tmp_path):
    assert client.head('/_hardcopy/files/page-p1.png').status_code == 404
    put = client.put('/_hardcopy/files/page-p1.png', data=PNG,
                     content_type='image/png')
    assert put.status_code == 204
    assert (tmp_path / 'page-p1.png').read_bytes() == PNG
    assert client.head('/_hardcopy/files/page-p1.png').status_code == 200


def test_refuses_bad_names(client, tmp_path):
    for name in ['a:b.png', 'page.txt', '.png', 'a%3Fb.png']:
        put = client.put('/_hardcopy/files/' + name, data=PNG,
                         content_type='image/png')
        assert put.status_code == 400, name
    assert list(tmp_path.iterdir()) == []


def test_refuses_what_is_not_a_png(client, tmp_path):
    notPng = client.put('/_hardcopy/files/x.png', data=b'hello',
                        content_type='image/png')
    assert notPng.status_code == 400
    # a cross-site page could only send text/plain without a preflight
    wrongType = client.put('/_hardcopy/files/x.png', data=PNG,
                           content_type='text/plain')
    assert wrongType.status_code == 415
    assert list(tmp_path.iterdir()) == []
