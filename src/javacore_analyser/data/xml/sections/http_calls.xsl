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
                            <li><strong>Request URL and Details</strong>
                                is the URL of the HTTP request. Click "Show" to view request and response details.
                            </li>
                            <li><strong>Method</strong>
                                is the HTTP method used (GET, POST, PUT, DELETE, etc.).
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
                                <th class="sixty">Request URL and Details</th>
                                <th class="http-small">Method</th>
                                <th class="http-small">Status</th>
                                <th class="http-medium">Start Time</th>
                                <th class="http-small">Duration</th>
                                <th class="http-small">Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="//http_call">
                                <xsl:variable name="call_id" select="generate-id()"/>
                                <tr>
                                    <td class="left">
                                        <div>
                                            <xsl:value-of select="@url"/>
                                        </div>
                                        <div class="http-show-button">
                                            <a class="expandit">
                                                <xsl:attribute name="id">
                                                    <xsl:text>toggle_</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                </xsl:attribute>
                                                <xsl:attribute name="href">
                                                    <xsl:text>javascript:expand_http_details(</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                    <xsl:text>_details,toggle_</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                    <xsl:text>)</xsl:text>
                                                </xsl:attribute>
                                                Details
                                            </a>
                                        </div>
                                        <div>
                                            <xsl:attribute name="id">
                                                <xsl:value-of select="$call_id"/>
                                                <xsl:text>_details</xsl:text>
                                            </xsl:attribute>
                                            <xsl:attribute name="style">display:none;</xsl:attribute>
                                            <div class="http-call-details">
                                                <h4>Request Details</h4>
                                                <xsl:if test="string-length(@request_headers) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Headers:</strong>
                                                        <pre class="http-detail-pre">
                                                            <xsl:value-of select="@request_headers"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                                <xsl:if test="string-length(@request_cookies) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Cookies:</strong>
                                                        <pre class="http-detail-pre">
                                                            <xsl:value-of select="@request_cookies"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                                <xsl:if test="string-length(@request_content) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Content:</strong>
                                                        <pre class="http-detail-pre scrollable">
                                                            <xsl:value-of select="@request_content"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                                
                                                <h4>Response Details</h4>
                                                <xsl:if test="string-length(@response_headers) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Headers:</strong>
                                                        <pre class="http-detail-pre">
                                                            <xsl:value-of select="@response_headers"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                                <xsl:if test="string-length(@response_cookies) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Cookies:</strong>
                                                        <pre class="http-detail-pre">
                                                            <xsl:value-of select="@response_cookies"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                                <xsl:if test="string-length(@response_content) > 0">
                                                    <div class="http-detail-section">
                                                        <strong>Content:</strong>
                                                        <pre class="http-detail-pre scrollable">
                                                            <xsl:value-of select="@response_content"/>
                                                        </pre>
                                                    </div>
                                                </xsl:if>
                                            </div>
                                        </div>
                                    </td>
                                    <td><xsl:value-of select="@method"/></td>
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
