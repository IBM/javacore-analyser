/*
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

const TOTAL_CPU_PERCENTAGE = 100;
const HEAP_PADDING_PERCENTAGE = 0.01;
const MB_SIZE = Math.pow(1024, 2);

// ---------------------------------------------------------------------------
// Shared Chart.js configuration fragments
// ---------------------------------------------------------------------------

/**
 * Zoom/pan plugin configuration reused by every chart.
 * Allows wheel zoom, pinch zoom and panning on both axes,
 * clamped to the original data range.
 */
const ZOOM_PLUGIN_CONFIG = {
  zoom: {
    wheel: { enabled: true },
    pinch: { enabled: true },
    mode: 'xy',
  },
  pan: {
    enabled: true,
    mode: 'xy',
  },
  limits: {
    x: { min: 'original', max: 'original' },
    y: { min: 'original', max: 'original' },
  },
};

/**
 * displayFormats for time-based X axes.  Shared by the GC, CPU and
 * Thread-Classifications charts so the format strings stay in one place.
 */
const TIME_AXIS_DISPLAY_FORMATS = {
  millisecond: 'HH:mm:ss.SSS',
  second: 'HH:mm:ss',
  minute: 'HH:mm',
  hour: 'MMM dd HH:mm',
  day: 'MMM dd',
  week: 'MMM dd',
  month: 'MMM yyyy',
  quarter: 'MMM yyyy',
  year: 'yyyy',
};

// Distinct colours for up to 13 classification categories (12 named + unknown).
const CLASSIFICATION_COLOURS = [
  'rgba(255,99,132,1)',
  'rgba(54,162,235,1)',
  'rgba(75,192,192,1)',
  'rgba(255,159,64,1)',
  'rgba(153,102,255,1)',
  'rgba(46,139,87,1)',
  'rgba(255,205,86,1)',
  'rgba(205,92,92,1)',
  'rgba(0,128,128,1)',
  'rgba(128,0,128,1)',
  'rgba(0,0,205,1)',
  'rgba(210,105,30,1)',
  'rgba(128,128,128,1)',
];

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

/**
 * Returns the inner text of a table cell, trimming whitespace.
 * @param {HTMLTableRowElement} row
 * @param {number} cellIndex
 * @returns {string}
 */
function getCellText(row, cellIndex) {
  return row.cells[cellIndex].innerHTML.trim();
}

/**
 * Parses the heap size string from the system-information table into bytes.
 * Returns 0 if the table or row is not present.
 * @returns {number} Heap size in bytes.
 */
function parseHeapSizeFromTable() {
  const sysInfoTable = document.getElementById('sys_info_table');
  if (!sysInfoTable || sysInfoTable.rows.length <= 2) {
    return 0;
  }

  const heapAsString = sysInfoTable.rows[2].cells[1].innerHTML;
  const heapUnit = heapAsString.slice(-1).toLowerCase();

  if (!isNaN(Number(heapUnit))) {
    return Number(heapAsString);
  }

  switch (heapUnit) {
    case 'g':
      return Number(heapAsString.slice(0, -1)) * MB_SIZE * 1024;
    case 'm':
      return Number(heapAsString.slice(0, -1)) * MB_SIZE;
    case 'k':
      return Number(heapAsString.slice(0, -1)) * 1024;
    default:
      console.log('Hmm, what now .. heap unit undefined!');
      return 0;
  }
}

/**
 * Estimates the heap size from GC collection data when the system-info table
 * is absent.  Uses the maximum observed (freeBefore + freed) value.
 * @param {Array<Object>} gcCollections
 * @returns {number} Estimated heap size in bytes.
 */
function estimateHeapSizeFromGC(gcCollections) {
  let maxHeap = 0;
  gcCollections.forEach(function(element) {
    const estimatedHeap = Number(element['freeBefore']) + Number(element['freed']);
    if (estimatedHeap > maxHeap) {
      maxHeap = estimatedHeap;
    }
  });
  return maxHeap;
}

// ---------------------------------------------------------------------------
// jQuery / tablesorter initialisation
// ---------------------------------------------------------------------------

