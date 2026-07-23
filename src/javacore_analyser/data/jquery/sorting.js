/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

$(function(){
    $('#javacore_threads_table').tablesorter({
        theme : 'blue',
        headers: {
            0: { sorter: true },
            1: { sorter: true },
            2: { sorter: true },
            3: { sorter: true },
            4: { sorter: true }
        },
    });
});