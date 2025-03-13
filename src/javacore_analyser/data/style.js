/*
Copyright IBM Corp. 2025 - 2026
SPDX-License-Identifier: Apache-2.0
*/

$(function(){
    $('#generated_reports_table').tablesorter({
        theme : 'blue',
        headers: {
            2: { sorter: false },
            3: { sorter: false },
        },
    });
});
