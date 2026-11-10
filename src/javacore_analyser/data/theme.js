/*
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0
*/

// Theme switcher for the generated HTML reports.
//
// The user can choose between three modes, cycled by the #theme-toggle button:
//   system - follow the device (prefers-color-scheme), updating live
//   light  - always use the Carbon "White" theme
//   dark   - always use the Carbon "Gray 100" theme
//
// The choice is persisted in localStorage and shared by all pages of a report.
// This script is loaded in <head> so the theme is applied before first paint.
// A 'themechange' event is dispatched on document whenever the effective theme
// changes, so other scripts (e.g. charts) can re-render.

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

(function() {
  const STORAGE_KEY = 'javacore-analyser-theme';
  const MODES = ['system', 'light', 'dark'];
  const MODE_LABELS = { system: 'Device', light: 'Light', dark: 'Dark' };
  const THEME_CLASSES = { light: 'cds--white', dark: 'cds--g100' };
  const ALL_CARBON_THEME_CLASSES = ['cds--white', 'cds--g10', 'cds--g90', 'cds--g100'];

  const darkQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function readMode() {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      return MODES.indexOf(stored) >= 0 ? stored : 'system';
    } catch (e) {
      return 'system'; // storage unavailable (e.g. blocked by browser settings)
    }
  }

  function saveMode(mode) {
    try {
      window.localStorage.setItem(STORAGE_KEY, mode);
    } catch (e) {
      // Ignore: the preference simply will not persist.
    }
  }

  function resolveTheme(mode) {
    if (mode === 'system') {
      return darkQuery && darkQuery.matches ? 'dark' : 'light';
    }
    return mode;
  }

  // Static icon markup (monitor / sun / moon). CSS shows the one matching html[data-theme-mode].
  const ICON_ATTRS = 'class="theme-icon theme-icon--%s" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" ' +
    'width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true" focusable="false"';
  const BUTTON_HTML =
    '<svg ' + ICON_ATTRS.replace('%s', 'system') + '><rect x="1" y="2" width="14" height="9" rx="1"/>' +
    '<path d="M5 14h6M8 11v3"/></svg>' +
    '<svg ' + ICON_ATTRS.replace('%s', 'light') + '><circle cx="8" cy="8" r="3"/>' +
    '<path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13M3 13l1.4-1.4M11.6 4.4L13 3"/></svg>' +
    '<svg ' + ICON_ATTRS.replace('%s', 'dark') + '><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z"/></svg>' +
    '<span class="theme-toggle__label" data-theme-label=""></span>';

  function updateButtons(mode) {
    const label = 'Theme: ' + MODE_LABELS[mode];
    document.querySelectorAll('[data-theme-toggle]').forEach(function(button) {
      if (!button.querySelector('[data-theme-label]')) {
        button.innerHTML = BUTTON_HTML;
      }
      button.querySelector('[data-theme-label]').textContent = label;
      button.setAttribute('aria-label', label + '. Activate to change theme.');
      button.setAttribute('title', label + ' (click to change)');
    });
  }

  let currentMode = readMode();

  function applyTheme(mode, notify) {
    const theme = resolveTheme(mode);
    const root = document.documentElement;
    root.classList.remove.apply(root.classList, ALL_CARBON_THEME_CLASSES);
    root.classList.add(THEME_CLASSES[theme]);
    root.setAttribute('data-theme-mode', mode);
    updateButtons(mode);
    if (notify) {
      document.dispatchEvent(new CustomEvent('themechange', { detail: { mode: mode, theme: theme } }));
    }
  }

  applyTheme(currentMode, false);

  if (darkQuery) {
    const onSystemChange = function() {
      if (currentMode === 'system') {
        applyTheme(currentMode, true);
      }
    };
    if (darkQuery.addEventListener) {
      darkQuery.addEventListener('change', onSystemChange);
    } else if (darkQuery.addListener) {
      darkQuery.addListener(onSystemChange); // Safari < 14
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    updateButtons(currentMode);
    document.querySelectorAll('[data-theme-toggle]').forEach(function(button) {
      button.addEventListener('click', function() {
        currentMode = MODES[(MODES.indexOf(currentMode) + 1) % MODES.length];
        saveMode(currentMode);
        applyTheme(currentMode, true);
      });
    });
  });

  // Keep several open report tabs in sync.
  window.addEventListener('storage', function(event) {
    if (event.key === STORAGE_KEY) {
      currentMode = readMode();
      applyTheme(currentMode, true);
    }
  });
})();

// Made with Bob
