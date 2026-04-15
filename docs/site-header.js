/* ================================================================
   Andhra Record — Header, Nav, Footer, Theme/Lang, Ticker
   CNN-style: logo + nav bar, hamburger on mobile, dark footer
   ================================================================ */

(function () {
  var THEME_KEY = 'andhra_theme';
  var saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
  document.documentElement.setAttribute('data-theme', (saved === 'dark' || saved === 'light') ? saved : 'light');
})();

var AndhraRecord = (function () {
  'use strict';

  var THEME_KEY = 'andhra_theme';
  var LANG_KEY = 'andhra_lang';

  var STRINGS = {
    en: {
      home: 'Home', reports: 'Reports', about: 'About', support: 'Support',
      ticker: [
        'LAND POOLING DATA: KAMMA COMMUNITY HOLDS 57.4% OF 47,993 ALLOCATED PLOTS ACROSS 26 VILLAGES',
        'NEXT LARGEST GROUPS: KAPU 13.0% AND REDDY 5.0% &mdash; FULL BREAKDOWN IN THE DASHBOARD',
        'CAPITAL TRACKER NOW MONITORING 20 CONSTRUCTION SITES ACROSS THE KRISHNA&ndash;GUNTUR CORRIDOR',
        'SURNAME DIRECTORY EXPANDS TO 15,000+ ENTRIES ACROSS 50+ CASTE CATEGORIES'
      ],
      footerCols: [
        { title: 'Reports', links: [
          { label: 'Caste Dashboard', page: 'reports/lps-caste-dashboard.html', isReport: true },
          { label: 'Investigation', page: 'reports/lps-caste-investigation.html', isReport: true },
          { label: 'Capital Tracker', href: 'https://sahitkogs.github.io/amaravati-tracker-staging/', external: true }
        ]},
        { title: 'About', links: [
          { label: 'About Us', page: 'pages/about.html' },
          { label: 'Methodology', page: 'pages/methodology.html' },
          { label: 'Editorial Policy', page: 'pages/editorial.html' }
        ]},
        { title: 'Legal', links: [
          { label: 'Privacy', page: 'pages/privacy.html' },
          { label: 'Cookies', page: 'pages/cookies.html' },
          { label: 'Terms', page: 'pages/terms.html' },
          { label: 'AI Disclosure', page: 'pages/ai-disclosure.html' },
          { label: 'Licenses', page: 'pages/licenses.html' }
        ]},
        { title: 'Contact', links: [
          { label: 'Contact & Tips', page: 'pages/contact.html' },
          { label: 'Corrections', page: 'pages/corrections.html' },
          { label: 'Support', page: 'pages/support.html' }
        ]}
      ],
      footerBottom: '&copy; 2026 Andhra Record. Independent &middot; Public Interest &middot; Reader-Supported',
      langLabel: '\u0C24\u0C46'
    },
    te: {
      home: '\u0C39\u0C4B\u0C2E\u0C4D', reports: '\u0C28\u0C3F\u0C35\u0C47\u0C26\u0C3F\u0C15\u0C32\u0C41', about: '\u0C17\u0C41\u0C30\u0C3F\u0C02\u0C1A\u0C3F', support: '\u0C2E\u0C26\u0C4D\u0C26\u0C24\u0C41',
      ticker: [
        '\u0C2D\u0C42 \u0C38\u0C2E\u0C40\u0C15\u0C30\u0C23 \u0C21\u0C47\u0C1F\u0C3E: 26 \u0C17\u0C4D\u0C30\u0C3E\u0C2E\u0C3E\u0C32\u0C32\u0C4B 47,993 \u0C15\u0C47\u0C1F\u0C3E\u0C2F\u0C3F\u0C02\u0C2A\u0C41 \u0C2A\u0C4D\u0C32\u0C3E\u0C1F\u0C4D\u0C32\u0C32\u0C4B 57.4% \u0C15\u0C2E\u0C4D\u0C2E \u0C15\u0C41\u0C32\u0C3E\u0C28\u0C3F\u0C15\u0C3F',
        '\u0C24\u0C26\u0C41\u0C2A\u0C30\u0C3F \u0C2A\u0C46\u0C26\u0C4D\u0C26 \u0C38\u0C2E\u0C42\u0C39\u0C3E\u0C32\u0C41: \u0C15\u0C3E\u0C2A\u0C41 13.0% \u0C2E\u0C30\u0C3F\u0C2F\u0C41 \u0C30\u0C46\u0C21\u0C4D\u0C21\u0C3F 5.0% &mdash; \u0C2A\u0C42\u0C30\u0C4D\u0C24\u0C3F \u0C35\u0C3F\u0C35\u0C30\u0C3E\u0C32\u0C41 \u0C21\u0C3E\u0C37\u0C4D\u200C\u0C2C\u0C4B\u0C30\u0C4D\u0C21\u0C4D\u200C\u0C32\u0C4B',
        '\u0C15\u0C4D\u0C2F\u0C3E\u0C2A\u0C3F\u0C1F\u0C32\u0C4D \u0C1F\u0C4D\u0C30\u0C3E\u0C15\u0C30\u0C4D: \u0C15\u0C43\u0C37\u0C4D\u0C23\u0C3E&ndash;\u0C17\u0C41\u0C02\u0C1F\u0C42\u0C30\u0C41 \u0C15\u0C3E\u0C30\u0C3F\u0C21\u0C3E\u0C30\u0C4D\u200C\u0C32\u0C4B 20 \u0C28\u0C3F\u0C30\u0C4D\u0C2E\u0C3E\u0C23 \u0C2A\u0C4D\u0C30\u0C26\u0C47\u0C36\u0C3E\u0C32 \u0C2A\u0C30\u0C4D\u0C2F\u0C35\u0C47\u0C15\u0C4D\u0C37\u0C23',
        '\u0C07\u0C02\u0C1F\u0C3F\u0C2A\u0C47\u0C30\u0C4D\u0C32 \u0C38\u0C02\u0C15\u0C32\u0C28\u0C02: 50+ \u0C15\u0C41\u0C32 \u0C35\u0C30\u0C4D\u0C17\u0C3E\u0C32\u0C32\u0C4B 15,000+ \u0C07\u0C02\u0C1F\u0C3F\u0C2A\u0C47\u0C30\u0C4D\u0C32\u0C41'
      ],
      footerCols: [
        { title: '\u0C28\u0C3F\u0C35\u0C47\u0C26\u0C3F\u0C15\u0C32\u0C41', links: [
          { label: '\u0C15\u0C41\u0C32 \u0C21\u0C3E\u0C37\u0C4D\u200C\u0C2C\u0C4B\u0C30\u0C4D\u0C21\u0C4D', page: 'reports/lps-caste-dashboard.html', isReport: true },
          { label: '\u0C2A\u0C30\u0C3F\u0C36\u0C4B\u0C27\u0C28', page: 'reports/lps-caste-investigation.html', isReport: true },
          { label: '\u0C15\u0C4D\u0C2F\u0C3E\u0C2A\u0C3F\u0C1F\u0C32\u0C4D \u0C1F\u0C4D\u0C30\u0C3E\u0C15\u0C30\u0C4D', href: 'https://sahitkogs.github.io/amaravati-tracker-staging/', external: true }
        ]},
        { title: '\u0C17\u0C41\u0C30\u0C3F\u0C02\u0C1A\u0C3F', links: [
          { label: '\u0C2E\u0C3E \u0C17\u0C41\u0C30\u0C3F\u0C02\u0C1A\u0C3F', page: 'pages/about.html' },
          { label: '\u0C2A\u0C26\u0C4D\u0C27\u0C24\u0C3F\u0C36\u0C3E\u0C38\u0C4D\u0C24\u0C4D\u0C30\u0C02', page: 'pages/methodology.html' },
          { label: '\u0C38\u0C02\u0C2A\u0C3E\u0C26\u0C15\u0C40\u0C2F\u0C02', page: 'pages/editorial.html' }
        ]},
        { title: '\u0C1A\u0C1F\u0C4D\u0C1F\u0C2A\u0C30\u0C02', links: [
          { label: '\u0C17\u0C4B\u0C2A\u0C4D\u0C2F\u0C24', page: 'pages/privacy.html' },
          { label: '\u0C15\u0C41\u0C15\u0C40\u0C32\u0C41', page: 'pages/cookies.html' },
          { label: '\u0C28\u0C3F\u0C2C\u0C02\u0C27\u0C28\u0C32\u0C41', page: 'pages/terms.html' },
          { label: 'AI', page: 'pages/ai-disclosure.html' },
          { label: '\u0C32\u0C48\u0C38\u0C46\u0C28\u0C4D\u0C38\u0C41\u0C32\u0C41', page: 'pages/licenses.html' }
        ]},
        { title: '\u0C38\u0C02\u0C2A\u0C4D\u0C30\u0C26\u0C3F\u0C02\u0C1A\u0C02\u0C21\u0C3F', links: [
          { label: '\u0C38\u0C02\u0C2A\u0C4D\u0C30\u0C26\u0C3F\u0C02\u0C1A\u0C02\u0C21\u0C3F', page: 'pages/contact.html' },
          { label: '\u0C38\u0C35\u0C30\u0C23\u0C32\u0C41', page: 'pages/corrections.html' },
          { label: '\u0C2E\u0C26\u0C4D\u0C26\u0C24\u0C41', page: 'pages/support.html' }
        ]}
      ],
      footerBottom: '&copy; 2026 \u0C06\u0C02\u0C27\u0C4D\u0C30 \u0C30\u0C3F\u0C15\u0C3E\u0C30\u0C4D\u0C21\u0C4D. \u0C38\u0C4D\u0C35\u0C24\u0C02\u0C24\u0C4D\u0C30 &middot; \u0C2A\u0C4D\u0C30\u0C1C\u0C3E\u0C39\u0C3F\u0C24\u0C02 &middot; \u0C2A\u0C3E\u0C20\u0C15 \u0C2E\u0C26\u0C4D\u0C26\u0C24\u0C41',
      langLabel: 'EN'
    }
  };

  function getTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (saved === 'dark' || saved === 'light') return saved;
    return 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    var btns = document.querySelectorAll('.theme-toggle');
    var icon = theme === 'dark' ? '\u2600' : '\u263D';
    for (var i = 0; i < btns.length; i++) btns[i].textContent = icon;
  }

  function getLang() {
    var p = location.pathname;
    if (p.indexOf('/en/') !== -1) return 'en';
    if (p.indexOf('/te/') !== -1) return 'te';
    var saved = null;
    try { saved = localStorage.getItem(LANG_KEY); } catch (e) {}
    if (saved === 'en' || saved === 'te') return saved;
    return 'en';
  }

  function setLang(lang) { try { localStorage.setItem(LANG_KEY, lang); } catch (e) {} }

  function switchLang() {
    var current = getLang();
    var target = current === 'en' ? 'te' : 'en';
    try { localStorage.setItem(LANG_KEY, target); } catch (e) {}
    location.href = location.pathname.replace('/' + current + '/', '/' + target + '/');
  }

  function getBase() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute('src') || '';
      if (src.indexOf('site-header.js') !== -1) return src.replace(/site-header\.js.*$/, '');
    }
    var p = location.pathname;
    if (p.indexOf('/pages/') !== -1 || p.indexOf('/reports/') !== -1) return '../../';
    return '../';
  }

  function getLangBase() {
    var p = location.pathname;
    if (p.indexOf('/pages/') !== -1 || p.indexOf('/reports/') !== -1) return '../';
    return '';
  }

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
    var lang = getLang();
    var s = STRINGS[lang];
    var langBase = getLangBase();
    var pagesBase = langBase + 'pages/';
    var theme = getTheme();

    document.documentElement.lang = lang;
    injectCSS(base);
    setTheme(theme);
    setLang(lang);

    // ── Header ──
    var el = document.getElementById('site-masthead');
    if (el) {
      var icon = theme === 'dark' ? '\u2600' : '\u263D';

      // Nav links data
      var navLinks = [
        { href: langBase + 'index.html', label: s.home, id: 'index' },
        { href: pagesBase + 'reports.html', label: s.reports, id: 'reports' },
        { href: pagesBase + 'about.html', label: s.about, id: 'about' },
        { href: pagesBase + 'support.html', label: s.support, id: 'support' }
      ];

      // Build nav HTML (used in both desktop and mobile)
      var navHTML = '';
      var mobileNavHTML = '';
      for (var n = 0; n < navLinks.length; n++) {
        var cls = navLinks[n].id === page ? ' class="is-current"' : '';
        navHTML += '<a href="' + navLinks[n].href + '"' + cls + '>' + navLinks[n].label + '</a>';
        mobileNavHTML += '<a href="' + navLinks[n].href + '"' + cls + '>' + navLinks[n].label + '</a>';
      }

      // Header bar
      el.innerHTML =
        '<header class="site-bar">' +
        '  <button class="burger" aria-label="Menu">&#9776;</button>' +
        '  <a href="' + langBase + 'index.html" class="site-bar__logo" aria-label="Andhra Record Home">' +
        '    <svg viewBox="0 0 220 36" width="150" height="24" xmlns="http://www.w3.org/2000/svg"><rect width="220" height="36" rx="3" fill="#8b1a1a"/><text x="110" y="25" text-anchor="middle" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-weight="800" font-size="18" fill="#fff" letter-spacing="3">ANDHRA RECORD</text></svg>' +
        '  </a>' +
        '  <nav class="site-bar__nav">' + navHTML + '</nav>' +
        '  <div class="site-bar__utils">' +
        '    <button class="theme-toggle" aria-label="Toggle dark mode">' + icon + '</button>' +
        '    <button class="lang-toggle" aria-label="Switch language">' + s.langLabel + '</button>' +
        '  </div>' +
        '</header>' +
        '<div class="mobile-menu">' + mobileNavHTML + '</div>';

      // Ticker
      var items = s.ticker;
      var tickerHTML = '<div class="ticker"><div class="ticker__track">';
      for (var t = 0; t < items.length; t++) tickerHTML += '<span class="ticker__item">' + items[t] + '</span><span class="ticker__sep">&#9670;</span>';
      for (var t2 = 0; t2 < items.length; t2++) tickerHTML += '<span class="ticker__item">' + items[t2] + '</span><span class="ticker__sep">&#9670;</span>';
      tickerHTML += '</div></div>';
      el.innerHTML += tickerHTML;

      // Bind burger
      var burger = el.querySelector('.burger');
      var mobileMenu = el.querySelector('.mobile-menu');
      if (burger && mobileMenu) {
        burger.addEventListener('click', function () {
          var open = mobileMenu.classList.toggle('mobile-menu--open');
          burger.innerHTML = open ? '&#10005;' : '&#9776;';
        });
      }

      // Bind toggles
      el.querySelector('.theme-toggle').addEventListener('click', function () { setTheme(getTheme() === 'dark' ? 'light' : 'dark'); });
      el.querySelector('.lang-toggle').addEventListener('click', switchLang);
    }

    // ── Footer ──
    var footerEl = document.getElementById('site-footer');
    if (footerEl) {
      var cols = s.footerCols;
      var gridHTML = '';
      for (var c = 0; c < cols.length; c++) {
        gridHTML += '<div class="site-footer__col"><h4>' + cols[c].title + '</h4>';
        for (var lk = 0; lk < cols[c].links.length; lk++) {
          var link = cols[c].links[lk];
          var href = link.external ? link.href : (link.isReport ? (langBase + link.page) : (langBase + link.page));
          var target = link.external ? ' target="_blank" rel="noopener"' : '';
          gridHTML += '<a href="' + href + '"' + target + '>' + link.label + '</a>';
        }
        gridHTML += '</div>';
      }

      footerEl.innerHTML =
        '<footer class="site-footer">' +
        '  <div class="site-footer__grid">' + gridHTML + '</div>' +
        '  <div class="site-footer__bottom">' + s.footerBottom + '</div>' +
        '</footer>';
    }
  }

  return { render: render, setTheme: setTheme, getTheme: getTheme, getLang: getLang, setLang: setLang, switchLang: switchLang };
})();

var AmaravatiHeader = AndhraRecord;
