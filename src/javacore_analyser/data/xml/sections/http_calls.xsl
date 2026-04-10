<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="http_calls">
        <xsl:choose>
            <xsl:when test="doc/har_files">
                <h3><a  id="toggle_http_calls" href="javascript:expand_it(http_calls,toggle_http_calls)" class="expandit">HTTP calls</a></h3>
                <div id="http_calls" style="display:none;" >
                    <a id="togglehttpcallsdoc" href="javascript:expand_it(httpcallsdoc,togglehttpcallsdoc)" class="expandit">
                        What does this table tell me?</a>
                        <div id="httpcallsdoc" style="display:none;">
                        The table shows the HTTP calls that are included in the HAR files from the data set.
                        The table can be sorted by clicking on a column header.
                        <ul>
                            <li><strong>URL</strong>
                                is the URL of the HTTP request.
                            </li>
                            <li><strong>Status</strong>
                                is the HTTP response code.
                            </li>
                            <li><strong>Start time</strong>
                                is the time when the HTTP request was made.
                            </li>
                            <li><strong>Duration</strong>
                                is the amount of time it took to complete the HTTP call, in milliseconds.
                            </li>
                            <li><strong>Size</strong>
                                is size of the response body, in bytes.
                            </li>
                        </ul>
                    </div>
                    <table id="HttpCallTable" class="tablesorter">
                        <thead>
                            <tr>
                                <th  class="sixty">URL</th>
                                <th>Status</th>
                                <th>Start Time</th>
                                <th>Duration</th>
                                <th>Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="//http_call">
                                <tr>
                                    <td class="left"><xsl:value-of select="@url"/></td>
                                    <td>
                                        <xsl:choose>
                                            <xsl:when test="@success='False'">
                                                <xsl:attribute name="class">http_failure</xsl:attribute>
                                            </xsl:when>
                                        </xsl:choose>
                                        <xsl:value-of select="@status"/>
                                    </td>
                                    <td><xsl:value-of select="@start_time"/></td>
                                    <td>
                                        <div class="info"><xsl:value-of select="@duration"/>
                                            <span class="infotooltip"><xsl:value-of select="@timings"/></span>
                                        </div>
                                    </td>
                                    <td><xsl:value-of select="@size"/></td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                </div>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
