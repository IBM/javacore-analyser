<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- Key used for Muenchian grouping to find distinct classification labels
         across all javacore_classifications/classification_entry nodes. -->
    <xsl:key name="classification-by-value"
             match="doc/report_info/javacore_list/javacore/javacore_classifications/classification_entry"
             use="@value"/>

    <xsl:template name="system_resources">
        <h3 id="system_resource_utilization_h3"><a id="toggleresourcesutil" href="javascript:expand_it(systemresources,toggleresourcesutil)" class="expandit">System resources utilization</a></h3>
        <div id="systemresources"  style="display:none;">
            <xsl:choose>
                <xsl:when test="//javacore_count = 0">
                    No javacore files were provided, so CPU utilization data cannot be calculated.
                </xsl:when>
                <xsl:when test="//javacore_count = 1">
                    Only one javacore file were provided, so CPU utilization data cannot be calculated.
                </xsl:when>
                <xsl:otherwise>
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
                    <div class="chart-container" style="overflow-x:auto;">
                        <canvas id="myChartCPUUsage" height="200" width="1400"></canvas>
                    </div>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="doc/report_info/verbose_gc_list/verbose_gc">
                    <xsl:choose>
                        <xsl:when test="//verbose_gc_list/@total_collects_in_time_limits = 0">
                            <br/>
                            There were no garbage collections withing the javacore time limits
                        </xsl:when>
                        <xsl:otherwise>
                            <h4>Garbage Collection Activity</h4>
                            <a id="togglememusagedoc" href="javascript:expand_it(memusagedoc,togglememusagedoc)" class="expandit">
                                What does this chart tell me?</a>
                            <div id="memusagedoc" style="display:none;">
                            This chart shows all the garbage collections that happened between the time
                            of the first and the last javacore in the data set.
                            Garbage collections that happened before the first
                            or after the last javacore generation time are not included.
                            If there are none or only one javacore provided, then the chart shows the data from all verbose GC log files.
                            <ul>
                                <li><strong>Heap Usage</strong>
                                    is the available Java heap memory over time,
                                    based on the garbage collection data from the verbose GC log files.
                                </li>
                                <li><strong>Total Heap</strong>
                                    is the maximum size of the Java heap, configured by using the Xmx Java argument,
                                    expressed in megabytes.
                                </li>
                                <li><strong>GC Pause Time</strong>
                                    is the duration of each garbage collection pause in milliseconds,
                                    indicating how long the application was stopped during garbage collection.
                                </li>
                                <li><strong>Nursery Usage</strong>
                                    shows the free memory in the nursery (young generation) space before and after each garbage collection,
                                    expressed in bytes. The nursery is where new objects are allocated.
                                </li>
                                <li><strong>Nursery Total</strong>
                                    is the total size of the nursery (young generation) space,
                                    expressed in bytes.
                                </li>
                                <li><strong>Tenure Usage</strong>
                                    shows the free memory in the tenure (old generation) space before and after each garbage collection,
                                    expressed in bytes. The tenure space holds long-lived objects.
                                </li>
                                <li><strong>Tenure Total</strong>
                                    is the total size of the tenure (old generation) space,
                                    expressed in bytes.
                                </li>
                        </ul>
                    </div>
                    <div id="systemresources_myChartGC" class="chart-container hide" style="overflow-x:auto;">
                        <canvas id="myChartGC" height="200" width="1400"></canvas>
                    </div>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <br/>
                    No verbosegc logs were provided, so verbose GC data cannot be shown.
                </xsl:otherwise>
            </xsl:choose>

            <!-- Thread Classification Over Time chart – only shown when ML is enabled
                 and at least two javacores are present so there is a time dimension. -->
            <xsl:if test="//@use_ml='True' and //javacore_count &gt; 1">
                <h4>Thread Classification Over Time</h4>
                <a id="toggleclassificationdoc" href="javascript:expand_it(classificationdoc,toggleclassificationdoc)" class="expandit">
                    What does this chart tell me?</a>
                <div id="classificationdoc" style="display:none;">
                    This chart shows how the number of thread snapshots belonging to each
                    machine-learning classification category changes over time.
                    The X axis represents the javacore generation time and the Y axis shows
                    the number of thread snapshots with that classification in each javacore.
                    Each line corresponds to one classification category.
                </div>
                <div class="chart-container" style="overflow-x:auto;">
                    <canvas id="myChartThreadClassifications" height="200" width="1400"></canvas>
                </div>
                <!-- Hidden data table consumed by loadChartThreadClassifications() in wait2scripts.js.
                     Row 0 = header (timestamp + one cell per category).
                     Rows 1..N = one row per javacore: ISO timestamp + counts per category. -->
                <div style="display:none;">
                    <table id="thread_classifications_data_table">
                        <thead>
                            <tr>
                                <th>timestamp</th>
                                <!-- Muenchian grouping: emit exactly one header cell per distinct
                                     classification label found across ALL javacore nodes. -->
                                <xsl:for-each select="doc/report_info/javacore_list/javacore/javacore_classifications/classification_entry[generate-id() = generate-id(key('classification-by-value', @value)[1])]">
                                    <th><xsl:value-of select="@value"/></th>
                                </xsl:for-each>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="doc/report_info/javacore_list/javacore">
                                <xsl:variable name="jc" select="."/>
                                <tr>
                                    <td><xsl:value-of select="javacore_file_time_stamp"/></td>
                                    <!-- One cell per distinct category; look up this javacore's count (0 if absent). -->
                                    <xsl:for-each select="//javacore_list/javacore/javacore_classifications/classification_entry[generate-id() = generate-id(key('classification-by-value', @value)[1])]">
                                        <xsl:variable name="cat" select="@value"/>
                                        <xsl:variable name="entry" select="$jc/javacore_classifications/classification_entry[@value=$cat]"/>
                                        <td>
                                            <xsl:choose>
                                                <xsl:when test="$entry"><xsl:value-of select="$entry/@count"/></xsl:when>
                                                <xsl:otherwise>0</xsl:otherwise>
                                            </xsl:choose>
                                        </td>
                                    </xsl:for-each>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                </div>
            </xsl:if>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
