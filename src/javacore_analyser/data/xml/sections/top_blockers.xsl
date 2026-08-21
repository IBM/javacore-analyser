<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="top_blockers">
        <div class="cds--accordion__item" id="accordion-top-blockers">
            <button type="button" class="cds--accordion__heading"
                    aria-expanded="false" aria-controls="content-top-blockers"
                    onclick="this.closest('.cds--accordion__item').classList.toggle('cds--accordion__item--active'); this.setAttribute('aria-expanded', this.closest('.cds--accordion__item').classList.contains('cds--accordion__item--active')?'true':'false');">
                <svg class="cds--accordion__arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11 8L6 13 4.6 11.6 8.2 8 4.6 4.4 6 3z"/></svg>
                <span class="cds--accordion__title">Top 10 Blockers</span>
            </button>
            <div class="cds--accordion__wrapper"><div id="content-top-blockers" class="cds--accordion__content">
            <xsl:choose>
                <xsl:when test="doc/blockers/blocker">
                    <a id="toggleblockersdoc" href="javascript:expand_it(blockersdoc,toggleblockersdoc)" class="expandit">
                        What does this table tell me?</a>
                    <div id="blockersdoc" style="display:none;">
                        This table shows top ten threads that were blocking other threads most frequently,
                        based on the information in the javacore files.
                        <ul>
                            <li>
                                <strong>Thread name</strong>
                                is the name of the thread.
                            </li>
                            <li>
                                <strong>Number of different blocked threads</strong>
                                is the total number of times, across all javacore files, this thread was
                                blocking any other thread.
                            </li>
                        </ul>
                    </div>
                    <div class="cds--data-table-container">
                    <div class="cds--data-table-content">
                    <table id="top10_blocker_table" class="cds--data-table cds--data-table--zebra cds--data-table--sort" data-sort-initial-col="1" data-sort-initial-dir="desc">
                        <thead>
                            <tr>
                                <xsl:call-template name="sort_th">
                                    <xsl:with-param name="col">0</xsl:with-param>
                                    <xsl:with-param name="label">Thread name</xsl:with-param>
                                    <xsl:with-param name="class">ninety</xsl:with-param>
                                </xsl:call-template>
                                <xsl:call-template name="sort_th">
                                    <xsl:with-param name="col">1</xsl:with-param>
                                    <xsl:with-param name="label">Number of different blocked threads</xsl:with-param>
                                </xsl:call-template>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="doc/blockers/blocker">
                                <tr>
                                    <td class="left">
                                        <a class="cds--link" target="_blank">
                                            <xsl:attribute name="href">
                                                <xsl:value-of select="concat('threads/thread_', blocker_hash, '.html')"/>
                                            </xsl:attribute>
                                            <xsl:value-of select="blocker_name"/>
                                        </a>
                                    </td>
                                    <td>
                                        <span class="cds--tag cds--tag--red">
                                            <xsl:value-of select="blocker_size"/>
                                        </span>
                                    </td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                    </div>
                    </div>
                </xsl:when>
                <xsl:otherwise>
                    <div class="cds--inline-notification cds--inline-notification--info" role="status">
                        <div class="cds--inline-notification__details">
                            <p class="cds--inline-notification__text">There are no blocking threads in javacores</p>
                        </div>
                    </div>
                </xsl:otherwise>
            </xsl:choose>
            </div>
            </div>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
