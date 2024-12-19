/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

'use strict';

$(function () {
  $('#all_threads_table_thread_xsl').tablesorter({
    theme: 'blue',
    headers: {
      0: { sorter: false },
      1: { sorter: false },
      2: { sorter: false },
      3: { sorter: false },
      4: { sorter: false },
      5: { sorter: false },
    },
  });
});

// Needed for tooltips. See https://jqueryui.com/tooltip/
$( function() {
    $(document).tooltip();
} );

const loadChartCPUUsage = function() {

  const ctx = document.getElementById('myChartCPUUsage');

  // 1. get the list of javacores with timestamps
  const coresNumber = document.getElementById('javacores_files_table').rows.length;

  // 2. get the number of CPUs
  //const CPUsNumber = document.getElementById('sys_info_table').rows[1].cells[0].innerHTML;

  // 3. fetch the CPU usage from each row
  const inputData = [];
  const totalCPUs = [];
  const labels = [];

  for(let i=1; i < coresNumber; i++){
    let rowEl = document.getElementById('javacores_files_table').rows[i];
    inputData.push(Number(rowEl.cells[2].innerHTML));
    labels.push(new Date(rowEl.cells[1].innerHTML).valueOf());

    totalCPUs.push(100);
  }

  new Chart(ctx, {
    type: 'bar',
    responsive: true,
    data: {
     labels: labels,
      datasets: [
        {
          label: '% CPU Usage',
          data: inputData,
          borderColor: 'rgba(54,162,235,1)',
          backgroundColor: 'rgba(104,185,240,0.5)',
          borderWidth: 1
        },
        {
          label: '% Total CPUs',
          data: totalCPUs,
          borderWidth: 1,
          fillColor: "black",
          borderColor: "black",
          backgroundColor: "black",
          pointRadius: 0.0,
          type: 'line'
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        },
        x: {
           type: 'time',
           time: {
              unit: 'second'
           }
        }
      },
    },
  });

}


