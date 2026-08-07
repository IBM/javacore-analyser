#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import os

from lxml import etree


class FileResolver(etree.Resolver):
    """
    Custom URI resolver for XSLT processing to handle xsl:include directives.

    This resolver enables lxml's XSLT processor to locate and include external XSL files
    referenced via <xsl:include> elements in the main XSLT stylesheet. It handles file://
    URIs by converting them to file system paths that lxml can access.

    The resolver is necessary because report.xsl has been modularised into separate section
    files (header.xsl, footer.xsl, etc.) to support a plugin architecture. Without this
    resolver, lxml would fail to locate the included files.

    See: https://lxml.de/resolvers.html for lxml resolver documentation
    """

    def __init__(self, temp_path=None):
        super().__init__()
        self.temp_path = temp_path

    def resolve(self, url, id, context):
        """
        Resolve a URI to a file system path.

        Args:
            url (str): The URI to resolve (may include file:// prefix)
            id (str): The document identifier (unused)
            context: The resolution context from lxml

        Returns:
            The resolved file content if the file exists, None otherwise
        """
        # Remove file:// prefix if present to get the actual file path
        if url.startswith('file://'):
            url = url[7:]  # Remove 'file://' prefix

        # If the file exists on the file system, resolve it
        if os.path.exists(url):
            return self.resolve_filename(url, context)

        return self.resolve_filename(self.temp_path + os.sep + url, context)
