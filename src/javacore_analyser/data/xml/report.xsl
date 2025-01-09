<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:variable name="displayed_stack_depth" select="50" />

    <xsl:template match="index">
        <html>
            <head>
                <link rel="stylesheet" href="data/style.css" />
                <link rel="stylesheet" href="data/jquery/theme.default.min.css" />
                <link rel="stylesheet" href="data/jquery/jq.css" />
                <link rel="stylesheet" href="data/jquery/theme.blue.css" />
                <script type="text/javascript" src="data/jquery/jquery.min.js" > _ </script>
                <script type="text/javascript" src="data/jquery/jquery.tablesorter.min.js" > _ </script>
                <script type="text/javascript" src="data/jquery/jquery.tablesorter.widgets.min.js" > _ </script>
                <script type="text/javascript" src="data/jquery/wait2scripts.js"> _ </script>
                <script type="text/javascript" src="data/jquery/chart.js"> _ </script>
                <script type="text/javascript" src="data/jquery/chartjs-adapter-date-fns.bundle.min.js"> _ </script>
                <script src="data/jquery/jquery.mark.min.js"> _ </script>
                <script type="text/javascript" src="data/jquery/search.js"> _ </script>

                <script>
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
                </script>
            </head>

            <body id="doc_body">
                <div class="searchbar">
                    <input id="search-input" type="search" />
                    <button data-search="search" id="search-button">Search</button>
                    <button data-search="next">Next</button>
                    <button data-search="prev">Prev</button>
                    <button data-search="clear">✖</button>
                </div>
                <div class="content">
                <h1>Wait Report</h1>
                <div class="margined">
                    from data between
                    <b><xsl:value-of select="doc/report_info/javacores_generation_time/starting_time"/></b> and
                    <b><xsl:value-of select="doc/report_info/javacores_generation_time/end_time"/></b>
                </div>
                <h3><a id="togglejavacores" href="javascript:expand_it(javacores,togglejavacores)" class="expandit">Input Files</a></h3>
                <div id="javacores" style="display:none;">
                    <h4>Javacore Files</h4>
                    <a id="togglejavacoredoc" href="javascript:expand_it(javacoredoc,togglejavacoredoc)" class="expandit">What does this table tell me?</a>
                    <div id="javacoredoc" style="display:none;">
                        This table shows all the javacore files that are included in the data set.
                        <ul>
                            <li>
                                <strong>File Name</strong>
                                is the name of the javacore file.
                            </li>
                            <li>
                                <strong>Time Stamp</strong>
                                is the time when the javacore was generated.
                            </li>
                            <li>
                                <strong>CPU usage (%)</strong>
                                is the total CPU usage of all the threads in the javacore. The maximum possible value is therefore 100%
                                This value is computed incrementally
                                with relation to the previous javacore, hence it is not available ("N/A") for the first
                                javacore file.
                                </li>
                                <li>
                                    <strong>CPU Load</strong>
                                    is the total CPU usage of all the threads in the javacore.
                                    Load of 1 means that 1 core is fully used.
                                    The maximum possible value is therefore the number of cores
                                    This value is computed incrementally
                                    with relation to the previous javacore, hence it is not available ("N/A") for the first
                                    javacore file.
                                </li>
                            </ul>
                        </div>
                        <table id="javacores_files_table">
                            <thead>
                                <tr>
                                    <th class="fifty">File Name</th>
                                    <th class="thirty">Time Stamp</th>
                                    <th class="ten">CPU usage (%)</th>
                                    <th class="ten">CPU Load</th>
                                </tr>
                            </thead>
                            <tbody>
                                <xsl:for-each select="doc/report_info/javacore_list/javacore">
                                    <tr>
                                        <td class="left">
                                            <a target="_blank">
                                                <xsl:attribute name="href">
                                                    <xsl:value-of select="concat('javacores/', javacore_file_name, '.html')"/>
                                                </xsl:attribute>
                                            </a>
                                            <xsl:value-of select="javacore_file_name"/>
                                        </td>
                                        <td class="left"><xsl:value-of select="javacore_file_time_stamp"/></td>
                                        <xsl:choose>
                                            <xsl:when test="position()=1">
                                                <td class="left">N/A</td>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <td><xsl:value-of select="format-number(javacore_cpu_percentage, '0.##')"/></td>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="position()=1">
                                                <td class="left">N/A</td>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <td><xsl:value-of select="format-number(javacore_load, '0.##')"/></td>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </tr>
                                </xsl:for-each>
                            </tbody>
                        </table>
                        <br/>
                        <xsl:choose>
                            <xsl:when test="doc/report_info/verbose_gc_list/verbose_gc">
                                <h4>Verbose GC files</h4>
                                <a id="toggleverbosegcdoc" href="javascript:expand_it(verbosegcdoc,toggleverbosegcdoc)" class="expandit">
                                    What does this table tell me?</a>
                                <div id="verbosegcdoc" style="display:none;">
                                    This table shows all the verbose GC log files that are included in the data set.
                                    <ul>
                                        <li>
                                            <strong>File Name</strong>
                                            is the name of the verbose GC log file.
                                        </li>
                                        <li>
                                            <strong>Number of collections in javacore time limits</strong>
                                            is the number of garbage collections in the verbose GC log file,
                                            that happened between the time of the first and the last javacore in the data set.
                                        </li>
                                        <li>
                                            <strong>Total number of collections in the file</strong>
                                            is the number of all garbage collections found in the verbose GC log file,
                                            regardless of when they happened with relation to the time the javacores
                                            were generated.
                                        </li>
                                    </ul>
                                </div>
                                <table id="verbose_gc_files_table">
                                    <thead>
                                        <tr>
                                            <th class="sixty">File Name</th>
                                            <th class="ten">Number of collections in javacore time limits</th>
                                            <th class="ten">Total number of collections in the file</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <xsl:for-each select="doc/report_info/verbose_gc_list/verbose_gc">
                                            <tr>
                                                <td class="left"><xsl:value-of select="verbose_gc_file_name"/></td>
                                                <td class="left"><xsl:value-of select="verbose_gc_collects"/></td>
                                                <td class="left"><xsl:value-of select="verbose_gc_total_collects"/></td>
                                            </tr>
                                        </xsl:for-each>
                                    </tbody>
                                </table>
                            </xsl:when>
                            <xsl:otherwise> No verbose GC files </xsl:otherwise>
                        </xsl:choose>
                    <xsl:choose>
                            <xsl:when test="doc/har_files">
                                <h4>HAR files</h4>
                                <a id="togglehardoc" href="javascript:expand_it(hardoc,togglehardoc)" class="expandit">
                                    What does this table tell me?</a>
                                <div id="hardoc" style="display:none;">
                                    This table shows all the HAR files that are included in the data set.
                                    <ul>
                                        <li>
                                            <strong>File Name</strong>
                                            is the name of the HAR file.
                                        </li>
                                        <li>
                                            <strong>Hostname</strong>
                                            is the name of the server machine for which the HAR file was collected.
                                        </li>
                                        <li>
                                            <strong>Browser</strong>
                                            contains information about the browser that was used to collect the HAR file.
                                        </li>
                                    </ul>
                                </div>
                                <table id="har_files_table">
                                    <thead>
                                        <tr>
                                            <th class="sixty">File Name</th>
                                            <th class="ten">Hostname</th>
                                            <th class="ten">Browser</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <xsl:for-each select="doc/har_files/har_file">
                                            <tr>
                                                <td class="left"><xsl:value-of select="@filename"/></td>
                                                <td class="left"><xsl:value-of select="@hostname"/></td>
                                                <td class="left"><xsl:value-of select="@browser"/></td>
                                            </tr>
                                        </xsl:for-each>
                                    </tbody>
                                </table>
                            </xsl:when>
                            <!-- xsl:otherwise> No HAR files </xsl:otherwise -->
                        </xsl:choose>
                    </div>
                    <h3><a id="toggle_system_properties"
                           href="javascript:expand_it(system_properties, toggle_system_properties)"
                           class="expandit">System Information</a></h3>
                    <div id="system_properties" style="display:none;">
                        <h4>Basic JVM Configuration</h4>
                        <table id="sys_info_table" class="tablesorter">
                            <thead>
                                <tr>
                                    <th class="ten">Property</th>
                                    <th class="ninety">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Number of CPUs</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/number_of_cpus"/></td>
                                </tr>
                                <tr>
                                    <td>Xmx</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/xmx"/></td>
                                </tr>
                                <tr>
                                    <td>Xms</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/xms"/></td>
                                </tr>
                                <tr>
                                    <td>Xmn</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/xmn"/></td>
                                </tr>
                                <tr>
                                    <td>Verbose GC</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/verbose_gc"/></td>
                                </tr>
                                <tr>
                                    <td>GC policy</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/gc_policy"/></td>
                                </tr>
                                <tr>
                                    <td>Compressed refs</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/compressed_refs"/></td>
                                </tr>
                                <tr>
                                    <td>Architecture</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/architecture"/></td>
                                </tr>
                                <tr>
                                    <td>Java version</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/java_version"/></td>
                                </tr>
                                <tr>
                                    <td>Os level</td>
                                    <td class="left"><xsl:value-of select="doc/system_info/os_level"/></td>
                                </tr>
                            </tbody>
                        </table>
                        <h4>Java Arguments</h4>
                        <table id="java_arguments_table" class="tablesorter">
                            <thead><th>Argument</th></thead>
                            <tbody>
                                <xsl:for-each select="doc/system_info/user_args_list/user_arg ">
                                    <tr><td class="left"><xsl:value-of select="current()"/></td></tr>
                                </xsl:for-each>
                            </tbody>
                        </table>
                    </div>

                <h3><a id="toggleintelligenttips" href="javascript:expand_it(intelligenttips,toggleintelligenttips)" class="expandit">Intelligent tips</a></h3>
                <div id="intelligenttips"  style="display:none;">
                    <xsl:choose>
                        <xsl:when test="doc/report_info/tips/tip">
                            <ul>
                                <xsl:for-each select="doc/report_info/tips/tip">
                                    <li><xsl:value-of select="current()"/></li>
                                </xsl:for-each>
                            </ul>
                        </xsl:when>
                        <xsl:otherwise>
                            We did not find any tips for you.
                        </xsl:otherwise>
                    </xsl:choose>
                </div>

                <h3 id="system_resource_utilization_h3"><a id="toggleresourcesutil" href="javascript:expand_it(systemresources,toggleresourcesutil)" class="expandit">System resources utilization</a></h3>
                <div id="systemresources"  style="display:none;">
                    <xsl:choose>
                        <xsl:when test="//javacore_count = 1">
                            System resource utilization data cannot be calculated with only a single javacore.
                        </xsl:when>
                        <xsl:otherwise>
                            <h4>Garbage Collection Activity</h4>
                            <a id="togglememusagedoc" href="javascript:expand_it(memusagedoc,togglememusagedoc)" class="expandit">
                                What does this chart tell me?</a>
                                <xsl:choose>
                                    <xsl:when test="doc/report_info/verbose_gc_list/verbose_gc">
                                        <xsl:choose>
                                            <xsl:when test="//verbose_gc_list/@total_collects_in_time_limits = 0">
                                                <br/>
                                                There were no garbage collections withing the javacore time limits
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <div id="memusagedoc" style="display:none;">
                                                This chart shows all the garbage collections that happened between the time
                                                of the first and the last javacore in the data set.
                                                Garbage collections that happened before the first
                                                or after the last javacore generation time are not included.
                                                <ul>
                                                    <li><strong>Heap Usage</strong>
                                                        is the available Java heap memory over time,
                                                        based on the garbage collection data from the verbose GC log files.
                                                    </li>
                                                    <li><strong>Total Heap</strong>
                                                        is the maximum size of the Java heap, configured by using the Xmx Java argument,
                                                        expressed in megabytes.
                                                    </li>
                                            </ul>
                                        </div>
                                        <div id="systemresources_myChartGC" class="chart-container hide">
                                            <canvas id="myChartGC" height="200"></canvas>
                                        </div>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <br/>
                                        No verbosegc logs were provided
                                    </xsl:otherwise>
                                </xsl:choose>
                            <h4>CPU Load</h4>
                            <a id="togglecpuloaddoc" href="javascript:expand_it(cpuloaddoc,togglecpuloaddoc)" class="expandit">
                                What does this chart tell me?</a>
                            <div id="cpuloaddoc" style="display:none;">
                                This chart shows the total CPU usage of all the threads in the javacore, expressed as percentage
                                of all the processor cores. The maximum possible value is therefore 100%, which
                                would indicate all the cores are completely busy. Each bar represents one javacore in the data set.
                                This value is computed incrementally with relation to the previous javacore,
                                hence it is not available for the first javacore file.
                            </div>
                            <div class="chart-container">
                                <canvas id="myChartCPUUsage" height="200"></canvas>
                            </div>
                        </xsl:otherwise>
                    </xsl:choose>
                </div>

                    <h3><a id="toggletop10blocker" href="javascript:expand_it(top10blocker,toggletop10blocker)" class="expandit">Top 10 Blockers</a></h3>
                    <div id="top10blocker" style="display:none;">
                        <xsl:choose>
                            <xsl:when test="doc/blockers/blocker">
                                <a id="toggleblockersdoc" href="javascript:expand_it(blockersdoc,toggleblockersdoc)" class="expandit">
                                    What does this table tell me?</a>
                                <div id="blockersdoc" style="display:none;">
                                    This table shows top ten threads that were blocking other threads most frequently,
                                    based on the information in the javacore files.
                                    <ul>
                                        <li>
                                            <strong>Thread name</strong>
                                            is the name of the thread.
                                        </li>
                                        <li>
                                            <strong>Number of different blocked threads</strong>
                                            is the total number of times, across all javacore files, this thread was
                                            blocking any other thread.
                                        </li>
                                    </ul>
                                </div>
                                <table id="top10_blocker_table" class="tablesorter">
                                    <thead>
                                        <tr>
                                            <th class="ninety">Thread name</th>
                                            <th>Number of different blocked threads</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <xsl:for-each select="doc/blockers/blocker">
                                            <tr>
                                                <td class="left">
                                                    <a class="right" target="_blank">
                                                        <xsl:attribute name="href">
                                                            <xsl:value-of select="concat('threads/thread_', blocker_hash, '.html')"/>
                                                        </xsl:attribute>
                                                        <xsl:value-of select="blocker_name"/>
                                                    </a>
                                                </td>
                                                <td><xsl:value-of select="blocker_size"/></td>
                                            </tr>
                                        </xsl:for-each>
                                    </tbody>
                                </table>
                            </xsl:when>
                            <xsl:otherwise> There are no blocking threads in Javacores </xsl:otherwise>
                        </xsl:choose>
                    </div>

                <h3><a  id="toggle_all_threads" href="javascript:expand_it(all_threads,toggle_all_threads)" class="expandit">All Threads</a></h3>
                <div id="all_threads"  style="display:none;">
                    <a id="togglethreadsdoc" href="javascript:expand_it(threadsdoc,togglethreadsdoc)" class="expandit">
                        What does this table tell me?</a>
                    <div id="threadsdoc" style="display:none;">
                        This table contains information about all the threads found in all the javacore files in the data set.
                        Note that the thread is identified by a combination of its ID and name. This makes sense for pool threads
                        that may be reused for unrelated tasks. Two tasks with different thread names are therefore treated
                        as separate threads for the purpose of this report, even if they are executed in the scope of the same
                        Thread java object.
                        The table can be sorted by clicking on any column header.
                        The following information is displayed for each thread:
                        <ul>
                            <li><strong>Thread name</strong>
                                The name is clickable, and when clicked it opens a view that allows you to see the stack trace
                                of the code that the thread was executing in each of the javacores in which it appears.
                                Note that there may be multiple threads with the same name,
                                since the names of threads are not unique over time, and may be reused.
                            </li>
                            <li><strong>Total CPU usage</strong>
                                is the total number of seconds the thread was using CPU time since the first javacore,
                                in which the thread appears until the last.
                            </li>
                            <li><strong>% CPU Usage</strong>
                                is the total CPU usage of the thread, expressed as percentage
                                of a single processor core. A thread can only use one CPU core at a time,
                                the maximum possible value is therefore 100%.
                            </li>
                            <li><strong>Average memory allocated since last GC</strong>
                                is the amount of memory, in megabytes, allocated by the thread since the last GC cycle,
                                averaged across all the javacores. Note that this number does not represent the total amount
                                of memory allocated by a thread and is only suitable for relative comparison between threads.
                                This number is only meaningful if a sufficient number of javacores is present in the data set,
                                10 being the absolute minimum in most cases.
                            </li>
                            <li><strong>Average stack depth</strong>
                                is the depth of the stack of the thread, averaged across all the javacore files in the
                                data set, in which the thread appears.
                            </li>
                            <li><strong>Blocking information</strong>
                                includes a list of links to threads which are blocking or being blocked by the given thread
                            </li>
                        </ul>
                    </div>
                    <table id="all_threads_table" class="tablesorter">
                        <thead>
                            <tr>
                                <th class="sixty">Thread name</th>
                                <th>Total CPU usage (s)</th>
                                <th>% CPU usage</th>
                                <th>Average memory allocated since last GC (MB)</th>
                                <th>Average stack depth</th>
                                <th>Blocking information</th>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="doc/Thread/all_snapshot_collection/snapshot_collection">
                                <xsl:variable name="i" select="position()" />
                                <tr>
                                    <td class="left">
                                        <a>
                                            <xsl:attribute name="id"><xsl:value-of select="concat('toggle_thread_name',$i)"/></xsl:attribute>
                                            <xsl:attribute name="href"><xsl:value-of select="concat('javascript:expand_stack(stack',$i,',toggle_thread_name',$i,')')"/></xsl:attribute>
                                            <xsl:attribute name="class">expandit</xsl:attribute><xsl:value-of select="thread_name"/></a>
                                        <a class="right" target="_blank">
                                            <xsl:attribute name="href">
                                                <xsl:value-of select="concat('threads/thread_', thread_hash, '.html')"/>
                                            </xsl:attribute>
                                            More...
                                        </a>
                                        <br/>
                                        <div  style="display:none;" >
                                            <xsl:attribute name="id"><xsl:value-of select="concat('stack',$i)"/></xsl:attribute>
                                            <xsl:for-each select="*[starts-with(name(), 'stack')]">
                                                <div>
                                                    <xsl:choose>
                                                        <xsl:when test="stack_depth &gt; 0">
                                                            <div class="toggle_expand">
                                                                <a href="javaScript:;" class="show">[+] Expand</a> <!-- "show" class is used in expand.js -->
                                                            </div>
                                                            <p class="stacktrace">
                                                                <xsl:for-each select="*[starts-with(name(), 'line')]">
                                                                    <xsl:choose>
                                                                        <xsl:when test="@order &lt; $displayed_stack_depth">
                                                                            <span>
                                                                                <xsl:attribute name="class">
                                                                                    <xsl:value-of select="@kind"/>
                                                                                </xsl:attribute>
                                                                                <xsl:value-of select="current()"/>
                                                                            </span>
                                                                            <br/>
                                                                        </xsl:when>
                                                                    </xsl:choose>
                                                                </xsl:for-each>

                                                                <xsl:choose>
                                                                    <xsl:when test="stack_depth &gt; $displayed_stack_depth">
                                                                        <span>
                                                                            ...
                                                                        </span>
                                                                        <br/>
                                                                    </xsl:when>
                                                                </xsl:choose>
                                                            </p>
                                                        </xsl:when>
                                                        <xsl:otherwise>
                                                            No Stack
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                                </div>
                                            </xsl:for-each>
                                        </div>
                                    </td>
                                    <td>
                                        <xsl:choose>
                                        <xsl:when test="//javacore_count = 1">
                                            N/A
                                        </xsl:when>
                                            <xsl:otherwise>
                                                    <xsl:choose>
                                                        <xsl:when test="total_cpu_usage &gt;= 0">
                                                            <xsl:value-of select='format-number(total_cpu_usage, "0.00")'/>
                                                        </xsl:when>
                                                        <xsl:otherwise>
                                                            <div class="warning">[!]
                                                                <span class="warningtooltip">Error computing CPU usage, javacores may be corrupted</span>
                                                            </div>
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td>
                                        <xsl:choose>
                                            <xsl:when test="//javacore_count = 1">
                                                N/A
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:choose>
                                                    <xsl:when test="cpu_percentage &gt;= 0">
                                                        <xsl:value-of select='format-number(cpu_percentage, "0.0")'/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <div class="warning">[!]
                                                            <span class="warningtooltip">Error computing CPU percentage, javacores may be corrupted</span>
                                                        </div>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td><xsl:value-of select='format-number(average_memory div 1024 div 1024, "0.00")'/></td>
                                    <td><xsl:value-of select='format-number(average_stack_depth, "0.0")'/></td>
                                    <td   class="left">
                                        <xsl:choose>
                                            <xsl:when test="blocking/thread">
                                                blocking:
                                                <xsl:for-each select="blocking/thread">
                                                    <a target="_blank">
                                                        <xsl:attribute name="href">
                                                            <xsl:value-of select="concat('threads/thread_', @hash, '.html')"/>
                                                        </xsl:attribute>
                                                        <xsl:attribute name="title">
                                                            <xsl:value-of select="@name" />
                                                        </xsl:attribute>
                                                        <xsl:value-of select="@id" />
                                                    </a>;

                                                </xsl:for-each>
                                            </xsl:when>
                                         </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="blocker/thread">
                                                blocked by:
                                                <xsl:for-each select="blocker/thread">
                                                    <a target="_blank">
                                                        <xsl:attribute name="href">
                                                            <xsl:value-of select="concat('threads/thread_', @hash, '.html')"/>
                                                        </xsl:attribute>
                                                        <xsl:attribute name="title">
                                                            <xsl:value-of select="@name" />
                                                        </xsl:attribute>
                                                        <xsl:value-of select="@id" />
                                                    </a>;
                                                </xsl:for-each>
                                            </xsl:when>
                                         </xsl:choose>
                                    </td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                </div>

                <h3><a  id="toggle_all_code_collection" href="javascript:expand_it(all_code_collection,toggle_all_code_collection)" class="expandit">All Code</a></h3>
                <div id="all_code_collection" style="display:none;" >
                    <a id="togglecodedoc" href="javascript:expand_it(codedoc,togglecodedoc)" class="expandit">
                        What does this table tell me?</a>
                        <div id="codedoc" style="display:none;">
                        The table shows resource usage of code that is being executed by the JVM,
                        regardless of the thread it is run in.
                        The table can be sorted by clicking on a column header.
                        <ul>
                            <li><strong>Stack</strong>
                                shows the top 5 methods from the top stack,
                                or fewer if the stack trace is shallower than 5.
                            </li>
                            <li><strong>Total CPU Usage</strong>
                                is the total number of seconds the code was using CPU time,
                                when executed in any thread in any javacore file.
                            </li>
                            <li><strong>% CPU Usage</strong>
                                is the total CPU usage of the thread, expressed as percentage
                                of a single processor core. The code can run simultanously in more than one thread,
                                each thread using one CPU core at a time, the maximum possible value may be therefore
                                greater than 100%.
                            </li>
                            <li><strong>Average memory allocated since last GC</strong>
                                is the amount of memory, in megabytes, allocated by all the threads since the last GC cycle,
                                while they were running the given code. Note that this number does not represent the total
                                amount of memory allocated by the code and is only suitable for relative comparison between
                                different pieces of code. This number is only meaningful if a sufficient number of javacores
                                is present in the data set, 10 being the absolute minimum in most cases.
                            </li>
                            <li><strong>Threads</strong>
                                is a list of links to threads that are known to have executed the given piece of code at any
                                point, based on the data in the javacore files.
                            </li>
                        </ul>
                    </div>
                    <table id="allCodeTable" class="tablesorter">
                        <thead>
                            <tr>
                                <th  class="sixty">stack</th>
                                <th>Total CPU usage (s)</th>
                                <th>% CPU usage</th>
                                <th>Average memory allocated since last GC (MB)</th>
                                <th>Threads</th>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="doc/CodeSnapshotCollection/all_snapshot_collection/snapshot_collection">
                                <tr>
                                    <td class="left">
                                        <xsl:for-each select="*[starts-with(name(), 'stack_trace')]">
                                            <xsl:value-of select="current()"/><br/>
                                        </xsl:for-each>
                                    </td>
                                    <td>
                                        <xsl:choose>
                                            <xsl:when test="//javacore_count = 1">
                                                N/A
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:choose>
                                                    <xsl:when test="total_cpu_usage &gt;= 0">
                                                        <xsl:value-of select='format-number(total_cpu_usage, "0.00")'/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <div class="warning">[!]
                                                            <span class="warningtooltip">Error computing CPU usage, javacores may be corrupted</span>
                                                        </div>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td>
                                        <xsl:choose>
                                            <xsl:when test="//javacore_count = 1">
                                                N/A
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:choose>
                                                    <xsl:when test="cpu_percentage &gt;= 0">
                                                        <xsl:value-of select='format-number(cpu_percentage, "0.0")'/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <div class="warning">[!]
                                                            <span class="warningtooltip">Error computing CPU percentage, javacores may be corrupted</span>
                                                        </div>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td><xsl:value-of select='format-number(average_memory div 1024 div 1024, "0.00")'/></td>
                                    <td  class="left">
                                        <xsl:for-each select="threads/thread">
                                                    <a target="_blank">
                                                        <xsl:attribute name="href">
                                                            <xsl:value-of select="concat('threads/thread_', @hash, '.html')"/>
                                                        </xsl:attribute>
                                                        <xsl:attribute name="title">
                                                            <xsl:value-of select="@name" />
                                                        </xsl:attribute>
                                                        <xsl:value-of select="@id" />
                                                    </a>;
                                        </xsl:for-each>
                                    </td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                </div>

                <xsl:choose>
                    <xsl:when test="doc/har_files">
                        <h3><a  id="toggle_http_calls" href="javascript:expand_it(http_calls,toggle_http_calls)" class="expandit">HTTP calls</a></h3>
                        <div id="http_calls" style="display:none;" >
                            <a id="togglehttpcallsdoc" href="javascript:expand_it(httpcallsdoc,togglehttpcallsdoc)" class="expandit">
                                What does this table tell me?</a>
                                <div id="httpcallsdoc" style="display:none;">
                                The table shows the HTTP calls that are included in the HAR files from the data set.
                                The table can be sorted by clicking on a column header.
                                <ul>
                                    <li><strong>URL</strong>
                                        is the URL of the HTTP request.
                                    </li>
                                    <li><strong>Status</strong>
                                        is the HTTP response code.
                                    </li>
                                    <li><strong>Start time</strong>
                                        is the time when the HTTP request was made.
                                    </li>
                                    <li><strong>Duration</strong>
                                        is the amount of time it took to complete the HTTP call, in milliseconds.
                                    </li>
                                    <li><strong>Size</strong>
                                        is size of the response body, in bytes.
                                    </li>
                                </ul>
                            </div>
                            <table id="HttpCallTable" class="tablesorter">
                                <thead>
                                    <tr>
                                        <th  class="sixty">URL</th>
                                        <th>Status</th>
                                        <th>Start Time</th>
                                        <th>Duration</th>
                                        <th>Size</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <xsl:for-each select="//http_call">
                                        <tr>
                                            <td class="left"><xsl:value-of select="@url"/></td>
                                            <td>
                                                <xsl:choose>
                                                    <xsl:when test="@success='False'">
                                                        <xsl:attribute name="class">http_failure</xsl:attribute>
                                                    </xsl:when>
                                                </xsl:choose>
                                                <xsl:value-of select="@status"/>
                                            </td>
                                            <td><xsl:value-of select="@start_time"/></td>
                                            <td>
                                                <div class="info"><xsl:value-of select="@duration"/>
                                                    <span class="infotooltip"><xsl:value-of select="@timings"/></span>
                                                </div>
                                            </td>
                                            <td><xsl:value-of select="@size"/></td>
                                        </tr>
                                    </xsl:for-each>
                                </tbody>
                            </table>
                        </div>
                    </xsl:when>
                </xsl:choose>

                    <p></p>
                    <div class="margined">
                        <a href="https://github.com/IBM/javacore-analyser/wiki" target="_blank">Documentation</a>
                    </div>
                    <div class="margined">
                        In case of any issues with the tool use Slack group:
                        <a href="https://ibm-ai-apps.slack.com/archives/C01KQ4X0ZK6"> #wait-necromancers</a>
                    </div>
                    <div class="margined">
                        Report Generation Time: <xsl:value-of select="doc/report_info/generation_time"/>
                    </div>


                <div style="display: none;">
                    <xsl:copy-of select="doc/gc-collections" />
                    </div>
                </div>
            </body>
            <script>loadChartGC();loadChartCPUUsage();</script>
            <script type="text/javascript" src="data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>
</xsl:stylesheet> 
