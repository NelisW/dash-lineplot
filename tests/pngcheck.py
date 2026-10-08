"""
Check a hardcopy page written by assets/hardcopy.js.

Reports the pixel size, the resolution recorded in the pHYs chunk, and
whether every chunk's CRC is valid. A 300 dpi A4 page reads 2480 x 3508
pixels and 11811 pixels per metre (unit 1, metre) on both axes.

Usage:
    python tests/pngcheck.py page.png [page2.png ...]
"""

import struct
import sys
import zlib
from pathlib import Path


def pngInfo(path):
    data = Path(path).read_bytes()
    info = {'width': None, 'height': None, 'ppmX': None, 'ppmY': None,
            'unit': None, 'crcOk': True}

    offset = 8
    while offset < len(data):
        length, kind = struct.unpack('>I4s', data[offset:offset + 8])
        body = data[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + body) != crc:
            info['crcOk'] = False
        if kind == b'IHDR':
            info['width'], info['height'] = struct.unpack('>II', body[:8])
        elif kind == b'pHYs':
            info['ppmX'], info['ppmY'], info['unit'] = struct.unpack('>IIB', body)
        offset += 12 + length

    return info


if __name__ == '__main__':
    for name in sys.argv[1:]:
        print(name, pngInfo(name))
