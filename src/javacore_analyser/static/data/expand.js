/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

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
    //if (link) {
    //    if (link.innerHTML) {
    //       if (whichEl.style.display == "none") {
    //            link.innerHTML = "[+]".concat(link.innerHTML.substring(3));
    //       } else {
    //            link.innerHTML = "[-]".concat(link.innerHTML.substring(3));
    //       }
    //    }
    //}
}

function expand_stack(whichEl, link) {
    whichEl.style.display = (whichEl.style.display == "none") ? "" : "none";
}
