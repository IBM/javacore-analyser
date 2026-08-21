<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="text()"/> <!-- these are not the threads you're looking for -->
    <xsl:template match="/index/doc/Thread/all_snapshot_collection/snapshot_collection[thread_hash='{id}']">
        <html height="100%">
            <head>
                <link rel="stylesheet" href="../data/carbon/ibm-plex.css"/>
                <link rel="stylesheet" href="../data/carbon/carbon.min.css"/>
                <link rel="stylesheet" href="../data/style.css"/>
                <link rel="stylesheet" href="../data/jquery/jq.css" />
                <link rel="stylesheet" href="../data/jquery/theme.blue.css" />
                <link rel="stylesheet" href="../data/jquery/theme.default.min.css" />
                <script type="text/javascript" src="../data/jquery/jquery.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.widgets.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/chart.umd.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/chartjs-adapter-date-fns.bundle.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/hammer.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/chartjs-plugin-zoom.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/wait2scripts.js"> _ </script>
                <script src="../data/jquery/jquery.mark.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/search.js"> _ </script>
                <script type="text/javascript" src="../data/carbon/carbon-components.min.js"> _ </script>
            </head>
            <body id="doc_body" class="cds--white" height="100%">
                <header class="cds--header" role="banner">
                    <a class="cds--header__name" href="../index.html">
                        <span class="cds--header__name--prefix">IBM</span>&#160;Javacore Analyser
                    </a>
                    <div class="cds--header__global">
                        <div class="cds--search cds--search--sm cds--search--light" role="search" aria-label="Search">
                            <input id="search-input" class="cds--search-input" type="search" placeholder="Search…" aria-label="Search" />
                            <button data-search="search" id="search-button" class="cds--search-button" aria-label="Search">
                                <svg class="cds--search-magnifier" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M15.14 13.73L11 9.58A5.88 5.88 0 0 0 7 0a6 6 0 1 0 4.36 10.08l4.05 4.09a1 1 0 0 0 1.41 0 1 1 0 0 0-.68-1.44zM7 10a4 4 0 1 1 4-4 4 4 0 0 1-4 4z"/></svg>
                            </button>
                            <button data-search="clear" class="cds--search-close" aria-label="Clear search">✖</button>
                        </div>
                        <button data-search="prev" class="cds--btn cds--btn--ghost cds--btn--sm cds--header__action" aria-label="Previous result">◂</button>
                        <button data-search="next" class="cds--btn cds--btn--ghost cds--btn--sm cds--header__action" aria-label="Next result">▸</button>
                        <span id="search-counter" class="search-counter"></span>
                    </div>
                </header>
                <main class="cds--content" id="main-content">
                <nav aria-label="Breadcrumb" class="cds--breadcrumb cds--breadcrumb--no-trailing-slash margined">
                    <ol class="cds--breadcrumb__list">
                        <li class="cds--breadcrumb-item">
                            <a href="../index.html" class="cds--link">Javacore Analyser Report</a>
                        </li>
                        <li class="cds--breadcrumb-item cds--breadcrumb-item--current" aria-current="page">
                            Thread Detail
                        </li>
                    </ol>
                </nav>
                <div class="content">
                    <h2>
                        Wait Report for thread: <b><xsl:value-of select="thread_name"/></b>
                        <br/>
                        java/lang/Thread:<xsl:value-of select="thread_address"/>
                    </h2>
                    <xsl:choose>
                        <xsl:when test="//javacore_count = 1">
                            System resource utilization data cannot be calculated with only a single javacore.
                        </xsl:when>
                        <xsl:otherwise>
                            <a id="togglethreadchartdoc" href="javascript:expand_it(threadchartdoc,togglethreadchartdoc)" class="expandit">
                                What does this chart tell me?</a>
                            <div id="threadchartdoc" style="display:none;">
                                This chart shows the CPU usage of this thread over time, expressed as a percentage of all available processor cores.
                                Each data point represents one javacore snapshot.
                                <p><strong>Chart interactions:</strong></p>
                                <ul>
                                    <li>Draw a rectangle on the chart to zoom into that area. Use the <em>Reset zoom</em> button to return to the full view.</li>
                                    <li>Click on a legend item to show or hide that data series.</li>
                                </ul>
                            </div>
                            <div class="chart-container" height="25%" style="overflow-x:auto;">
                                <canvas id="myChart" height="300" width="1400"
                                        title="Draw a rectangle to zoom in. Use the Reset zoom button to return to the full view."></canvas>
                            </div>
                        </xsl:otherwise>
                    </xsl:choose>
                    <div id="all_threads">
                    <div class="cds--data-table-container">
                    <div class="cds--data-table-content">
                        <table id="all_threads_table_thread_xsl" class="cds--data-table cds--data-table--zebra">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Elapsed time (s)</th>
                                    <th>CPU usage (s)</th>
                                    <th>% CPU usage</th>
                                    <th class='sixty'>Stack trace</th>
                                    <th>State</th>
                                    <th>Blocking</th>
                                    <xsl:choose>
                                        <xsl:when test="//@use_ml='True'">
                                            <th>Classification</th>
                                        </xsl:when>
                                    </xsl:choose>
                                </tr>
                            </thead>
                            <!-- Snapshot starts here -->
                            <xsl:for-each select="*[starts-with(name(), 'stack')]">
                                <tr>
                                    <td>
                                        <a>
                                            <xsl:attribute name="href">
                                                ../javacores/<xsl:value-of select="file_name"/>.html
                                            </xsl:attribute>
                                            <xsl:value-of select='timestamp'/>
                                        </a>
                                    </td>
                                    <xsl:choose>
                                        <xsl:when test="position()=1">
                                            <td>N/A</td>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <td>
                                                <xsl:value-of select='format-number(elapsed_time, "0.##")'/>
                                            </td>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                    <xsl:choose>
                                        <xsl:when test="position()=1">
                                            <td>N/A</td>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <td><xsl:value-of select='format-number(cpu_usage, "0.##")'/></td>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                    <xsl:choose>
                                            <xsl:when test="position()=1">
                                                <td>N/A</td>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <td><xsl:value-of select='format-number(cpu_percentage, "0.#")'/></td>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    <td class="left">
                                        <div>
                                            <xsl:choose>
                                                <xsl:when test="stack_depth &gt; 0">
                                                    <div class="toggle_expand">
                                                        <a href="javaScript:;" class="show">[+] Expand</a>
                                                    </div>
                                                    <p class="stacktrace">
                                                        <xsl:for-each select="*[starts-with(name(), 'line')]">
                                                            <span>
                                                                <xsl:attribute name="class"><xsl:value-of select="@kind"/></xsl:attribute>
                                                                <xsl:value-of select="current()"/>
                                                            </span>
                                                            <br/>
                                                        </xsl:for-each>
                                                    </p>
                                                </xsl:when>
                                                <xsl:otherwise>
                                                    No Stack
                                                </xsl:otherwise>
                                            </xsl:choose>
                                        </div>
                                    </td>
                                    <xsl:choose>
                                        <xsl:when test="state='CW'">
                                            <td class="waiting">
                                                <xsl:choose>
                                                    <xsl:when test="blocked_by=''">
                                                        Waiting on condition
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <a target="_blank">
                                                            <xsl:attribute name="href">
                                                                <xsl:value-of select="concat('thread_', blocked_by/@thread_hash, '.html')"/>
                                                            </xsl:attribute>
                                                            <xsl:attribute name="title">
                                                                <xsl:value-of select="blocked_by/@name" />
                                                            </xsl:attribute>
                                                            Waiting for <xsl:value-of select="blocked_by/@thread_id"/>
                                                        </a>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </td>
                                        </xsl:when>
                                        <xsl:when test="state='R'">
                                            <td class="runnable">Runnable</td>
                                        </xsl:when>
                                        <xsl:when test="state='P'">
                                            <td class="parked">
                                                <xsl:choose>
                                                    <xsl:when test="blocked_by=''">
                                                        Parked
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <a target="_blank">
                                                            <xsl:attribute name="href">
                                                                <xsl:value-of select="concat('thread_', blocked_by/@thread_hash, '.html')"/>
                                                            </xsl:attribute>
                                                            <xsl:attribute name="title">
                                                                <xsl:value-of select="blocked_by/@name" />
                                                            </xsl:attribute>
                                                            Parked on <xsl:value-of select="blocked_by/@thread_id"/>
                                                        </a>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </td>
                                        </xsl:when>
                                        <xsl:when test="state='B'">
                                            <td><span class="ml-badge state-blocked">
                                                <a target="_blank">
                                                    <xsl:attribute name="href">
                                                        <xsl:value-of select="concat('thread_', blocked_by/@thread_hash, '.html')"/>
                                                    </xsl:attribute>
                                                    <xsl:attribute name="title">
                                                                <xsl:value-of select="blocked_by/@name" />
                                                    </xsl:attribute>
                                                    Blocked by <xsl:value-of select="blocked_by/@thread_id"/>
                                                </a>
                                            </span></td>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <td><xsl:value-of select="state"/></td>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                    <td>
                                        <xsl:choose>
                                                <xsl:when test="blocking/thread">
                                                    blocking:
                                                    <xsl:for-each select="blocking/thread">
                                                        <a target="_blank">
                                                            <xsl:attribute name="href">
                                                                <xsl:value-of select="concat('thread_', @thread_hash, '.html')"/>
                                                            </xsl:attribute>
                                                            <xsl:attribute name="title">
                                                                <xsl:value-of select="@name" />
                                                            </xsl:attribute>
                                                            <xsl:value-of select="@thread_id" />
                                                        </a>;
                                                    </xsl:for-each>
                                                </xsl:when>
                                             </xsl:choose>
                                    </td>
                                    <xsl:choose>
                                        <xsl:when test="//@use_ml='True'">
                                            <td>
                                                <xsl:variable name="cls" select="ml_classification"/>
                                                <span>
                                                    <xsl:attribute name="class">ml-badge <xsl:choose>
                                                        <xsl:when test="$cls='Computing'">ml-computing</xsl:when>
                                                        <xsl:when test="$cls='Display Graphics'">ml-display-graphics</xsl:when>
                                                        <xsl:when test="$cls='Java Internal'">ml-java-internal</xsl:when>
                                                        <xsl:when test="$cls='Liberty Internal'">ml-liberty-internal</xsl:when>
                                                        <xsl:when test="$cls='Read From Database'">ml-read-database</xsl:when>
                                                        <xsl:when test="$cls='Read From Disk'">ml-read-disk</xsl:when>
                                                        <xsl:when test="$cls='Read From Network'">ml-read-network</xsl:when>
                                                        <xsl:when test="$cls='Save To Disk'">ml-save-disk</xsl:when>
                                                        <xsl:when test="$cls='Wait For Condition'">ml-wait-condition</xsl:when>
                                                        <xsl:when test="$cls='Wait For Connection'">ml-wait-connection</xsl:when>
                                                        <xsl:when test="$cls='Write To Database'">ml-write-database</xsl:when>
                                                        <xsl:when test="$cls='Write To Network'">ml-write-network</xsl:when>
                                                        <xsl:otherwise>ml-unknown</xsl:otherwise>
                                                    </xsl:choose></xsl:attribute>
                                                    <xsl:value-of select="$cls"/>
                                                </span>
                                            </td>
                                        </xsl:when>
                                    </xsl:choose>
                                </tr>
                            </xsl:for-each>
                        </table>
                    </div>
                    </div>
                    </div>
                </div>
                </main>
            </body>
            <script>loadChart();</script>
            <script type="text/javascript" src="../data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>
</xsl:stylesheet>
