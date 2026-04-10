<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="all_threads">
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
                        The address of the java Thread object is included for each thread. This corresponds to the address reported in Java heapdumps.
                        The table can be sorted by clicking on any column header.
                        The following information is displayed for each thread:
                        <ul>
                            <li><strong>Thread name</strong>
                                The name is clickable, and when clicked it opens a view that allows you to see the stack trace
                                of the code that the thread was executing in each of the javacores in which it appears.
                                Note that there may be multiple threads with the same name,
                                since the names of threads are not unique over time, and may be reused.
                                A 'More' link may appear next to the thread name to allow to drilldown into that thread's individual page
                                The drilldown may be supressed for threads that don't appear to be doing anything interesting.
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
                                            <xsl:attribute name="class">expandit</xsl:attribute>
                                            <xsl:value-of select="thread_name"/>
                                        </a>
                                        <xsl:choose>
                                                <xsl:when test="@has_drill_down='True'">
                                                <a class="right" target="_blank">
                                                    <xsl:attribute name="href">
                                                        <xsl:value-of select="concat('threads/thread_', thread_hash, '.html')"/>
                                                    </xsl:attribute>
                                                    More...
                                                </a>
                                                <br/>
                                            </xsl:when>
                                        </xsl:choose>
                                        <div  style="display:none;" >
                                            <xsl:attribute name="id"><xsl:value-of select="concat('stack',$i)"/></xsl:attribute>
                                            java/lang/Thread:<xsl:value-of select="thread_address"/>
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
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
