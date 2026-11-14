/*
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

//Expanding and collapsing stack trace
$('.show').click(function () {
    var par = $(this).parent().parent().children("p")
    if (par.hasClass('show-all')) {
        par.removeClass('show-all')
        $(this).text('[+] Expand')
    } else {
        par.addClass('show-all');
        $(this).text('[-] Collapse')
    }
});



function expand_it(whichEl, link) {
    whichEl.style.display = (whichEl.style.display == "none") ? "" : "none";
}

function expand_http_details(whichEl, link) {
    whichEl.style.display = (whichEl.style.display == "none") ? "" : "none";
    if (link) {
        if (link.innerHTML) {
           if (whichEl.style.display == "none") {
                link.innerHTML = "Details";
           } else {
                link.innerHTML = "Hide";
           }
        }
    }
}

function expand_stack(whichEl, link) {
    // Lazy-load stack content from the thread detail page on the first expand.
    // An <iframe> is used instead of fetch() so this works when the report is
    // opened directly from disk (file:// URLs block cross-file fetch requests
    // in all major browsers).
    if (whichEl.style.display === "none" && !whichEl.dataset.loaded) {
        var url = whichEl.dataset.threadUrl;
        if (url) {
            var iframe = document.createElement('iframe');
            iframe.src = url;
            iframe.style.width = '100%';
            iframe.style.border = 'none';
            // Grow the iframe to fit its content once the page has loaded.
            iframe.onload = function() {
                try {
                    var body = iframe.contentDocument && iframe.contentDocument.body;
                    if (body) {
                        iframe.style.height = body.scrollHeight + 'px';
                    }
                } catch (e) { /* cross-origin guard – shouldn't happen for file:// */ }
            };
            whichEl.appendChild(iframe);
            whichEl.dataset.loaded = 'true';
        }
    }
    whichEl.style.display = (whichEl.style.display === "none") ? "" : "none";
}
