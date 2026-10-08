// Tests for the pure functions of assets/hardcopy.js. Run with:
//     node --test tests/hardcopy.test.js
const test = require('node:test');
const assert = require('node:assert');
const hc = require('../assets/hardcopy.js');

test('cleanName', () => {
    assert.strictEqual(hc.cleanName('  gimbal.PNG '), 'gimbal');
    assert.strictEqual(hc.cleanName('a.png.png'), 'a.png');
    for (const bad of ['', '   ', '.png', 'a/b', 'a:b', 'a?']) {
        assert.strictEqual(hc.cleanName(bad), null);
    }
});

test('pageFileNames', () => {
    assert.deepStrictEqual(hc.pageFileNames('t', 1), ['t.png']);
    assert.deepStrictEqual(hc.pageFileNames('t', 3), ['t-p1.png', 't-p2.png', 't-p3.png']);
});

test('layoutPages equal slots', () => {
    const pages = hc.layoutPages(Array(10).fill(150), 4, 1000);
    assert.deepStrictEqual(pages.map(p => p.length), [4, 4, 2]);
    assert.deepStrictEqual(pages[2], [{index: 8, y: 0, h: 250}, {index: 9, y: 250, h: 250}]);
});

test('layoutPages by height', () => {
    const pages = hc.layoutPages([300, 300, 150, 150, 150, 150], null, 1047);
    assert.deepStrictEqual(pages.map(p => p.map(s => s.y)), [[0, 300, 600, 750], [0, 150]]);
    assert.deepStrictEqual(hc.layoutPages([200, 200, 201], null, 1047).length, 1);
    assert.deepStrictEqual(hc.layoutPages([1200], null, 1047), [[{index: 0, y: 0, h: 1047}]]);
    assert.deepStrictEqual(hc.layoutPages([], 4, 1047), []);
});

test('findLeftovers reports pages of an earlier, longer run', async () => {
    const folder = (names) => ({
        getFileHandle: async (name) => {
            if (!names.includes(name)) {
                throw Object.assign(new Error('missing'), { name: 'NotFoundError' });
            }
            return {};
        }
    });
    // three pages before, two now: p3 is left over
    assert.deepStrictEqual(
        await hc.findLeftovers(folder(['t-p1.png', 't-p2.png', 't-p3.png']), 't', 2),
        ['t-p3.png']);
    // one page before, two now: t.png is left over
    assert.deepStrictEqual(
        await hc.findLeftovers(folder(['t.png']), 't', 2), ['t.png']);
    // two pages before, one now: both numbered pages are left over
    assert.deepStrictEqual(
        await hc.findLeftovers(folder(['t-p1.png', 't-p2.png']), 't', 1),
        ['t-p1.png', 't-p2.png']);
    // nothing from before
    assert.deepStrictEqual(await hc.findLeftovers(folder([]), 't', 3), []);
});

test('crc32 check value', () => {
    assert.strictEqual(hc.crc32(new TextEncoder().encode('123456789')), 0xCBF43926);
});

test('setPngDpi inserts then replaces pHYs', () => {
    // 1x1 PNG with IHDR, IDAT, IEND and no pHYs
    const png = Uint8Array.from(Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
        'base64'));
    const once = hc.setPngDpi(png, 300);
    assert.strictEqual(once.length, png.length + 21);
    const dv = new DataView(once.buffer);
    assert.strictEqual(String.fromCharCode(...once.slice(37, 41)), 'pHYs');
    assert.strictEqual(dv.getUint32(41), 11811);
    assert.strictEqual(dv.getUint32(45), 11811);
    assert.strictEqual(once[49], 1);
    assert.strictEqual(dv.getUint32(50), hc.crc32(once.slice(37, 50)));
    const twice = hc.setPngDpi(once, 300);
    assert.deepStrictEqual(twice, once);
});
