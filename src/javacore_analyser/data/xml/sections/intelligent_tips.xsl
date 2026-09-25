<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="intelligent_tips">
        <h3><a id="toggleintelligenttips" href="javascript:expand_it(intelligenttips,toggleintelligenttips)" class="expandit">Intelligent tips</a></h3>
        <div id="intelligenttips"  style="display:none;">
            <p>
                <a id="toggleintelligenttipshelp" 
                        href="javascript:expand_it(intelligenttipshelp,toggleintelligenttipshelp)" class="expandit">
                    What does this section tell me?
                </a>
            </p>
            <div id="intelligenttipshelp" style="display:none;">
                <ul>
                    <li>
                        &#x26A0;&#xFE0F; <strong>Warning</strong> 
                        &#x2013; the data input is unreliable. Results based on this data should be treated with caution.
                    </li>
                    <li>
                        &#x1F4A1; <strong>Tip</strong> 
                        &#x2013; a suggestion about what can be a cause of performance degradation.
                    </li>
                </ul>
            </div>
            <xsl:choose>
                <xsl:when test="doc/report_info/tips/@ai_tips != ''">
                    <xsl:value-of select="doc/report_info/tips/@ai_tips" disable-output-escaping="yes" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="doc/report_info/tips/tip">
                            <ul>
                                <xsl:for-each select="doc/report_info/tips/tip">
                                    <xsl:choose>
                                        <xsl:when test="@type = 'WARNING'">
                                            <li>&#x26A0;&#xFE0F; <xsl:value-of select="current()" disable-output-escaping="yes"/></li>
                                        </xsl:when>
                                        <xsl:when test="@type = 'TIP'">
                                            <li>&#x1F4A1; <xsl:value-of select="current()" disable-output-escaping="yes"/></li>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <li><xsl:value-of select="current()" disable-output-escaping="yes"/></li>
                                        </xsl:otherwise>
                                    </xsl:choose>
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
