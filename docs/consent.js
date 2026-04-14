/* ================================================================
   The Amaravati Record — Cookie Consent + GA4 Integration
   ----------------------------------------------------------------
   Purpose: show a minimal consent banner, honor Do Not Track and
            Global Privacy Control automatically, and load Google
            Analytics 4 only if the reader explicitly accepts.
   Zero third-party dependencies. No CDN. Self-contained.
   ================================================================ */

(function () {
  'use strict';

  // ----------------------------------------------------------------
  // Configuration — replace the placeholder when you create your
  // GA4 property (Google Analytics → Admin → Data Streams → Measurement ID).
  // The format is always "G-XXXXXXXXXX". Until this is replaced,
  // clicking "Accept" will do nothing (no network request is made)
  // because the script loader guards against the placeholder.
  // ----------------------------------------------------------------
  var GA4_MEASUREMENT_ID = 'G-E1WVK9GMFP';
  var STORAGE_KEY = 'amaravatirecord_consent_v1';

  // ----------------------------------------------------------------
  // Google Consent Mode v2 — set defaults BEFORE anything loads.
  // This is the documented way to run GA4 in a consent-aware site.
  // ----------------------------------------------------------------
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted',
    personalization_storage: 'denied',
    security_storage: 'granted',
    wait_for_update: 500
  });

  // ----------------------------------------------------------------
  // Honor Do Not Track / Global Privacy Control — if the browser
  // sends either signal, treat it as a silent "reject" and never
  // show the banner. This is required for GPC compliance in
  // California (CCPA) and is a good-faith signal to honor DNT.
  // ----------------------------------------------------------------
  function honoringPrivacySignal() {
    if (navigator.globalPrivacyControl) return 'GPC';
    if (window.doNotTrack === '1' ||
        navigator.doNotTrack === '1' ||
        navigator.doNotTrack === 'yes' ||
        navigator.msDoNotTrack === '1') return 'DNT';
    return null;
  }

  // ----------------------------------------------------------------
  // Storage helpers — we use localStorage, not a cookie, so the
  // consent record itself does not require consent to exist.
  // ----------------------------------------------------------------
  function readConsent() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return null;
      return parsed;
    } catch (e) {
      return null;
    }
  }

  function writeConsent(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        analytics: !!state.analytics,
        updated_at: new Date().toISOString(),
        version: 1
      }));
    } catch (e) { /* storage blocked; fail silently */ }
  }

  // ----------------------------------------------------------------
  // GA4 loader — only called if consent is granted AND the
  // measurement ID has been configured. Lazy-loads the gtag.js
  // script from googletagmanager.com.
  // ----------------------------------------------------------------
  function loadGA4() {
    if (!GA4_MEASUREMENT_ID || GA4_MEASUREMENT_ID === 'G-PLACEHOLDER') {
      // eslint-disable-next-line no-console
      console.info('[consent] GA4 measurement ID not configured; skipping load');
      return;
    }
    if (window.__AR_GA4_LOADED__) return;
    window.__AR_GA4_LOADED__ = true;

    gtag('consent', 'update', {
      analytics_storage: 'granted'
    });

    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' +
            encodeURIComponent(GA4_MEASUREMENT_ID);
    document.head.appendChild(s);

    gtag('js', new Date());
    gtag('config', GA4_MEASUREMENT_ID, {
      anonymize_ip: true,
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
  }

  function revokeGA4() {
    gtag('consent', 'update', {
      analytics_storage: 'denied'
    });
  }

  // ----------------------------------------------------------------
  // Banner rendering — creates the DOM for the consent banner.
  // Styling is inline so we don't need to add to styles.css and
  // the banner works even if the main stylesheet failed to load.
  // ----------------------------------------------------------------
  function renderBanner() {
    var existing = document.getElementById('ar-consent-banner');
    if (existing) existing.remove();

    var banner = document.createElement('div');
    banner.id = 'ar-consent-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-live', 'polite');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.innerHTML = [
      '<style>',
      '  #ar-consent-banner {',
      '    position: fixed;',
      '    left: 0; right: 0; bottom: 0;',
      '    background: #1a1715;',
      '    color: #faf8f4;',
      '    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;',
      '    font-size: 13px;',
      '    line-height: 1.5;',
      '    padding: 16px 20px;',
      '    z-index: 9999;',
      '    border-top: 3px solid #8b1a1a;',
      '    box-shadow: 0 -2px 8px rgba(0,0,0,0.15);',
      '  }',
      '  #ar-consent-banner .ar-consent__inner {',
      '    max-width: 1100px;',
      '    margin: 0 auto;',
      '    display: flex;',
      '    gap: 18px;',
      '    align-items: center;',
      '    flex-wrap: wrap;',
      '    justify-content: space-between;',
      '  }',
      '  #ar-consent-banner p {',
      '    margin: 0;',
      '    flex: 1 1 300px;',
      '  }',
      '  #ar-consent-banner a {',
      '    color: #faf8f4;',
      '    text-decoration: underline;',
      '  }',
      '  #ar-consent-banner .ar-consent__actions {',
      '    display: flex;',
      '    gap: 10px;',
      '    flex-shrink: 0;',
      '  }',
      '  #ar-consent-banner button {',
      '    font-family: inherit;',
      '    font-size: 11px;',
      '    font-weight: 700;',
      '    text-transform: uppercase;',
      '    letter-spacing: 1.5px;',
      '    padding: 9px 16px;',
      '    border: 1px solid #faf8f4;',
      '    background: transparent;',
      '    color: #faf8f4;',
      '    cursor: pointer;',
      '    min-width: 90px;',
      '  }',
      '  #ar-consent-banner button.ar-consent__accept {',
      '    background: #faf8f4;',
      '    color: #1a1715;',
      '  }',
      '  #ar-consent-banner button:hover {',
      '    opacity: 0.88;',
      '  }',
      '  @media (max-width: 600px) {',
      '    #ar-consent-banner { font-size: 12px; padding: 14px 16px; }',
      '    #ar-consent-banner .ar-consent__inner { gap: 12px; }',
      '    #ar-consent-banner .ar-consent__actions { width: 100%; }',
      '    #ar-consent-banner button { flex: 1 1 0; }',
      '  }',
      '</style>',
      '<div class="ar-consent__inner">',
      '  <p>',
      '    <strong>Analytics cookies &mdash; your choice.</strong> ',
      '    The Amaravati Record uses Google Analytics 4 to understand how readers find our work, ',
      '    with IP anonymization enabled. No cookies are set unless you accept. ',
      '    See the <a href="' + (location.pathname.indexOf('/pages/') !== -1 ? '' : (location.pathname.indexOf('/reports/') !== -1 ? '../pages/' : 'pages/')) + 'cookies.html">cookie notice</a> or <a href="' + (location.pathname.indexOf('/pages/') !== -1 ? '' : (location.pathname.indexOf('/reports/') !== -1 ? '../pages/' : 'pages/')) + 'privacy.html">privacy policy</a> for details.',
      '  </p>',
      '  <div class="ar-consent__actions">',
      '    <button type="button" class="ar-consent__reject" aria-label="Reject analytics cookies">Reject</button>',
      '    <button type="button" class="ar-consent__accept" aria-label="Accept analytics cookies">Accept</button>',
      '  </div>',
      '</div>'
    ].join('\n');

    banner.querySelector('.ar-consent__accept').addEventListener('click', function () {
      writeConsent({ analytics: true });
      loadGA4();
      banner.remove();
    });

    banner.querySelector('.ar-consent__reject').addEventListener('click', function () {
      writeConsent({ analytics: false });
      revokeGA4();
      banner.remove();
    });

    document.body.appendChild(banner);
  }

  // ----------------------------------------------------------------
  // Public API — readers can click the "Cookie settings" link in
  // the footer to re-open the banner and change their mind.
  // ----------------------------------------------------------------
  window.AmaravatRecord_openConsent = function () {
    renderBanner();
    return false;
  };

  // ----------------------------------------------------------------
  // Boot — decide what to do on page load.
  //   1. If DNT or GPC is set: silently reject, never show banner
  //   2. If user has a stored choice: honor it
  //   3. Otherwise: show the banner
  // ----------------------------------------------------------------
  function boot() {
    var privacySignal = honoringPrivacySignal();
    if (privacySignal) {
      writeConsent({ analytics: false });
      revokeGA4();
      return;
    }

    var stored = readConsent();
    if (stored) {
      if (stored.analytics) loadGA4();
      else revokeGA4();
      return;
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderBanner);
    } else {
      renderBanner();
    }
  }

  boot();
})();
