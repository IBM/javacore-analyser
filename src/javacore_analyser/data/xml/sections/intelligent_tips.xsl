<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="intelligent_tips">
        <h3><a id="toggleintelligenttips" href="javascript:expand_it(intelligenttips,toggleintelligenttips)" class="expandit">Intelligent tips</a></h3>
        <div id="intelligenttips"  style="display:none;">
            <xsl:choose>
                <xsl:when test="doc/report_info/tips/@ai_tips != ''">
                    <xsl:value-of select="doc/report_info/tips/@ai_tips" disable-output-escaping="yes" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="doc/report_info/tips/tip">
                            <ul>
                                <xsl:for-each select="doc/report_info/tips/tip">
                                    <li><xsl:value-of select="current()"/></li>
                                </xsl:for-each>
                            </ul>
                        </xsl:when>
                        <xsl:otherwise>
                            We did not find any tips for you.
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
