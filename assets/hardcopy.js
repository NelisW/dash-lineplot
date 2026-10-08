/*
 * Hardcopy of the graphs on the tab currently on screen.
 *
 * Ctrl+Alt+H renders every graph of the visible tab into A4 portrait pages
 * at 300 dpi and writes each page as a PNG file. Only the graphs are drawn:
 * no tab strip, no markdown, no readout boxes, no logo. Each graph prints as
 * it is on screen, current zoom included, because Plotly.toImage renders
 * the figure the browser holds.
 *
 * Plain browser-side JavaScript like graphsync.js: Dash serves every .js
 * file in the assets folder automatically, so no callback or package is
 * involved. The tab's settings come from the data attributes of its
 * graph-tab container, written by makeGraphSet:
 *
 *   data-tab-name            default file name
 *   data-hardcopy-per-page   HardcopyGraphsPerPage, or '' when not set
 *
 * Why a folder dialog and not a Save-As dialog: showSaveFilePicker grants
 * write access to the one file named in it and to nothing beside it, so it
 * cannot write the second and later pages of a multi-page tab.
 * showDirectoryPicker grants a folder, into which every page can be written
 * after one dialog. The file name is therefore typed into a small box on
 * the page, and the folder chosen in the native dialog. Both pickers exist
 * only in Chromium browsers (Chrome, Edge), and only on a secure origin,
 * which http://localhost and http://127.0.0.1 are.
 *
 * Sizes are worked in CSS pixels, 96 to the inch, and multiplied by
 * 300 / 96 only when a graph is rendered, so text and lines come out at the
 * physical size they have on screen rather than a third of it.
 *
 * The pure functions at the top are exported under node for the tests in
 * tests/hardcopy.test.js; in the browser that guard does nothing.
 */

