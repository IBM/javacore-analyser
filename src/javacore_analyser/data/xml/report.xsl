<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:variable name="displayed_stack_depth" select="50" />

    <!-- Reusable sort-button markup for Carbon DataTable sort headers.
         Call with: <xsl:call-template name="sort_th">
                        <xsl:with-param name="col">0</xsl:with-param>
                        <xsl:with-param name="label">Column Label</xsl:with-param>
                        <xsl:with-param name="class">sixty</xsl:with-param>  (optional)
                    </xsl:call-template>
    -->
    <xsl:template name="sort_th">
        <xsl:param name="col"/>
        <xsl:param name="label"/>
        <xsl:param name="class" select="''"/>
        <th>
            <xsl:if test="$class != ''">
                <xsl:attribute name="class"><xsl:value-of select="$class"/> cds--table-sort__header</xsl:attribute>
            </xsl:if>
            <xsl:if test="$class = ''">
                <xsl:attribute name="class">cds--table-sort__header</xsl:attribute>
            </xsl:if>
            <button class="cds--table-sort">
                <xsl:attribute name="data-col"><xsl:value-of select="$col"/></xsl:attribute>
                <xsl:attribute name="aria-label">Sort by <xsl:value-of select="$label"/></xsl:attribute>
                <span class="cds--table-header-label"><xsl:value-of select="$label"/></span>
                <svg class="cds--table-sort__icon-unsorted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
                <svg class="cds--table-sort__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M27.6 20.6L24 24.2V4h-2v20.2l-3.6-3.6L17 22l6 6 6-6zM9 4L3 10l1.4 1.4L8 7.8V28h2V7.8l3.6 3.6L15 10z"/></svg>
            </button>
        </th>
    </xsl:template>

    <!-- Import section templates -->
    <xsl:include href="sections/classification_config.xsl"/>
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
        <html class="cds--white">
            <head>
                <xsl:call-template name="header"/>
            </head>
            <body id="doc_body">
                <xsl:call-template name="body_content"/>
            </body>
            <script>loadChartGC();loadChartCPUUsage();loadChartThreadClassifications();</script>
            <script type="text/javascript" src="data/expand.js"> _ <!-- underscore character is required to prevent converting to <script /> which does not work --> </script>
        </html>
        <xsl:call-template name="expand_it"/>
    </xsl:template>
    
    <xsl:template name="body_content">
        <!-- Carbon Header bar with search -->
        <header class="cds--header" role="banner">
            <a class="cds--header__name" href="#">
                <span class="cds--header__name--prefix">IBM</span>&#160;Javacore Analyser Report
            </a>
            <div class="cds--header__global">
                <div class="cds--search cds--search--sm cds--search--light" role="search" aria-label="Search report">
                    <input id="search-input" class="cds--search-input" type="search" placeholder="Search…" aria-label="Search" />
                    <button data-search="search" id="search-button" class="cds--search-button" aria-label="Search">
                        <svg class="cds--search-magnifier" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                            <path d="M15.14 13.73L11 9.58A5.88 5.88 0 0 0 7 0a6 6 0 1 0 4.36 10.08l4.05 4.09a1 1 0 0 0 1.41 0 1 1 0 0 0-.68-1.44zM7 10a4 4 0 1 1 4-4 4 4 0 0 1-4 4z"/>
                        </svg>
                    </button>
                    <button data-search="clear" class="cds--search-close" aria-label="Clear search">✖</button>
                </div>
                <button data-search="prev" class="cds--btn cds--btn--ghost cds--btn--sm cds--header__action" aria-label="Previous result">◂</button>
                <button data-search="next" class="cds--btn cds--btn--ghost cds--btn--sm cds--header__action" aria-label="Next result">▸</button>
                <span id="search-counter" class="search-counter"></span>
            </div>
        </header>

        <main class="cds--content" id="main-content">
            <div class="cds--grid cds--grid--full-width">
                <div class="cds--row">
                    <div class="cds--col">

                        <xsl:if test="doc/report_info/javacores_generation_time">
                            <p class="cds--type-body-long-01 margined">
                                Data between&#160;
                                <strong><xsl:value-of select="doc/report_info/javacores_generation_time/starting_time"/></strong>
                                &#160;and&#160;
                                <strong><xsl:value-of select="doc/report_info/javacores_generation_time/end_time"/></strong>
                            </p>
                        </xsl:if>

                        <div class="cds--accordion">
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
                        </div>

                        <xsl:call-template name="footer"/>

                    </div>
                </div>
            </div>
        </main>
    </xsl:template>
    
    <xsl:template name="expand_it">
        <script language="JavaScript"></script>
    </xsl:template>

    <!-- Made with Bob -->
</xsl:stylesheet>
