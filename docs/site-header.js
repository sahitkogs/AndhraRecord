/* ================================================================
   The Amaravati Record — Shared Header, Nav & Footer
   ----------------------------------------------------------------
   Drop <script src="...site-header.js"></script> into any page,
   then call: AmaravatiHeader.render({ page: 'about' })

   The script detects its own depth (pages/, reports/, or root)
   and sets link prefixes automatically.
   ================================================================ */

var AmaravatiHeader = (function () {
  'use strict';

  // Detect path depth from the script's own src attribute
  function getBase() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute('src') || '';
      if (src.indexOf('site-header.js') !== -1) {
        // Strip filename to get relative path to docs/
        return src.replace('site-header.js', '');
      }
    }
    // Fallback: guess from pathname
    var p = location.pathname;
    if (p.indexOf('/pages/') !== -1 || p.indexOf('/reports/') !== -1) return '../';
    return '';
  }

  function render(opts) {
    opts = opts || {};
    var page = opts.page || '';          // e.g. 'about', 'reports', 'index'
    var base = getBase();                // '' from root, '../' from subfolders
    var pagesBase = base + 'pages/';

    // ── Masthead ──
    var mastheadEl = document.getElementById('site-masthead');
    if (mastheadEl) {
      mastheadEl.innerHTML =
        '<header class="masthead">' +
        '  <div class="masthead__meta">' +
        '    <span>VOL. I &middot; NO. 001</span>' +
        '    <span>FRIDAY, APRIL 10, 2026</span>' +
        '    <span>FOUNDING EDITION &middot; AMARAVATI, A.P.</span>' +
        '  </div>' +
        '  <h1 class="masthead__title"><a href="' + base + 'index.html">The Amaravati Record</a></h1>' +
        '  <p class="masthead__tagline">&ldquo;Independent reporting on the making of a capital&rdquo; &mdash; Est. 2026</p>' +
        '</header>';
    }

    // ── Nav ──
    var navEl = document.getElementById('site-nav');
    if (navEl) {
      var links = [
        { href: base + 'index.html',          label: 'Home',    id: 'index' },
        { href: pagesBase + 'reports.html',    label: 'Reports', id: 'reports' },
        { href: pagesBase + 'about.html',      label: 'About',   id: 'about' },
        { href: pagesBase + 'support.html',    label: 'Support', id: 'support' }
      ];
      var html = '<nav class="nav" aria-label="Primary">';
      for (var i = 0; i < links.length; i++) {
        var cls = (links[i].id === page) ? ' class="is-current"' : '';
        html += '<a href="' + links[i].href + '"' + cls + '>' + links[i].label + '</a>';
      }
      html += '</nav>';
      navEl.innerHTML = html;
    }

    // ── Footer ──
    var footerEl = document.getElementById('site-footer');
    if (footerEl) {
      footerEl.innerHTML =
        '<footer class="colophon">' +
        '  <span>THE AMARAVATI RECORD &middot; FOUNDING EDITION &middot; APRIL 2026</span>' +
        '  <span>' +
        '    <a href="' + pagesBase + 'privacy.html">Privacy</a> &middot; ' +
        '    <a href="' + pagesBase + 'cookies.html">Cookies</a> &middot; ' +
        '    <a href="' + pagesBase + 'terms.html">Terms</a> &middot; ' +
        '    <a href="' + pagesBase + 'editorial.html">Editorial</a> &middot; ' +
        '    <a href="' + pagesBase + 'corrections.html">Corrections</a> &middot; ' +
        '    <a href="' + pagesBase + 'ai-disclosure.html">AI</a> &middot; ' +
        '    <a href="' + pagesBase + 'licenses.html">Licenses</a> &middot; ' +
        '    <a href="' + pagesBase + 'contact.html">Contact</a> &middot; ' +
        '    <a href="https://sahitkogs.github.io/amaravati-tracker-staging/" target="_blank" rel="noopener">Tracker</a>' +
        (typeof AmaravatRecord_openConsent === 'function'
          ? ' &middot; <a href="#" onclick="return AmaravatRecord_openConsent();">Cookie settings</a>'
          : '') +
        '  </span>' +
        '  <span>Independent &middot; Public Interest &middot; Reader-Supported</span>' +
        '</footer>';
    }
  }

  return { render: render };
})();
