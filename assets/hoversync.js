/*
 * Synchronised hover across every graph on a page.
 *
 * Replaces the visdcc.Run_js injection that did this before visdcc stopped
 * being maintained. Dash serves every .js file in the assets folder
 * automatically, so this needs no package and no callback: it is plain
 * browser-side JavaScript talking to the Plotly graphs already on the page.
 *
 * Behaviour: hovering any graph makes every other graph on the page show
 * its own readout at the same x value. Each graph resolves that x against
 * its own samples, so graphs recorded at different rates each show their
 * own nearest sample. Nothing is interpolated and no graph is assumed to
 * share a time base, a sample rate or a data type with any other.
 *
 * Graphs are re-created when a tab is selected, so a MutationObserver
 * re-attaches the handlers whenever the tab content changes.
 */

(function () {
    'use strict';

    // Guard against the feedback loop: calling Plotly.Fx.hover on another
    // graph makes that graph emit plotly_hover in turn, which would come
    // straight back here.
    var syncing = false;

    function plots() {
        return Array.prototype.slice.call(
            document.querySelectorAll('.js-plotly-plot'));
    }

    // Every subplot of one graph, e.g. ['xy'] or ['xy', 'xy2', ...].
    function subplotsOf(gd) {
        if (!gd._fullLayout || !gd._fullLayout._plots) {
            return ['xy'];
        }
        return Object.keys(gd._fullLayout._plots);
    }

    function showAtX(gd, xval) {
        try {
            window.Plotly.Fx.hover(gd, { xval: xval }, subplotsOf(gd));
        } catch (err) {
            /* A graph whose x axis cannot resolve this value simply shows
               nothing. That is not an error worth reporting to the user. */
        }
    }

    function clear(gd) {
        try {
            window.Plotly.Fx.unhover(gd);
        } catch (err) {
            /* as above */
        }
    }

    function onHover(source, eventdata) {
        if (syncing) {
            return;
        }
        if (!eventdata || !eventdata.xvals || eventdata.xvals.length === 0) {
            return;
        }
        var xval = eventdata.xvals[0];

        syncing = true;
        try {
            plots().forEach(function (gd) {
                if (gd !== source && gd.offsetParent !== null) {
                    showAtX(gd, xval);
                }
            });
        } finally {
            syncing = false;
        }
    }

    function onUnhover(source) {
        if (syncing) {
            return;
        }
        syncing = true;
        try {
            plots().forEach(function (gd) {
                if (gd !== source) {
                    clear(gd);
                }
            });
        } finally {
            syncing = false;
        }
    }

    function attach(gd) {
        if (gd._hoverSyncAttached || typeof gd.on !== 'function') {
            return;
        }
        gd._hoverSyncAttached = true;
        gd.on('plotly_hover', function (eventdata) { onHover(gd, eventdata); });
        gd.on('plotly_unhover', function () { onUnhover(gd); });
    }

    function attachAll() {
        if (!window.Plotly) {
            return;
        }
        plots().forEach(attach);
    }

    // Dash renders tab content through a callback, so the graphs of a tab do
    // not exist until that tab is first selected, and are replaced wholesale
    // on every later selection.
    function watch() {
        attachAll();
        var observer = new MutationObserver(function () { attachAll(); });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watch);
    } else {
        watch();
    }
}());
