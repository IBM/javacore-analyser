<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="top_blockers">
        <h3><a id="toggletop10blocker" href="javascript:expand_it(top10blocker,toggletop10blocker)" class="expandit">Top 10 Blockers</a></h3>
        <div id="top10blocker" style="display:none;">
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
                    <table id="top10_blocker_table" class="tablesorter">
                        <thead>
                            <tr>
                                <th class="ninety">Thread name</th>
                                <th>Number of different blocked threads</th>
                            </tr>
                        </thead>
                        <tbody>
                            <xsl:for-each select="doc/blockers/blocker">
                                <tr>
                                    <td class="left">
                                        <a class="right" target="_blank">
                                            <xsl:attribute name="href">
                                                <xsl:value-of select="concat('threads/thread_', blocker_hash, '.html')"/>
                                            </xsl:attribute>
                                            <xsl:value-of select="blocker_name"/>
                                        </a>
                                    </td>
                                    <td><xsl:value-of select="blocker_size"/></td>
                                </tr>
                            </xsl:for-each>
                        </tbody>
                    </table>
                </xsl:when>
                <xsl:otherwise> There are no blocking threads in Javacores </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
