/*
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

/**
 * Renders the stack trace data for a single thread into its placeholder div.
 *
 * The placeholder div carries two data attributes written by all_threads.xsl:
 *   data-stack-index   – integer index into window.THREAD_STACKS
 *   data-thread-address – java/lang/Thread address string
 *
 * The function is idempotent: calling it on an already-populated div is safe.
 *
 * @param {HTMLElement} div  The placeholder <div> with data-stack-index set.
 */
function populateStackPlaceholder(div) {
  if (!div || div.dataset.stackLoaded === 'true') return;
  var idx = div.dataset.stackIndex;
  if (idx === undefined || idx === null) return;

  var stacks = window.THREAD_STACKS;
  if (!stacks) return;

  var snapshots = stacks[String(idx)];
  if (!snapshots) return;

  var address = div.dataset.threadAddress || '';
  var html = 'java/lang/Thread:' + escapeHtml(address);

  var DISPLAYED_STACK_DEPTH = 50;  // must match $displayed_stack_depth in report.xsl

  for (var s = 0; s < snapshots.length; s++) {
    var snap = snapshots[s];
    html += '<br/><strong>Timestamp: ' + escapeHtml(snap.timestamp) + '</strong>';
    html += '<div>';
    if (snap.stack_depth > 0) {
      html += '<div class="toggle_expand"><a href="javaScript:;" class="show">[+] Expand</a></div>';
      html += '<p class="stacktrace">';
      var lines = snap.lines;
      for (var l = 0; l < lines.length && l < DISPLAYED_STACK_DEPTH; l++) {
        html += '<span class="' + escapeHtml(lines[l].kind) + '">'
             + escapeHtml(lines[l].text)
             + '</span><br/>';
      }
      if (snap.stack_depth > DISPLAYED_STACK_DEPTH) {
        html += '<span>...</span><br/>';
      }
      html += '</p>';
    } else {
      html += 'No Stack';
    }
    html += '</div>';
  }

  div.innerHTML = html;
  div.dataset.stackLoaded = 'true';

  // Re-bind the expand/collapse click handlers for any newly created .show links.
  $(div).find('.show').off('click').on('click', function () {
    var par = $(this).parent().parent().children('p');
    if (par.hasClass('show-all')) {
      par.removeClass('show-all');
      $(this).text('[+] Expand');
    } else {
      par.addClass('show-all');
      $(this).text('[-] Collapse');
    }
  });
}

/**
 * Populates ALL stack placeholder divs in the document.
 * Called by search.js before running a text search so that jquery.mark
 * can find text inside stack traces.
 */
function populateAllStackPlaceholders() {
  var divs = document.querySelectorAll('[data-stack-index]');
  for (var i = 0; i < divs.length; i++) {
    populateStackPlaceholder(divs[i]);
  }
}

/**
 * Minimal HTML-escape helper to prevent XSS when inserting user data via innerHTML.
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