$(function() {
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
$(function() {
  $(document).tooltip();
});

// ---------------------------------------------------------------------------
// Chart: CPU Usage
// ---------------------------------------------------------------------------

const loadChartCPUUsage = function() {

  const ctx = document.getElementById('myChartCPUUsage');

  const javacoresTable = document.getElementById('javacores_files_table');
  const coresNumber = javacoresTable.rows.length;

  const inputData = [];
  const totalCPUs = [];
  const labels = [];

  for (let i = 1; i < coresNumber; i++) {
    const rowEl = javacoresTable.rows[i];
    inputData.push(Number(getCellText(rowEl, 2)));
    labels.push(new Date(getCellText(rowEl, 1)).valueOf());
    totalCPUs.push(TOTAL_CPU_PERCENTAGE);
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
          borderWidth: 1,
        },
        {
          label: '% Total CPUs',
          data: totalCPUs,
          borderWidth: 1,
          fillColor: 'black',
          borderColor: 'black',
          backgroundColor: 'black',
          pointRadius: 0.0,
          type: 'line',
        },
      ],
    },
    options: {
      scales: {
        y: { beginAtZero: true },
        x: {
          type: 'time',
          time: { unit: 'second' },
        },
      },
      plugins: {
        zoom: ZOOM_PLUGIN_CONFIG,
      },
    },
  });
};

// ---------------------------------------------------------------------------
// Chart: Garbage Collection Activity
// ---------------------------------------------------------------------------

