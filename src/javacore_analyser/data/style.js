/*
Copyright IBM Corp. 2025 - 2026
SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

$(function(){
    $('#generated_reports_table').tablesorter({
        theme : 'blue',
        headers: {
            2: { sorter: false },
            3: { sorter: false },
        },
    });
});