const loadChartGC = function() {

  const gcTable = document.querySelector('gc-collections');

  if(!gcTable.hasChildNodes()) {
     return;
  }

  const sysResourceE3Elem = document.getElementById('systemresources_myChartGC');
  if (sysResourceE3Elem) {
    sysResourceE3Elem.classList.remove('hide');
  }

  const ctx = document.getElementById('myChartGC');

  // 1. get the list of javacores with timestamps, to set the chart range (x range)
  const coresFiles = document.getElementById('javacores_files_table');
  const coresNumber = document.getElementById('javacores_files_table').rows.length;

  const coresTimestamps = [];
  const coresTimeRange = {
      'startTime': new Date(document.getElementById('javacores_files_table').rows[1].cells[1].innerHTML),
      'endTime': new Date(document.getElementById('javacores_files_table').rows[1].cells[1].innerHTML)
  };

  let startingPoint = coresTimeRange['startTime'];
  let endingPoint = coresTimeRange['endTime'];

  for(let i=2; i<coresNumber; i++){
    let rowEl = document.getElementById('javacores_files_table').rows[i];
    coresTimestamps.push(String(rowEl.cells[1].innerHTML));

    let timestamp = new Date(rowEl.cells[1].innerHTML);
    if(startingPoint > timestamp)
       startingPoint = timestamp;

    if(endingPoint < timestamp)
        endingPoint = timestamp;
  }

  coresTimeRange['startTime'] = startingPoint;
  coresTimeRange['endTime'] = endingPoint;

  // 2. get the list of gc collections with timestamps, to get the data to draw
  const gcCollectionsElms = document.querySelectorAll('gc-collection');
  const gcCollections = [];

  //  timestamp="2022-06-06T11:45:13.841" durationms="15.881" free-before="3219388536" free-after="3709718896" freed="490330360"/>
  gcCollectionsElms.forEach(function (element) {
    gcCollections.push( { 'startTime':  element.attributes[0],
                          'duration':   element.attributes[1],
                          'freeBefore': element.attributes[2],
                          'freeAfter':  element.attributes[3],
                          'freed':      element.attributes[4] })
  });

  // 3. find the HEAP_SIZE
  const MB_SIZE = Math.pow(1024, 2);
  let heapAsString = document.getElementById('sys_info_table').rows[2].cells[1].innerHTML;
  let HEAP_SIZE;
  let heapUnit = heapAsString.slice(-1).toLowerCase();

  if(!isNaN(Number(heapUnit))) {
     HEAP_SIZE = Number(heapAsString);
  }
  else {

      switch (heapUnit) {
        case "g":
            HEAP_SIZE =
                Number(heapAsString.slice(0, -1)) * MB_SIZE * 1024;
        break;
        case "m":
            HEAP_SIZE =
                Number(heapAsString.slice(0, -1)) * MB_SIZE;
        break;
        case "k":
            HEAP_SIZE =
                Number(heapAsString.slice(0, -1)) * 1024;
        break;
        default:
            console.log("Hmm, what now .. heap unit undefined!");
        break;
      }
  }

  // 4. create input data for GC chart
  //        start with gc collection done after the first javacore creation
  //        end with gc collection done after the last javacore was collected
  const inputData = [];
  const totalHeap = [];
  const labels = [];

  let dateTmp;
  gcCollections.forEach(function (element) {
      let gcStartDate = new Date(element['startTime'].textContent);

      // TODO - filter range
      //if( gcStartDate >= coresTimeRange['startTime'] && gcStartDate <= coresTimeRange['endTime']) {

        // before running GC
        inputData.push((HEAP_SIZE - Number(element['freeBefore'].textContent)) / MB_SIZE);
        totalHeap.push(HEAP_SIZE / MB_SIZE);
        labels.push(new Date(element['startTime'].textContent).valueOf());

        // result of GC execution
        inputData.push((HEAP_SIZE - Number(element['freeAfter'].textContent)) / MB_SIZE);
        totalHeap.push(HEAP_SIZE / MB_SIZE);
        dateTmp = new Date(element['startTime'].textContent);
        dateTmp.setMilliseconds(dateTmp.getMilliseconds() + Number(element['duration'].textContent.split('.')[0]));
        labels.push(dateTmp.valueOf());
  })

  new Chart(ctx, {
    type: 'line',
    responsive: true,
    data: {
     labels: labels,
      datasets: [
        {
          label: 'Heap Usage (MB)',
          data: inputData,
          borderWidth: 1,
          fillColor: 'rgba(255,99,132,0.5)',
          borderColor: 'rgba(255,99,132,1)',
          backgroundColor: 'rgba(255,99,132,0.5)',
          pointRadius: 0.5
        },
        {
          label: 'Total Heap (MB)',
          data: totalHeap,
          borderWidth: 1,
          fillColor: "black",
          borderColor: "black",
          backgroundColor: "black",
          pointRadius: 0.0
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: (HEAP_SIZE + 0.01*HEAP_SIZE) / MB_SIZE
        },
        x: {
             type: 'time',
             time: {
                   unit: 'second',
                   parser: 'dd-MM-yy HH:mm:ss'
             }
        }
      },
    },
  });

}

const loadChart = function () {
  const ctx = document.getElementById('myChart');

  // 1. count the number of snapshots
  const snapshotsNumber = document.getElementById('all_threads_table_thread_xsl').rows.length;

  // 2. fetch the CPU usage from each row
  const inputData = [];
  const labels = [];

  for(let i=1; i<snapshotsNumber; i++){
    let rowEl = document.getElementById('all_threads_table_thread_xsl').rows[i];
    inputData.push(Number(rowEl.cells[3].innerHTML));
    labels.push(String(rowEl.cells[0].innerHTML));
  }

  new Chart(ctx, {
    type: 'bar',
    responsive: true,
    data: {
     labels: labels,
      datasets: [
        {
          label: '% CPU Usage',
          data: inputData,
          borderWidth: 1,
          minBarLength: 7
        },
      ],
    },
    options: {
      layout: {
        padding: {
          // Section needed for fixing #179 - right bar is truncated
          left: 0,
          right: 4,
          top: 0,
          bottom: 0
         }
      },
      legend: {
	    display: true,
		onClick: () => {}, // disable legend onClick functionality that filters datasets
	  },
      scales: {
        y: {
          beginAtZero: true
        },
        x: {
          type: 'time',
          time: {
              unit: 'second',
              parser: 'dd-MM-yy HH:mm:ss'
            }
        }
      },
    },
  });
};
