<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="system_information">
        <h3><a id="toggle_system_properties"
               href="javascript:expand_it(system_properties, toggle_system_properties)"
               class="expandit">System Information</a></h3>
        <div id="system_properties" style="display:none;">
        <!--    <xsl:if test="doc/system_info/@ai_overview != ''">
                <h4>AI Overview:</h4>
                    <xsl:value-of select="doc/system_info/@ai_overview" disable-output-escaping="yes"/>
            </xsl:if>
        -->
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
                    <tr>
                        <td>JVM startup time</td>
                        <td class="left"><xsl:value-of select="doc/system_info/jvm_start_time"/></td>
                    </tr>
                     <tr>
                        <td>Command line</td>
                        <td class="left"><xsl:value-of select="doc/system_info/cmd_line"/></td>
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
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
