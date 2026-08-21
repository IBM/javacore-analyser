<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="http_calls">
        <xsl:choose>
            <xsl:when test="doc/har_files">
                <div class="cds--accordion__item" id="accordion-http-calls">
                    <button type="button" class="cds--accordion__heading"
                            aria-expanded="false" aria-controls="content-http-calls"
                            onclick="this.closest('.cds--accordion__item').classList.toggle('cds--accordion__item--active'); this.setAttribute('aria-expanded', this.closest('.cds--accordion__item').classList.contains('cds--accordion__item--active')?'true':'false');">
                        <svg class="cds--accordion__arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11 8L6 13 4.6 11.6 8.2 8 4.6 4.4 6 3z"/></svg>
                        <span class="cds--accordion__title">HTTP Calls</span>
                    </button>
                    <div class="cds--accordion__wrapper"><div id="content-http-calls" class="cds--accordion__content">
                    <a id="togglehttpcallsdoc" href="javascript:expand_it(httpcallsdoc,togglehttpcallsdoc)" class="expandit">
                        What does this table tell me?</a>
                        <div id="httpcallsdoc" style="display:none;">
                        The table shows the HTTP calls that are included in the HAR files from the data set.
                        The table can be sorted by clicking on a column header.
                        Rows highlighted in <span style="background-color:#ffcccc;padding:0 4px;">red</span> finished
                        with a 4xx or 5xx error status. Rows highlighted in
                        <span style="background-color:#fff3cd;padding:0 4px;">yellow</span> took longer than 5 seconds.
                        <ul>
                            <li><strong>Request URL and Details</strong>
                                is the URL of the HTTP request. Click "Details" to view request and response details,
                                including a traffic timing breakdown (DNS, connect, SSL, send, wait, receive).
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
                    <div class="cds--data-table-container">
                    <div class="cds--data-table-content">
                    <table id="HttpCallTable" class="cds--data-table cds--data-table--zebra cds--data-table--sort">
                        <thead>
                            <tr>
                                <th class="fifty cds--table-sort__header" data-col="0">
                                    <button class="cds--table-sort" data-col="0" aria-label="Sort by Request URL">
                                        <span class="cds--table-header-label">Request URL and Details</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
                                <th class="http-small cds--table-sort__header" data-col="1">
                                    <button class="cds--table-sort" data-col="1" aria-label="Sort by Method">
                                        <span class="cds--table-header-label">Method</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
                                <th class="http-small cds--table-sort__header" data-col="2">
                                    <button class="cds--table-sort" data-col="2" aria-label="Sort by Status">
                                        <span class="cds--table-header-label">Status</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
                                <th class="http-medium cds--table-sort__header" data-col="3">
                                    <button class="cds--table-sort" data-col="3" aria-label="Sort by Start Time">
                                        <span class="cds--table-header-label">Start Time</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
                                <th class="http-medium cds--table-sort__header" data-col="4">
                                    <button class="cds--table-sort" data-col="4" aria-label="Sort by Duration">
                                        <span class="cds--table-header-label">Duration</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
                                <th class="http-medium cds--table-sort__header" data-col="5">
                                    <button class="cds--table-sort" data-col="5" aria-label="Sort by Size">
                                        <span class="cds--table-header-label">Size</span>
                                        <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                        <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                                    </button>
                                </th>
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
                                            <a class="cds--btn cds--btn--ghost cds--btn--sm expandit">
                                                <xsl:attribute name="id">
                                                    <xsl:text>toggle_</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                </xsl:attribute>
                                                <xsl:attribute name="href">
                                                    <xsl:text>javascript:expand_http_details(document.getElementById('</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                    <xsl:text>_details'),document.getElementById('toggle_</xsl:text>
                                                    <xsl:value-of select="$call_id"/>
                                                    <xsl:text>'))</xsl:text>
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
                                                <h4>Traffic Timing Breakdown</h4>
                                                 <!-- Div-based layout avoids nested <th>/<tr>/<td> inside the outer
                                                      sortable table, which would confuse tablesorter's header detection. -->
                                                 <div class="timing-grid">
                                                     <div class="timing-grid__header">Phase</div>
                                                     <div class="timing-grid__header">Duration (ms)</div>
                                                     <div class="timing-grid__header">Bar</div>
                                                     <xsl:if test="@timing_blocked &gt;= 0">
                                                         <div class="timing-grid__cell">Blocked</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_blocked"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-blocked">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_blocked div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_dns &gt;= 0">
                                                         <div class="timing-grid__cell">DNS</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_dns"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-dns">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_dns div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_connect &gt;= 0">
                                                         <div class="timing-grid__cell">Connect</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_connect"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-connect">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_connect div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_ssl &gt;= 0">
                                                         <div class="timing-grid__cell">SSL</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_ssl"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-ssl">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_ssl div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_send &gt;= 0">
                                                         <div class="timing-grid__cell">Send</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_send"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-send">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_send div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_wait &gt;= 0">
                                                         <div class="timing-grid__cell">Wait</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_wait"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-wait">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_wait div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                     <xsl:if test="@timing_receive &gt;= 0">
                                                         <div class="timing-grid__cell">Receive</div>
                                                         <div class="timing-grid__cell"><xsl:value-of select="@timing_receive"/></div>
                                                         <div class="timing-grid__cell timing-bar-cell">
                                                             <div class="timing-bar timing-receive">
                                                                 <xsl:attribute name="style">
                                                                     <xsl:text>width:</xsl:text>
                                                                     <xsl:value-of select="@timing_receive div @duration * 100"/>
                                                                     <xsl:text>%</xsl:text>
                                                                 </xsl:attribute>
                                                                 <xsl:text> </xsl:text>
                                                             </div>
                                                         </div>
                                                     </xsl:if>
                                                 </div>

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
                                                <span class="cds--tag cds--tag--red"><xsl:value-of select="@status"/></span>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="@status"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td><xsl:value-of select="@start_time"/></td>
                                    <td>
                                        <xsl:choose>
                                            <xsl:when test="@duration &gt; 5000">
                                                <xsl:attribute name="class">http_slow</xsl:attribute>
                                            </xsl:when>
                                        </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="@duration &gt; 5000">
                                                <div class="info"><xsl:value-of select="format-number(@duration, '0.000')"/>
                                                    <span class="infotooltip">Request took longer than 5 seconds&#10;<xsl:value-of select="@timings"/></span>
                                                </div>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <div class="info"><xsl:value-of select="format-number(@duration, '0.000')"/>
                                                    <span class="infotooltip"><xsl:value-of select="@timings"/></span>
                                                </div>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </td>
                                    <td><xsl:value-of select="@size"/></td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                    </div>
                    </div>
                    </div>
                    </div>
                </div>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
