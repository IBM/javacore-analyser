<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:variable name="displayed_stack_depth" select="50" />

    <!-- Import section templates -->
    <xsl:include href="sections/header.xsl"/>
    <xsl:include href="sections/input_files.xsl"/>
    <xsl:include href="sections/system_information.xsl"/>
    <xsl:include href="sections/intelligent_tips.xsl"/>
    <xsl:include href="sections/system_resources.xsl"/>
    <xsl:include href="sections/top_blockers.xsl"/>
    <xsl:include href="sections/all_threads.xsl"/>
    <xsl:include href="sections/all_code.xsl"/>
    <xsl:include href="sections/http_calls.xsl"/>
    <!-- plugins.xsl is generated dynamically at runtime and contains XSL templates from loaded plugins -->
    <xsl:include href="plugins.xsl"/>
    <xsl:include href="sections/footer.xsl"/>

    <xsl:template match="index">
        <html>
            <head>
                <xsl:call-template name="header"/>
            </head>
            <body id="doc_body">
                <xsl:call-template name="body_content"/>
            </body>
            <script>loadChartGC();loadChartCPUUsage();</script>
            <script type="text/javascript" src="data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    
    <xsl:template name="body_content">
        <div class="searchbar">
            <input id="search-input" type="search" />
            <button data-search="search" id="search-button">Search</button>
            <button data-search="next">Next</button>
            <button data-search="prev">Prev</button>
            <button data-search="clear">✖</button>
        </div>
        <div class="content">
            <h1>Javacore Analyser Report</h1>

            <xsl:if test="doc/report_info/javacores_generation_time">
                <div class="margined">
                    from data between
                    <b><xsl:value-of select="doc/report_info/javacores_generation_time/starting_time"/></b> and
                    <b><xsl:value-of select="doc/report_info/javacores_generation_time/end_time"/></b>
                </div>
            </xsl:if>
            
            <xsl:call-template name="input_files"/>
            <xsl:if test="doc/data_types/type[text()='javacores']">
                <xsl:call-template name="system_information"/>
            </xsl:if>
            <xsl:call-template name="intelligent_tips"/>
            <xsl:call-template name="system_resources"/>
            <xsl:if test="doc/data_types/type[text()='javacores']">
                <xsl:call-template name="top_blockers"/>
                <xsl:call-template name="all_threads"/>
                <xsl:call-template name="all_code"/>
            </xsl:if>

            <xsl:call-template name="http_calls"/>
            <xsl:call-template name="plugins"/>
            <xsl:call-template name="footer"/>
        </div>
    </xsl:template>
    
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>

    <!-- Made with Bob -->
</xsl:stylesheet>
