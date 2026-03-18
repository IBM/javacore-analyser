<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="system_resources">
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
                    <xsl:if test="doc/data_types/type[text()='javacores']">
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
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
