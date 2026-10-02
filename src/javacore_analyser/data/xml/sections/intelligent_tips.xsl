<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="intelligent_tips">
        <div class="cds--accordion__item" id="accordion-intelligent-tips">
            <button type="button" class="cds--accordion__heading"
                    aria-expanded="false" aria-controls="content-intelligent-tips"
                    onclick="this.closest('.cds--accordion__item').classList.toggle('cds--accordion__item--active'); this.setAttribute('aria-expanded', this.closest('.cds--accordion__item').classList.contains('cds--accordion__item--active')?'true':'false');">
                <svg class="cds--accordion__arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11 8L6 13 4.6 11.6 8.2 8 4.6 4.4 6 3z"/></svg>
                <span class="cds--accordion__title">Intelligent Tips</span>
            </button>
            <div class="cds--accordion__wrapper"><div id="content-intelligent-tips" class="cds--accordion__content">
                <xsl:choose>
                    <xsl:when test="doc/report_info/tips/@ai_tips != ''">
                        <div class="cds--tile chart-tile">
                            <p class="cds--type-label-01 ai-tile-label">AI-generated analysis</p>
                            <xsl:value-of select="doc/report_info/tips/@ai_tips" disable-output-escaping="yes" />
                        </div>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="doc/report_info/tips/tip">
                                <xsl:for-each select="doc/report_info/tips/tip">
                                    <xsl:variable name="tiptext" select="current()"/>
                                    <xsl:choose>
                                        <xsl:when test="starts-with($tiptext, '[WARNING]')">
                                            <div class="cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--warning report-notification" role="status">
                                                <svg class="cds--inline-notification__icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm-1.1 6h2.2v11h-2.2V8zM16 25c-.8 0-1.5-.7-1.5-1.5S15.2 22 16 22s1.5.7 1.5 1.5S16.8 25 16 25z"/></svg>
                                                <div class="cds--inline-notification__details">
                                                    <p class="cds--inline-notification__text"><xsl:value-of select="$tiptext" disable-output-escaping="yes"/></p>
                                                </div>
                                            </div>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <div class="cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--info report-notification" role="status">
                                                <svg class="cds--inline-notification__icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M17 22v-8h-4v2h2v6h-3v2h8v-2zm-1-12a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/><path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm0 26C9.4 28 4 22.6 4 16S9.4 4 16 4s12 5.4 12 12-5.4 12-12 12z"/></svg>
                                                <div class="cds--inline-notification__details">
                                                    <p class="cds--inline-notification__text"><xsl:value-of select="$tiptext" disable-output-escaping="yes"/></p>
                                                </div>
                                            </div>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <div class="cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--info report-notification" role="status">
                                    <svg class="cds--inline-notification__icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M17 22v-8h-4v2h2v6h-3v2h8v-2zm-1-12a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/><path d="M16 2C8.3 2 2 8.3 2 16s6.3 14 14 14 14-6.3 14-14S23.7 2 16 2zm0 26C9.4 28 4 22.6 4 16S9.4 4 16 4s12 5.4 12 12-5.4 12-12 12z"/></svg>
                                    <div class="cds--inline-notification__details">
                                        <p class="cds--inline-notification__text">No tips found for this data set.</p>
                                    </div>
                                </div>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </div>
            </div>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
