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

  function updateButtons(mode) {
    const label = 'Theme: ' + MODE_LABELS[mode];
    document.querySelectorAll('[data-theme-toggle]').forEach(function(button) {
      button.textContent = label;
      button.setAttribute('aria-label', label + '. Activate to change theme.');
      button.setAttribute('title', label);
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
