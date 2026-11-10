/*
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

$(function(){
    // Set blue theme as default for all tablesorter instances
    $.extend($.tablesorter.defaults, {
        theme: 'blue'
    });

    // sys_info_table: all columns are display-only, sorting is disabled.
    // The zebra/columns widgets and sort options are set further below.
    $('#sys_info_table').tablesorter({
        widgets: ['zebra', 'columns'],
        sortInitialOrder: 'desc',
        usNumberFormat: false,
        sortReset: true,
        sortRestart: true,
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false },
            3: { sorter: false },
            4: { sorter: false },
            5: { sorter: false },
            6: { sorter: false },
            7: { sorter: false },
            8: { sorter: false },
            9: { sorter: false }
        },
    });

    $('#javacores_files_table').tablesorter({
        headers: {
            1: { sorter: false },
        },
    });

    $('#verbose_gc_files_table').tablesorter({
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false }
        },
    });

    $('#har_files_table').tablesorter({
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false }
        },
    });

    $('#plugin_files_table').tablesorter({
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false }
        },
    });

    $('#java_arguments_table').tablesorter({
        widgets : ['zebra', 'columns'],
        sortInitialOrder: 'desc',
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    $('#top10_blocker_table').tablesorter({
        // the default order
        sortInitialOrder: 'asc',
        // sorting order in the selected column
        headers : {
            1 : { sortInitialOrder: 'desc'  }
        },
        widgets : ['zebra', 'columns'],
        sortReset : true,
        sortRestart : true
    });

    $('#all_threads_table').tablesorter({
        widgets : ['zebra', 'columns'],
        // initial sorting order
        sortList: [
          [1, 1]
        ],
        // the default order
        sortInitialOrder: 'desc',
        // sorting order in the selected column
        headers : {
            0 : { sortInitialOrder: 'asc'  }
        },
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    $('#allCodeTable').tablesorter({
        widgets : ['zebra', 'columns'],
        sortList: [
          [2, 1]
        ],
        sortInitialOrder: 'desc',
        headers : {
            0 : { sortInitialOrder: 'asc'  }
        },
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    $('#HttpCallTable').tablesorter({
        widgets : ['zebra', 'columns'],
        sortList: [
          [2, 1]
        ],
        sortInitialOrder: 'asc',
        headers : {
            0 : { sortInitialOrder: 'asc'  }
        },
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    // Initialize any remaining tables with tablesorter class that haven't been initialized yet
    // This handles plugin-generated tables and other dynamic content
    $('table.tablesorter').each(function() {
        const $table = $(this);
        // Check if table is already initialized by checking for tablesorter-specific classes
        if (!$table.hasClass('tablesorter-blue') && !$table.hasClass('tablesorter-default')) {
            $table.tablesorter({
                widgets : ['zebra', 'columns'],
                sortInitialOrder: 'desc',
                usNumberFormat : false,
                sortReset : true,
                sortRestart : true
            });
        }
    });
});

// Made with Bob
