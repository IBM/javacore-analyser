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