const loadChartGC = function() {

  const gcTable = document.querySelector('gc-collections');

  if (!gcTable) {
    console.log('gc-collections element not found');
    return;
  }

  const gcCollectionElements = gcTable.querySelectorAll('gc-collection');
  if (gcCollectionElements.length === 0) {
    console.log('No gc-collection elements found');
    return;
  }

  const sysResourceE3Elem = document.getElementById('systemresources_myChartGC');
  if (sysResourceE3Elem) {
    sysResourceE3Elem.classList.remove('hide');
  } else {
    console.log('Chart container systemresources_myChartGC not found');
  }

  const ctx = document.getElementById('myChartGC');
  if (!ctx) {
    console.log('Canvas element myChartGC not found');
    return;
  }

  // Build the array of GC collection objects from the custom HTML elements
  const gcCollections = [];
  gcCollectionElements.forEach(function(element) {
    gcCollections.push({
      startTime:          element.getAttribute('timestamp'),
      duration:           element.getAttribute('durationms'),
      freeBefore:         element.getAttribute('free-before'),
      freeAfter:          element.getAttribute('free-after'),
      freed:              element.getAttribute('freed'),
      nurseryFreeBefore:  element.getAttribute('nursery-free-before'),
      nurseryFreeAfter:   element.getAttribute('nursery-free-after'),
      nurseryTotal:       element.getAttribute('nursery-total'),
      tenureFreeBefore:   element.getAttribute('tenure-free-before'),
      tenureFreeAfter:    element.getAttribute('tenure-free-after'),
      tenureTotal:        element.getAttribute('tenure-total'),
    });
  });

  // Resolve heap size: prefer explicit table value, fall back to GC estimation
  const HEAP_SIZE = parseHeapSizeFromTable() || estimateHeapSizeFromGC(gcCollections);

  // Build chart datasets
  const inputData       = [];
  const totalHeap       = [];
  const pauseTimeData   = [];
  const nurseryUsageData = [];
  const tenureUsageData  = [];
  const nurseryTotalData = [];
  const tenureTotalData  = [];
  const labels          = [];

  console.log(`Processing ${gcCollections.length} GC collections`);
  console.log(`HEAP_SIZE: ${HEAP_SIZE} bytes (${HEAP_SIZE / MB_SIZE} MB)`);

  gcCollections.forEach(function(element) {
    const durationMs   = Number(element['duration']);
    const gcStartTime  = new Date(element['startTime']).valueOf();
    const nurseryTotal = Number(element['nurseryTotal']);
    const tenureTotal  = Number(element['tenureTotal']);

    // Data point: state before GC
    inputData.push((HEAP_SIZE - Number(element['freeBefore'])) / MB_SIZE);
    totalHeap.push(HEAP_SIZE / MB_SIZE);
    nurseryUsageData.push(nurseryTotal > 0 ? (nurseryTotal - Number(element['nurseryFreeBefore'])) / MB_SIZE : null);
    tenureUsageData.push(tenureTotal > 0  ? (tenureTotal  - Number(element['tenureFreeBefore']))  / MB_SIZE : null);
    nurseryTotalData.push(nurseryTotal > 0 ? nurseryTotal / MB_SIZE : null);
    tenureTotalData.push(tenureTotal > 0  ? tenureTotal  / MB_SIZE : null);
    labels.push(gcStartTime);
    pauseTimeData.push(durationMs);

    // Data point: state after GC
    inputData.push((HEAP_SIZE - Number(element['freeAfter'])) / MB_SIZE);
    totalHeap.push(HEAP_SIZE / MB_SIZE);
    nurseryUsageData.push(nurseryTotal > 0 ? (nurseryTotal - Number(element['nurseryFreeAfter'])) / MB_SIZE : null);
    tenureUsageData.push(tenureTotal > 0  ? (tenureTotal  - Number(element['tenureFreeAfter']))  / MB_SIZE : null);
    nurseryTotalData.push(nurseryTotal > 0 ? nurseryTotal / MB_SIZE : null);
    tenureTotalData.push(tenureTotal > 0  ? tenureTotal  / MB_SIZE : null);
    pauseTimeData.push(null);
    const gcEndTime = new Date(element['startTime']);
    gcEndTime.setMilliseconds(gcEndTime.getMilliseconds() + durationMs);
    labels.push(gcEndTime.valueOf());
  });

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
          pointRadius: 0.5,
          yAxisID: 'y',
        },
        {
          label: 'Total Heap (MB)',
          data: totalHeap,
          borderWidth: 1,
          fillColor: 'black',
          borderColor: 'black',
          backgroundColor: 'black',
          pointRadius: 0.0,
          yAxisID: 'y',
        },
        {
          label: 'Pause Time (ms)',
          data: pauseTimeData,
          type: 'bar',
          borderWidth: 1,
          borderColor: 'rgba(54,162,235,1)',
          backgroundColor: 'rgba(54,162,235,0.5)',
          yAxisID: 'yPause',
          barPercentage: 1.0,
          categoryPercentage: 1.0,
          barThickness: 6,
          maxBarThickness: 9,
          order: 1,
        },
        {
          label: 'Nursery Usage (MB)',
          data: nurseryUsageData,
          borderWidth: 1,
          borderColor: 'rgba(75,192,192,1)',
          backgroundColor: 'rgba(75,192,192,0.2)',
          pointRadius: 0.5,
          yAxisID: 'y',
          hidden: true,
        },
        {
          label: 'Tenure Usage (MB)',
          data: tenureUsageData,
          borderWidth: 1,
          borderColor: 'rgba(255,159,64,1)',
          backgroundColor: 'rgba(255,159,64,0.2)',
          pointRadius: 0.5,
          yAxisID: 'y',
          hidden: true,
        },
        {
          label: 'Nursery Total (MB)',
          data: nurseryTotalData,
          borderWidth: 1,
          fillColor: 'rgba(46,139,87,1)',
          borderColor: 'rgba(46,139,87,1)',
          backgroundColor: 'rgba(46,139,87,1)',
          pointRadius: 0.0,
          yAxisID: 'y',
          hidden: true,
        },
        {
          label: 'Tenure Total (MB)',
          data: tenureTotalData,
          borderWidth: 1,
          fillColor: 'rgba(205,92,92,1)',
          borderColor: 'rgba(205,92,92,1)',
          backgroundColor: 'rgba(205,92,92,1)',
          pointRadius: 0.0,
          yAxisID: 'y',
          hidden: true,
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: (HEAP_SIZE + HEAP_PADDING_PERCENTAGE * HEAP_SIZE) / MB_SIZE,
          title: {
            display: true,
            text: 'Heap Usage (MB)',
          },
        },
        yPause: {
          beginAtZero: true,
          position: 'right',
          title: {
            display: true,
            text: 'Pause Time (ms)',
          },
          grid: { drawOnChartArea: false },
        },
        x: {
          type: 'time',
          time: { displayFormats: TIME_AXIS_DISPLAY_FORMATS },
        },
      },
      plugins: {
        zoom: ZOOM_PLUGIN_CONFIG,
      },
    },
  });

  console.log('GC Chart created successfully');
};

