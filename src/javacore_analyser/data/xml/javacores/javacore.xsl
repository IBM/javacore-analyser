<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="text()"/> <!-- these are not the nodes you're looking for -->
    <xsl:template match="/">
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
                <script type="text/javascript" src="../data/jquery/wait2scripts.js"> _ </script>
                <script type="text/javascript" src="../data/jquery/sorting.js"> _ </script>
                <script type="text/javascript" src="../data/expand.js"> _ </script>
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
                            Javacore Detail
                        </li>
                    </ol>
                </nav>
                <div class="content">
                    <h2>Wait Report for: <b>{id}</b></h2>
                    <div id="all_threads">
                    <div class="cds--data-table-container">
                    <div class="cds--data-table-content">
                        <table id="javacore_threads_table" class="cds--data-table cds--data-table--zebra">
                            <thead>
                                <tr>
                                    <th class="sixty">Thread name</th>
                                    <th>Total CPU usage (s)</th>
                                    <th>% CPU usage</th>
                                    <th>Memory allocated since last GC (MB)</th>
                                    <th>Java stack depth</th>
                                    <th>Status</th>
                                    <xsl:choose>
                                        <xsl:when test="//@use_ml='True'">
                                            <th>Classification</th>
                                        </xsl:when>
                                    </xsl:choose>
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
                                                        <xsl:value-of select="concat('../threads/thread_', preceding-sibling::thread_hash, '.html')"/>
                                                    </xsl:attribute>
                                                    <xsl:value-of select="preceding-sibling::thread_name"/>
                                                </a>
                                                <xsl:choose>
                                                    <xsl:when test="@is_current_thread='true'">
                                                        <b style="color: #d9534f; margin-left: 5px;">[Current Thread]</b>
                                                    </xsl:when>
                                                </xsl:choose>
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
                                            <td><span class="ml-badge state-waiting">Waiting on condition</span></td>
                                        </xsl:when>
                                        <xsl:when test="state='R'">
                                            <td><span class="ml-badge state-runnable">Runnable</span></td>
                                        </xsl:when>
                                        <xsl:when test="state='P'">
                                            <td><span class="ml-badge state-parked">
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
                                            </span></td>
                                        </xsl:when>
                                        <xsl:when test="state='B'">
                                            <td><span class="ml-badge state-blocked">
                                                <a target="_blank">
                                                    <xsl:attribute name="href">
                                                        <xsl:value-of select="concat('../threads/thread_', blocked_by/@thread_hash, '.html')"/>
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
                            </tbody>
                        </table>
                    </div>
                    </div>
                    </div>
                </div>
                </main>
            </body>
            <script type="text/javascript" src="../data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>
</xsl:stylesheet>
