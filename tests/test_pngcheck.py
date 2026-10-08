import struct
import zlib

from pngcheck import pngInfo


def chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data
            + struct.pack('>I', zlib.crc32(kind + data)))


def writePng(path, width, height):
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    phys = struct.pack('>IIB', 11811, 11811, 1)
    rows = (b'\x00' + b'\xff' * 3 * width) * height
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'pHYs', phys)
           + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
    path.write_bytes(png)
    return png


def test_png_info(tmp_path):
    page = tmp_path / 'page.png'
    png = writePng(page, 2480, 3508)
    assert pngInfo(page) == {'width': 2480, 'height': 3508, 'ppmX': 11811,
                             'ppmY': 11811, 'unit': 1, 'crcOk': True}

    # one byte of the IDAT data changed: its CRC no longer matches
    idat = png.index(b'IDAT') + 4
    broken = bytearray(png)
    broken[idat] ^= 0xFF
    page.write_bytes(bytes(broken))
    assert pngInfo(page)['crcOk'] is False