(function () {
    'use strict';

    var PAGE = { widthMm: 210, heightMm: 297, marginMm: 10, dpi: 300 };

    function mmToCss(mm) {
        return mm / 25.4 * 96;
    }

    function mmToPx(mm) {
        return Math.round(mm / 25.4 * PAGE.dpi);
    }

    // A file name as typed, without its .png, or null if it cannot be used.
    // The refused characters are the ones Windows does not allow in a name.
    function cleanName(raw) {
        var name = String(raw).trim().replace(/\.png$/i, '');
        if (name === '' || /[<>:"\/\\|?*]/.test(name)) {
            return null;
        }
        return name;
    }

    function pageFileNames(name, count) {
        if (count === 1) {
            return [name + '.png'];
        }
        var names = [];
        for (var k = 1; k <= count; k++) {
            names.push(name + '-p' + k + '.png');
        }
        return names;
    }

    // Place graphs of the given heights onto pages of pageHeight, all in CSS
    // px. With perPage, each page has that many equal slots. Without it,
    // each graph keeps its own height, a graph that does not fit in what is
    // left of a page starts the next one, and a graph taller than a whole
    // page is cut down to exactly one page.
    function layoutPages(heights, perPage, pageHeight) {
        var pages = [];
        var page = [];
        var y = 0;

        heights.forEach(function (height, index) {
            var h = perPage ? pageHeight / perPage : Math.min(height, pageHeight);
            var full = perPage ? page.length === perPage : y + h > pageHeight;
            if (page.length > 0 && full) {
                pages.push(page);
                page = [];
                y = 0;
            }
            page.push({ index: index, y: y, h: h });
            y += h;
        });

        if (page.length > 0) {
            pages.push(page);
        }
        return pages;
    }

    var crcTable = null;

    // The CRC-32 every PNG chunk carries, over its type and data.
    function crc32(bytes) {
        if (crcTable === null) {
            crcTable = [];
            for (var n = 0; n < 256; n++) {
                var c = n;
                for (var k = 0; k < 8; k++) {
                    c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
                }
                crcTable.push(c >>> 0);
            }
        }
        var crc = 0xFFFFFFFF;
        for (var i = 0; i < bytes.length; i++) {
            crc = crcTable[(crc ^ bytes[i]) & 0xFF] ^ (crc >>> 8);
        }
        return (crc ^ 0xFFFFFFFF) >>> 0;
    }

    // Mark a PNG with its resolution. canvas.toBlob writes none, and without
    // one most programs assume 96 dpi and show a 300 dpi page at about three
    // times its intended size. The pHYs chunk goes straight after IHDR, and
    // replaces any pHYs already there.
    function setPngDpi(png, dpi) {
        var view = new DataView(png.buffer, png.byteOffset, png.byteLength);
        var ppm = Math.round(dpi / 0.0254);

        var phys = new Uint8Array(21);
        var pv = new DataView(phys.buffer);
        pv.setUint32(0, 9);
        phys.set([0x70, 0x48, 0x59, 0x73], 4);      // 'pHYs'
        pv.setUint32(8, ppm);
        pv.setUint32(12, ppm);
        phys[16] = 1;                               // unit: metre
        pv.setUint32(17, crc32(phys.subarray(4, 17)));

        // walk the chunks, keeping all but an existing pHYs, and put the new
        // one in after IHDR
        var parts = [png.subarray(0, 8)];
        var offset = 8;
        while (offset < png.length) {
            var length = view.getUint32(offset);
            var end = offset + 12 + length;
            var type = String.fromCharCode.apply(null, png.subarray(offset + 4, offset + 8));
            if (type !== 'pHYs') {
                parts.push(png.subarray(offset, end));
            }
            if (type === 'IHDR') {
                parts.push(phys);
            }
            offset = end;
        }

        var total = parts.reduce(function (sum, p) { return sum + p.length; }, 0);
        var out = new Uint8Array(total);
        var at = 0;
        parts.forEach(function (p) {
            out.set(p, at);
            at += p.length;
        });
        return out;
    }

    async function exists(dir, name) {
        try {
            await dir.getFileHandle(name, { create: false });
            return true;
        } catch (err) {
            if (err && err.name === 'NotFoundError') {
                return false;
            }
            throw err;
        }
    }

    // Pages an earlier hardcopy of the same name left in the folder that
    // this one will not overwrite: the higher-numbered pages of a longer
    // run, and the single-page name.png beside a numbered set or the other
    // way round. They are reported, not deleted -- they are the reader's
    // files -- so that a stale page is not mistaken for part of this copy.
    async function findLeftovers(dir, name, count) {
        var leftovers = [];
        if (count > 1 && await exists(dir, name + '.png')) {
            leftovers.push(name + '.png');
        }
        for (var k = count > 1 ? count + 1 : 1; ; k++) {
            var pageName = name + '-p' + k + '.png';
            if (!(await exists(dir, pageName))) {
                break;
            }
            leftovers.push(pageName);
        }
        return leftovers;
    }

    if (typeof module === 'object' && module.exports) {
        module.exports = {
            PAGE: PAGE, mmToCss: mmToCss, mmToPx: mmToPx,
            cleanName: cleanName, pageFileNames: pageFileNames,
            layoutPages: layoutPages, crc32: crc32, setPngDpi: setPngDpi,
            findLeftovers: findLeftovers
        };
        return;
    }

    // ---------------------------------------------------------------- browser

    var UNSUPPORTED = 'Hardcopy needs Chrome or Edge, opened at a localhost address';

    // the open box, if any, and whether pages are being written into it
    var box = null;
    var writing = false;

    // The tab on screen. With callbacks only the selected tab is on the page
    // at all; without them every tab is, and the hidden ones have no
    // offsetParent.
    function visibleTab() {
        var tabs = document.querySelectorAll('.graph-tab');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].offsetParent !== null) {
                return tabs[i];
            }
        }
        return null;
    }

    function closeBox() {
        if (box !== null) {
            box.overlay.remove();
            box = null;
        }
        writing = false;
    }

    function setStatus(text) {
        box.status.textContent = text;
    }

    // Leave the final message up until the reader has seen it.
    function closeOnNextInput() {
        setTimeout(function () {
            function dismiss(event) {
                event.preventDefault();
                document.removeEventListener('keydown', dismiss, true);
                document.removeEventListener('mousedown', dismiss, true);
                closeBox();
            }
            document.addEventListener('keydown', dismiss, true);
            document.addEventListener('mousedown', dismiss, true);
        }, 0);
    }

    // The box: a file name field with Save and Cancel, or, when message is
    // given, just that message and a Close button.
    function openBox(message, defaultName, onSave) {
        var overlay = document.createElement('div');
        overlay.id = 'hardcopy-modal';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:10000;' +
            'background:rgba(0,0,0,0.3);display:flex;' +
            'align-items:center;justify-content:center;';

        var panel = document.createElement('div');
        panel.style.cssText = 'background:#fff;padding:1.6rem 2rem;' +
            'border-radius:4px;box-shadow:0 2px 12px rgba(0,0,0,0.3);' +
            'min-width:32rem;max-width:60rem;font-size:1.4rem;';
        overlay.appendChild(panel);

        var title = document.createElement('div');
        title.textContent = 'Hardcopy of this tab';
        title.style.cssText = 'font-weight:bold;margin-bottom:0.8rem;';
        panel.appendChild(title);

        var input = document.createElement('input');
        input.id = 'hardcopy-name';
        input.type = 'text';
        input.value = defaultName || '';
        input.style.cssText = 'width:100%;margin-bottom:0.8rem;';

        var save = document.createElement('button');
        save.id = 'hardcopy-save';
        save.textContent = 'Save';

        var cancel = document.createElement('button');
        cancel.id = 'hardcopy-cancel';
        cancel.textContent = message ? 'Close' : 'Cancel';
        cancel.style.marginLeft = '0.8rem';

        var status = document.createElement('div');
        status.id = 'hardcopy-status';
        status.style.cssText = 'margin-top:0.8rem;white-space:pre-wrap;';

        if (!message) {
            panel.appendChild(input);
            panel.appendChild(save);
        }
        panel.appendChild(cancel);
        panel.appendChild(status);

        box = { overlay: overlay, input: input, save: save, cancel: cancel,
                status: status };

        cancel.addEventListener('click', function () {
            if (!writing) {
                closeBox();
            }
        });
        save.addEventListener('click', onSave);
        overlay.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !writing) {
                event.preventDefault();
                closeBox();
            } else if (event.key === 'Enter' && !message && !writing) {
                event.preventDefault();
                onSave();
            }
        });

        document.body.appendChild(overlay);
        if (message) {
            status.textContent = message;
            cancel.focus();
        } else {
            input.focus();
            input.select();
        }
    }

    function loadImage(url) {
        return new Promise(function (resolve, reject) {
            var img = new Image();
            img.onload = function () { resolve(img); };
            img.onerror = function () { reject(new Error('could not load a rendered graph')); };
            img.src = url;
        });
    }

    // One page: a white A4 canvas with each graph of the page drawn at its
    // slot, rendered at its printed size and scaled up to 300 dpi.
    async function renderPage(page, graphs, widthCss) {
        var canvas = document.createElement('canvas');
        canvas.width = mmToPx(PAGE.widthMm);
        canvas.height = mmToPx(PAGE.heightMm);
        var ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        var scale = PAGE.dpi / 96;
        for (var i = 0; i < page.length; i++) {
            var slot = page[i];
            var url = await window.Plotly.toImage(graphs[slot.index], {
                format: 'png', width: widthCss, height: Math.floor(slot.h),
                scale: scale
            });
            var img = await loadImage(url);
            ctx.drawImage(img, mmToPx(PAGE.marginMm),
                          mmToPx(PAGE.marginMm) + Math.round(slot.y * scale));
        }

        var blob = await new Promise(function (resolve) {
            canvas.toBlob(resolve, 'image/png');
        });
        var bytes = new Uint8Array(await blob.arrayBuffer());
        return new Blob([setPngDpi(bytes, PAGE.dpi)], { type: 'image/png' });
    }

    async function writePages(dir, name, tab, graphs) {
        var widthCss = Math.floor(mmToCss(PAGE.widthMm - 2 * PAGE.marginMm));
        var heightCss = mmToCss(PAGE.heightMm - 2 * PAGE.marginMm);
        var perPage = parseInt(tab.getAttribute('data-hardcopy-per-page'), 10) || null;

        var pages = layoutPages(graphs.map(function (gd) { return gd.offsetHeight; }),
                                perPage, heightCss);
        var names = pageFileNames(name, pages.length);

        var existing = 0;
        for (var i = 0; i < names.length; i++) {
            if (await exists(dir, names[i])) {
                existing += 1;
            }
        }
        if (existing > 0 &&
                !window.confirm('Overwrite ' + existing + ' existing file(s) in this folder?')) {
            closeBox();
            return;
        }

        for (var k = 0; k < pages.length; k++) {
            setStatus('Page ' + (k + 1) + ' of ' + pages.length);
            var blob = await renderPage(pages[k], graphs, widthCss);
            var handle = await dir.getFileHandle(names[k], { create: true });
            var writable = await handle.createWritable();
            await writable.write(blob);
            await writable.close();
        }

        var leftovers = await findLeftovers(dir, name, pages.length);
        var note = leftovers.length === 0 ? '' :
            '\nNot part of this hardcopy, left from an earlier one: ' + leftovers.join(', ') + '.';

        setStatus('Wrote ' + names.join(', ') + ' in ' + (dir.name || 'the chosen folder') +
                  '.' + note + '\nPress any key or click to close.');
        closeOnNextInput();
    }

    function start() {
        var tab = visibleTab();
        var graphs = tab ? Array.prototype.slice.call(tab.querySelectorAll('.js-plotly-plot')) : [];
        if (graphs.length === 0) {
            openBox('There are no graphs on this tab to print.');
            return;
        }
        if (typeof window.showDirectoryPicker !== 'function') {
            openBox(UNSUPPORTED);
            return;
        }

        openBox(null, tab.getAttribute('data-tab-name'), function onSave() {
            if (writing) {
                return;
            }
            var name = cleanName(box.input.value);
            if (name === null) {
                setStatus('Not a usable file name: it must not be empty, ' +
                          'or contain any of < > : " / \\ | ? *');
                return;
            }

            // called straight from the click or the Enter key, so the
            // browser still counts it as the reader's own action, which the
            // folder dialog requires
            var picking = window.showDirectoryPicker({ mode: 'readwrite',
                                                       id: 'dash-lineplot-hardcopy' });
            writing = true;
            box.save.disabled = true;
            box.cancel.disabled = true;
            box.input.disabled = true;

            picking.then(function (dir) {
                return writePages(dir, name, tab, graphs);
            }).catch(function (err) {
                if (err && err.name === 'AbortError') {
                    // the folder dialog was cancelled
                    closeBox();
                    return;
                }
                writing = false;
                box.cancel.disabled = false;
                // disabling the focused field sent focus to the page body,
                // out of reach of the box's own Escape handler
                box.cancel.focus();
                setStatus('Hardcopy failed: ' + (err && err.message ? err.message : err));
            });
        });
    }

    document.addEventListener('keydown', function (event) {
        if (!(event.ctrlKey && event.altKey && event.code === 'KeyH')) {
            return;
        }
        event.preventDefault();
        if (box !== null) {
            return;
        }
        start();
    });
}());
