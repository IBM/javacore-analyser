<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
-->

<!--
  Classification categories that are noisy (i.e. present in almost every thread set
  and not particularly interesting on their own).  These are struck through in the
  Thread Classification Over Time legend by default so they do not dominate the chart.
  The user can click their legend entry to toggle them back on.

  To change which categories are considered noisy, edit the value of
  $noisy_classifications below.  Each name must appear between pipe characters:
  |Category Name|
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:variable name="noisy_classifications">|Java Internal|Liberty Internal|Wait For Condition|</xsl:variable>

</xsl:stylesheet>
