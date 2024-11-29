<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="text()"/> <!-- these are not the threads you're looking for -->
    <xsl:template match="/index/doc/Thread/all_snapshot_collection/snapshot_collection[thread_hash='{id}']">
        <html height="100%">
            <head>
                <link rel="stylesheet" href="../data/style.css"/>
                <link rel="stylesheet" href="../data/jquery/jq.css" />
                <link rel="stylesheet" href="../data/jquery/theme.blue.css" />
                <link rel="stylesheet" href="../data/jquery/theme.default.min.css" />
                <script type="text/javascript" src="../data/jquery/jquery.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.widgets.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/chart.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/chartjs-adapter-date-fns.bundle.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/wait2scripts.js"> _ </script>
                <script src="../data/jquery/jquery.mark.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/search.js"> _ </script>
            </head>
            <body id="doc_body" height="100%">
                <div class="searchbar">
                    <input id="search-input" type="search" />
                    <button data-search="search" id="search-button">Search</button>
                    <button data-search="next">Next</button>
                    <button data-search="prev">Prev</button>
                    <button data-search="clear">✖</button>
                </div>
                <div class="content">
                    <p class="right"><a href="../index.html"> Back to Main page </a></p>
                    <h2>Wait Report for thread: <b><xsl:value-of select="thread_name"/></b></h2>
                    <xsl:choose>
                        <xsl:when test="//javacore_count = 1">
                            System resource utilization data cannot be calculated with only a single javacore.
                        </xsl:when>
                        <xsl:otherwise>
                            <div class="chart-container" height="25%">
                                <canvas id="myChart" height="100%"></canvas>
                            </div>
                        </xsl:otherwise>
                    </xsl:choose>
                    <div id="all_threads">
                        <table id="all_threads_table_thread_xsl">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Elapsed time (s)</th>
                                    <th>CPU usage (s)</th>
                                    <th>% CPU usage</th>
                                    <th class='sixty'>Stack trace</th>
                                    <th>State</th>
                                    <th>Blocking</th>
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
                                            <td class="blocked">
                                                <a target="_blank">
                                                    <xsl:attribute name="href">
                                                        <xsl:value-of select="concat('thread_', blocked_by/@thread_hash, '.html')"/>
                                                    </xsl:attribute>
                                                    <xsl:attribute name="title">
                                                                <xsl:value-of select="blocked_by/@name" />
                                                    </xsl:attribute>
                                                    Blocked by <xsl:value-of select="blocked_by/@thread_id"/>
                                                </a>
                                            </td>
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
                                </tr>
                            </xsl:for-each>
                        </table>
                    </div>
                </div>
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