// ---------------------------------------------------------------------------
// Chart: Per-thread CPU Usage (thread drill-down page)
// ---------------------------------------------------------------------------

const loadChart = function() {
  const ctx = document.getElementById('myChart');

  const threadsTable = document.getElementById('all_threads_table_thread_xsl');
  const snapshotsNumber = threadsTable.rows.length;

  const inputData = [];
  const labels    = [];

  for (let i = 1; i < snapshotsNumber; i++) {
    const rowEl = threadsTable.rows[i];
    const value = Number(rowEl.cells[3].innerText);
    if (!isNaN(value)) {
      inputData.push(value);
      labels.push(String(rowEl.cells[0].innerText));
    }
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
          minBarLength: 7,
        },
      ],
    },
    options: {
      layout: {
        padding: {
          // Fixes #179 — right-most bar was truncated
          left: 0,
          right: 4,
          top: 0,
          bottom: 0,
        },
      },
      legend: {
        display: true,
        onClick: () => {}, // disable legend onClick that would filter datasets
      },
      scales: {
        y: { beginAtZero: true },
        x: {
          type: 'time',
          time: {
            unit: 'second',
            parser: 'dd-MM-yy HH:mm:ss',
          },
        },
      },
      plugins: {
        zoom: ZOOM_PLUGIN_CONFIG,
      },
    },
  });
};

// ---------------------------------------------------------------------------
// Chart: Thread Classifications Over Time
// ---------------------------------------------------------------------------

/**
 * loadChartThreadClassifications – reads per-javacore classification counts
 * from the hidden table emitted by system_resources.xsl and renders a
 * multi-line Chart.js chart: X axis = javacore timestamp, Y axis = number of
 * thread snapshots, one line per classification category.
 */
const loadChartThreadClassifications = function() {

  const ctx = document.getElementById('myChartThreadClassifications');
  if (!ctx) return;

  const dataTable = document.getElementById('thread_classifications_data_table');
  if (!dataTable || dataTable.rows.length < 2) {
    console.log('thread_classifications_data_table not found or empty');
    return;
  }

  const headerRow = dataTable.rows[0];
  const categories = [];
  for (let c = 1; c < headerRow.cells.length; c++) {
    categories.push(headerRow.cells[c].innerHTML.trim());
  }

  if (categories.length === 0) {
    console.log('No classification categories found in data table');
    return;
  }

  const labels     = [];
  const seriesData = categories.map(() => []);

  for (let r = 1; r < dataTable.rows.length; r++) {
    const row = dataTable.rows[r];
    labels.push(new Date(row.cells[0].innerHTML.trim()).valueOf());
    for (let c = 0; c < categories.length; c++) {
      seriesData[c].push(Number(row.cells[c + 1].innerHTML.trim()) || 0);
    }
  }

  const datasets = categories.map(function(cat, idx) {
    const colour = CLASSIFICATION_COLOURS[idx % CLASSIFICATION_COLOURS.length];
    return {
      label: cat,
      data: seriesData[idx],
      borderColor: colour,
      backgroundColor: colour.replace(',1)', ',0.15)'),
      borderWidth: 2,
      pointRadius: 3,
      fill: false,
    };
  });

  new Chart(ctx, {
    type: 'line',
    responsive: true,
    data: {
      labels: labels,
      datasets: datasets,
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of threads',
          },
        },
        x: {
          type: 'time',
          time: { displayFormats: TIME_AXIS_DISPLAY_FORMATS },
        },
      },
      plugins: {
        zoom: ZOOM_PLUGIN_CONFIG,
      },
    },
  });

  console.log('Thread classifications chart created successfully');
};
