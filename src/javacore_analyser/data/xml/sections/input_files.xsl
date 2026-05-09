<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="input_files">
        <h3><a id="togglejavacores" href="javascript:expand_it(javacores,togglejavacores)" class="expandit">Input Files</a></h3>
        <div id="javacores" style="display:none;">
            <xsl:choose>
                <xsl:when test="doc/report_info/javacore_list">
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
                    </xsl:when>
                    <xsl:otherwise> No javacore files </xsl:otherwise>
                </xsl:choose>
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
                                    <xsl:choose>
                                        <xsl:when test="//doc/report_info/javacore_list">
                                            <th class="ten">Number of collections in javacore time limits</th>
                                        </xsl:when>
                                    </xsl:choose>
                                    <th class="ten">Total number of collections in the file</th>
                                </tr>
                            </thead>
                            <tbody>
                                <xsl:for-each select="doc/report_info/verbose_gc_list/verbose_gc">
                                    <tr>
                                        <td class="left"><xsl:value-of select="verbose_gc_file_name"/></td>
                                        <xsl:choose>
                                            <xsl:when test="//doc/report_info/javacore_list">
                                                <td class="left"><xsl:value-of select="verbose_gc_collects"/></td>
                                            </xsl:when>
                                        </xsl:choose>
                                        <td class="left"><xsl:value-of select="verbose_gc_total_collects"/></td>
                                    </tr>
                                </xsl:for-each>
                            </tbody>
                        </table>
                    </xsl:when>
                    <xsl:otherwise> No verbose GC files </xsl:otherwise>
                </xsl:choose>
                <br/>
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
                    <xsl:otherwise> No HAR files </xsl:otherwise>
                </xsl:choose>
                <br/>
                <xsl:choose>
                    <xsl:when test="doc/plugins/*">
                        <h4>Plugin files</h4>
                        <a id="toggleplugindoc" href="javascript:expand_it(plugindoc,toggleplugindoc)" class="expandit">
                            What does this table tell me?</a>
                        <div id="plugindoc" style="display:none;">
                            This table shows all the files processed by custom plugins.
                            <ul>
                                <li>
                                    <strong>Plugin Name</strong>
                                    is the name of the plugin that processed the files.
                                </li>
                                <li>
                                    <strong>File Name</strong>
                                    is the name of the file processed by the plugin.
                                </li>
                                <li>
                                    <strong>Message Count</strong>
                                    is the number of messages or entries found in the file (if applicable).
                                </li>
                            </ul>
                        </div>
                        <table id="plugin_files_table">
                            <thead>
                                <tr>
                                    <th class="forty">Plugin Name</th>
                                    <th class="fifty">File Name</th>
                                    <th class="ten">Message Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                <xsl:for-each select="doc/plugins/*">
                                    <xsl:variable name="plugin_name">
                                        <xsl:choose>
                                            <xsl:when test="local-name() = 'liberty_logs'">Liberty System Out</xsl:when>
                                            <xsl:otherwise><xsl:value-of select="local-name()"/></xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:variable>
                                    <!-- Handle log_files/log_file structure (Liberty plugin) -->
                                    <xsl:for-each select=".//log_files/log_file">
                                        <tr>
                                            <td class="left"><xsl:value-of select="$plugin_name"/></td>
                                            <td class="left"><xsl:value-of select="@file"/></td>
                                            <td class="left">
                                                <xsl:choose>
                                                    <xsl:when test="@message_count">
                                                        <xsl:value-of select="@message_count"/>
                                                    </xsl:when>
                                                    <xsl:otherwise>N/A</xsl:otherwise>
                                                </xsl:choose>
                                            </td>
                                        </tr>
                                    </xsl:for-each>
                                    <!-- Handle files/file structure (generic plugins) -->
                                    <xsl:for-each select=".//files/file">
                                        <tr>
                                            <td class="left"><xsl:value-of select="$plugin_name"/></td>
                                            <td class="left"><xsl:value-of select="@name"/></td>
                                            <td class="left">N/A</td>
                                        </tr>
                                    </xsl:for-each>
                                </xsl:for-each>
                            </tbody>
                        </table>
                    </xsl:when>
                    <xsl:otherwise> No plugin files </xsl:otherwise>
                </xsl:choose>
            </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
