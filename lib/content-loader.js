// =============================================================
// lib/content-loader.js
// -------------------------------------------------------------
// Runtime content loader. Drop-in replacement for content.js.
//
// Strategy:
//   • Resolve data URLs RELATIVE TO THIS SCRIPT'S OWN LOCATION,
//     so the same file works for /, /he/, /work/<slug>/,
//     /he/work/<slug>/ — no matter how deep the page is nested.
//   • Fetch both languages in parallel; once both land, populate
//     window.PORTFOLIO_CONTENT with the same shape content.js used.
//   • Expose `window.PORTFOLIO_CONTENT_READY` (a Promise) so any
//     consumer can `await` readiness without polling.
//   • If a previous bundle has already populated PORTFOLIO_CONTENT
//     (e.g. content.js still in DOM during a transitional build),
//     do nothing — coexists rather than fights.
//
// On purpose:
//   • No bundling, no module syntax — works in any browser, in any
//     order with the other lib/ scripts.
//   • No third-party libs.
// =============================================================

(function () {
  // Bail if some prior script already assembled the content (e.g.
  // a legacy build that still ships lib/content.js).
  if (window.PORTFOLIO_CONTENT && window.PORTFOLIO_CONTENT.en) {
    if (!window.PORTFOLIO_CONTENT_READY) {
      window.PORTFOLIO_CONTENT_READY = Promise.resolve(window.PORTFOLIO_CONTENT);
    }
    return;
  }

  // Resolve our own location so JSON paths stay correct at every depth.
  // document.currentScript is reliable for non-module classic scripts.
  var src = (document.currentScript && document.currentScript.src) || '';
  // strip filename: ".../lib/content-loader.js" → ".../lib/"
  var libBase = src.replace(/[^/]+$/, '');
  // up one: ".../lib/" → ".../"
  var siteBase = libBase.replace(/lib\/$/, '');

  // Initialise the global container synchronously so existing code that
  // references window.PORTFOLIO_CONTENT directly doesn't TypeError. The
  // .en/.he sub-objects appear once fetched. Consumers should await
  // PORTFOLIO_CONTENT_READY before reading them.
  window.PORTFOLIO_CONTENT = window.PORTFOLIO_CONTENT || {};

  function load(lang) {
    var url = siteBase + 'data/content.' + lang + '.json';
    return fetch(url, { credentials: 'omit' }).then(function (r) {
      if (!r.ok) throw new Error('Failed to load ' + url + ': ' + r.status);
      return r.json();
    });
  }

  window.PORTFOLIO_CONTENT_READY = Promise.all([load('en'), load('he')])
    .then(function (langs) {
      window.PORTFOLIO_CONTENT.en = langs[0];
      window.PORTFOLIO_CONTENT.he = langs[1];
      // Notify any subscribers that prefer events over Promises.
      try {
        document.dispatchEvent(new CustomEvent('portfolio:ready', {
          detail: window.PORTFOLIO_CONTENT
        }));
      } catch (_) { /* IE / very old Safari */ }
      return window.PORTFOLIO_CONTENT;
    })
    .catch(function (err) {
      console.error('[content-loader] fatal:', err);
      throw err;
    });
})();
