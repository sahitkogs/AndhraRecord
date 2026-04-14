/* ================================================================
   The Amaravati Record — Shared Header, Nav, Footer & Theme Toggle
   ----------------------------------------------------------------
   Drop <script src="...site-header.js"></script> into any page,
   then call: AmaravatiHeader.render({ page: 'about' })

   The script detects its own depth (pages/, reports/, or root)
   and sets link prefixes automatically.

   Theme toggle: sun/moon icon in the top-right of the masthead.
   Persists in localStorage. Overrides prefers-color-scheme.
   ================================================================ */

// --- Theme: apply saved preference immediately (before render) to avoid flash ---
(function () {
  var THEME_KEY = 'amaravati_theme';
  var saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
  if (saved === 'dark' || saved === 'light') {
    document.documentElement.setAttribute('data-theme', saved);
  }
})();

var AmaravatiHeader = (function () {
  'use strict';

  var THEME_KEY = 'amaravati_theme';

  function getTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (saved === 'dark' || saved === 'light') return saved;
    // Fall back to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    // Update toggle icon
    var btn = document.querySelector('.theme-toggle');
    if (btn) btn.textContent = theme === 'dark' ? '\u2600' : '\u263D';
  }

  // Detect path depth from the script's own src attribute
  function getBase() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute('src') || '';
      if (src.indexOf('site-header.js') !== -1) {
        return src.replace('site-header.js', '');
      }
    }
    var p = location.pathname;
    if (p.indexOf('/pages/') !== -1 || p.indexOf('/reports/') !== -1) return '../';
    return '';
  }

  // Inject site-header.css to enforce identical styling everywhere
  function injectCSS(base) {
    var href = base + 'site-header.css';
    if (!document.querySelector('link[href="' + href + '"]')) {
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      document.head.appendChild(link);
    }
  }

  function render(opts) {
    opts = opts || {};
    var page = opts.page || '';
    var base = getBase();
    var pagesBase = base + 'pages/';
    var theme = getTheme();

    // Inject shared header CSS
    injectCSS(base);

    // Apply theme
    setTheme(theme);

    // ── Masthead ──
    var mastheadEl = document.getElementById('site-masthead');
    if (mastheadEl) {
      var icon = theme === 'dark' ? '\u2600' : '\u263D';
      mastheadEl.innerHTML =
        '<header class="masthead">' +
        '  <button class="theme-toggle" aria-label="Toggle dark mode" title="Toggle dark mode">' + icon + '</button>' +
        '  <div class="masthead__meta">' +
        '    <span>VOL. I &middot; NO. 001</span>' +
        '    <span>FRIDAY, APRIL 10, 2026</span>' +
        '    <span>FOUNDING EDITION &middot; AMARAVATI, A.P.</span>' +
        '  </div>' +
        '  <h1 class="masthead__title"><a href="' + base + 'index.html" style="color:inherit;text-decoration:none;">The Amaravati Record</a></h1>' +
        '  <p class="masthead__tagline">&ldquo;Independent reporting on the making of a capital&rdquo; &mdash; Est. 2026</p>' +
        '</header>';

      // Bind toggle
      var btn = mastheadEl.querySelector('.theme-toggle');
      if (btn) {
        btn.addEventListener('click', function () {
          var current = getTheme();
          setTheme(current === 'dark' ? 'light' : 'dark');
        });
      }
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

  return { render: render, setTheme: setTheme, getTheme: getTheme };
})();
