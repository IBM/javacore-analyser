<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="text()"/> <!-- these are not the nodes you're looking for -->
    <xsl:template match="/">
        <html height="100%">
            <head>
                <link rel="stylesheet" href="../data/style.css"/>
                <link rel="stylesheet" href="../data/jquery/jq.css" />
                <link rel="stylesheet" href="../data/jquery/theme.blue.css" />
                <link rel="stylesheet" href="../data/jquery/theme.default.min.css" />
                <script type="text/javascript" src="../data/jquery/jquery.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/jquery.tablesorter.widgets.min.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/wait2scripts.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/sorting.js"> _ </script>
                <script type="text/javascript" src="../data/expand.js"> _ </script>
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
                    <h2>Wait Report for: <b>{id}</b></h2>
                    <div id="all_threads">
                        <table id="javacore_threads_table" class="tablesorter_blue">
                            <thead>
                                <tr>
                                    <th class="sixty">Thread name</th>
                                    <th>Total CPU usage (s)</th>
                                    <th>% CPU usage</th>
                                    <th>Memory allocated since last GC (MB)</th>
                                    <th>Java stack depth</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <xsl:for-each select="//Thread/all_snapshot_collection/snapshot_collection/stack[file_name='{id}']">
                                    <xsl:variable name="i" select="position()" />
                                    <tr>
                                        <td class="left">
                                            <div>
                                                <xsl:attribute name="id">
                                                    <xsl:value-of select="concat('stack',$i)"/>
                                                </xsl:attribute>
                                                <a target="_blank">
                                                    <xsl:attribute name="href">
                                                        <xsl:value-of select="concat('../threads/thread_', thread_hash, '.html')"/>
                                                    </xsl:attribute>
                                                    <xsl:value-of select="thread_name"/>
                                                </a>
                                                <xsl:choose>
                                                    <xsl:when test="stack_depth &gt; 0">
                                                    <div>
                                                        <div class="toggle_expand">
                                                            <a href="javaScript:;" class="show">[+] Expand</a> <!-- "show" class is used in expand.js -->
                                                        </div>
                                                        <p class="stacktrace">
                                                            <xsl:for-each select="*[starts-with(name(), 'line')]">
                                                                <span>
                                                                    <xsl:attribute name="class">
                                                                        <xsl:value-of select="@kind"/>
                                                                    </xsl:attribute>
                                                                    <xsl:value-of select="current()"/>
                                                                </span>
                                                                <br/>
                                                            </xsl:for-each>
                                                        </p>
                                                    </div>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        No stack
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </div>
                                        </td>
                                        <td>
                                            <xsl:choose>
                                                <xsl:when test="cpu_usage &gt;= 0">
                                                    <xsl:value-of select='format-number(cpu_usage, "0.00")'/>
                                                </xsl:when>
                                                <xsl:otherwise>
                                                    <div class="warning">[!]
                                                        <span class="warningtooltip">Error computing CPU usage, javacores may be corrupted</span>
                                                    </div>
                                                </xsl:otherwise>
                                            </xsl:choose>
                                        </td>
                                        <td>
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
                                        </td>
                                        <td><xsl:value-of select='format-number(allocated_memory div 1024 div 1024, "0.00")'/></td>
                                        <td><xsl:value-of select='java_stack_depth'/></td>
                                        <xsl:choose>
                                        <xsl:when test="state='CW'">
                                            <td class="waiting">Waiting on condition</td>
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
                                                                <xsl:value-of select="concat('../threads/thread_', blocked_by/@thread_hash, '.html')"/>
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
                                                        <xsl:value-of select="concat('../threads/thread_', blocked_by/@thread_hash, '.html')"/>
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
                                </tr>
                            </xsl:for-each>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            <script type="text/javascript" src="../data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>
</xsl:stylesheet>
