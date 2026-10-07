/*
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
*/

/* This placeholder is shipped as part of the package. It is overwritten with
   the actual thread stack trace data by ReportGenerator._generate_thread_stacks_js()
   when the report contains javacore files.
   When no javacore data is present (e.g. verbose-GC only reports) this file remains
   as-is and thread_stacks_loader.js simply does nothing. */
'use strict';
window.THREAD_STACKS = window.THREAD_STACKS || {};
