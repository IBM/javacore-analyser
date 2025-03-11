$(function(){
    $('#generated_reports_table').tablesorter({
        theme : 'blue',
        headers: {
            2: { sorter: false },
            3: { sorter: false },
        },
    });
});
