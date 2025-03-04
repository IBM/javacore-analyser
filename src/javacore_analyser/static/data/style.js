$(function(){
    $('#sys_info_table').tablesorter({
        theme : 'blue',
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
        theme : 'blue',
        headers: {
            1: { sorter: false },
        },
    });

    $('#verbose_gc_files_table').tablesorter({
        theme : 'blue',
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false }
        },
    });

    $('#har_files_table').tablesorter({
        theme : 'blue',
        headers: {
            0: { sorter: false },
            1: { sorter: false },
            2: { sorter: false }
        },
    });

    $('#java_arguments_table').tablesorter({
        theme : 'blue',
        widgets : ['zebra', 'columns'],
        sortInitialOrder: 'desc',
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    $('#sys_info_table').tablesorter({
        theme : 'blue',
        widgets : ['zebra', 'columns'],
        sortInitialOrder: 'desc',
        usNumberFormat : false,
        sortReset : true,
        sortRestart : true
    });

    $('#top10_blocker_table').tablesorter({
        theme : 'blue',
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
        theme : 'blue',
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
        theme : 'blue',
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
        theme : 'blue',
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
});