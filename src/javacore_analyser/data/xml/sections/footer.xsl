<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="footer">
        <footer style="margin-top:2rem;padding-top:1rem;border-top:1px solid var(--cds-border-subtle-01,#e0e0e0);">
            <div class="margined">
                <a class="cds--link" href="https://github.com/IBM/javacore-analyser/wiki" target="_blank">Documentation</a>
            </div>
            <div class="margined">
                In case of any issues with the tool use Slack group:
                <a class="cds--link" href="https://ibm-ai-apps.slack.com/archives/C01KQ4X0ZK6">#wait-necromancers</a>
            </div>
            <div class="margined">
                Report Generation Time: <xsl:value-of select="doc/report_info/generation_time"/>
            </div>
        </footer>
        <div style="display: none;">
            <xsl:copy-of select="doc/gc-collections" />
        </div>
    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
