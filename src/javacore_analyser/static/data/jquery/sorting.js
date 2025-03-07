/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

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