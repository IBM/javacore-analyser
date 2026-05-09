<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="all_code">
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
                                            <xsl:when test="total_cpu_usage >= 0">
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
                                            <xsl:when test="cpu_percentage >= 0">
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
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
