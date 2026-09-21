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
    whichEl.style.display = (whichEl.style.display == "none") ? "" : "none";
}

// Opens a collapsed section (if needed) and scrolls the heading into view.
// contentId: the id of the collapsible <div> for the section
// headingId:  the id of the section <h3> to scroll to
function tocGoto(contentId, headingId) {
    var content = document.getElementById(contentId);
    if (content && content.style.display === 'none') {
        content.style.display = '';
    }
    var heading = document.getElementById(headingId);
    if (heading) {
        heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
