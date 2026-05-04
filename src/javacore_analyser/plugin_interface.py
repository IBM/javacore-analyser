#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Plugin interface definitions for javacore-analyser.

This module provides the abstract base class used by custom data source plugins.
Plugins extend :class:`DataSourcePlugin` to integrate additional diagnostic data
types into javacore-analyser without modifying the core codebase.

A plugin is responsible for:

- Identifying itself with a unique internal name and a human-readable display name
- Declaring file discovery patterns for candidate input files
- Validating whether specific files can be processed
- Parsing one or more matching files into a structured data model
- Generating XML nodes for integration into the final report
- Generating HTML content for direct injection into the final report

Optional extension points are also provided for plugins that need to:

- Expose a time range for correlation with javacore data
- Publish summary metrics for dashboards or overview sections

The processed data structure returned by :meth:`process_files` is intentionally
plugin-defined, which gives plugin authors flexibility to model their own
diagnostic domain while still conforming to a consistent lifecycle.

HTML Generation:
Plugins must implement :meth:`generate_html` to produce HTML content that will be
injected directly into the report. The HTML should use CSS classes from the existing
report for consistent styling (e.g., 'tablesorter', 'expandit', 'error_row',
'warning_row'). Use the html.escape() function to safely escape user data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.dom.minidom import Document, Element


class DataSourcePlugin(ABC):
    """
    Abstract base class for custom data source plugins.

    Users extend this class to add support for new diagnostic data types such as
    thread dumps, heap dumps, custom log files, or any other artefacts that can
    be correlated with javacore analysis.

    Plugin implementations are expected to provide a stable contract across the
    following lifecycle stages:

    1. Discovery
       The plugin declares one or more glob-style file patterns through
       :meth:`get_file_patterns`.

    2. Validation
       Each candidate file is checked with :meth:`can_process` to confirm that
       the plugin can safely parse it.

    3. Processing
       Matching files are parsed by :meth:`process_files`, which returns a
       plugin-defined dictionary containing structured analysis results.

    4. Report integration
       The processed data is transformed into an XML element by
       :meth:`generate_xml` so it can be included in the generated report.
       
    5. HTML generation
       The plugin generates HTML content via :meth:`generate_html` which is
       injected directly into the final report.

    Optional methods let the plugin contribute temporal correlation metadata
    and summary metrics without forcing all plugins to support those capabilities.
    """

    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Return the unique plugin identifier.

        This value is intended for internal identification, storage, and lookup.
        It should be stable, short, and unique across all loaded plugins.

        Example values include ``"threaddump"``, ``"heapdump"``, or
        ``"customlog"``.

        Returns:
            A unique plugin identifier.
        """

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Return the human-readable plugin name.

        This value is intended for display in logs, reports, and user-facing
        output.

        Example values include ``"Thread Dumps"``, ``"Heap Dumps"``, or
        ``"Custom Application Logs"``.

        Returns:
            A human-readable plugin name.
        """

    @abstractmethod
    def get_file_patterns(self) -> List[str]:
        """
        Return glob patterns used for file discovery.

        The returned patterns are used to locate candidate files before
        :meth:`can_process` performs more specific validation.

        Example values include ``["*.tdump", "*threaddump*.txt"]``.

        Returns:
            A list of glob patterns for files supported by the plugin.
        """

    @abstractmethod
    def can_process(self, filepath: str) -> bool:
        """
        Validate whether the plugin can process the specified file.

        This method should perform lightweight validation, such as checking file
        extensions, headers, magic strings, or expected structural markers.

        Args:
            filepath: Path to the file to validate.

        Returns:
            ``True`` if the plugin can process the file, otherwise ``False``.
        """

    @abstractmethod
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Process input files and return plugin-defined structured data.

        Implementations should parse the supplied files and return a dictionary
        describing the extracted information. The exact structure of the
        dictionary is defined by the plugin.

        Args:
            filepaths: List of file paths to process.

        Returns:
            A dictionary containing processed data for later report integration.
        """

    @abstractmethod
    def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Element:
        """
        Generate an XML representation of processed plugin data.

        The returned element is intended to be inserted into the main report XML
        document.

        Args:
            doc: XML document used to create DOM elements.
            data: Processed data previously returned by :meth:`process_files`.

        Returns:
            An XML element representing the plugin data for report integration.
        """

    @abstractmethod
    def generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML content for direct injection into the report.

        This method must return a complete HTML fragment that will be inserted
        directly into the final report. The HTML should use CSS classes from the
        existing report for consistent styling.

        Available CSS classes include:
        - 'tablesorter': For sortable tables
        - 'expandit': For collapsible section headers
        - 'error_row': For error highlighting in table rows
        - 'warning_row': For warning highlighting in table rows
        - 'error_cell': For error highlighting in table cells

        The HTML typically includes:
        - A collapsible section header (h3 with expandit class)
        - A hidden div containing the section content
        - Tables with thead/tbody structure
        - Proper escaping of user data using html.escape()

        Example structure:
            <h3><a id="toggle_section" href="javascript:expand_it(section,toggle_section)"
                   class="expandit">Section Title</a></h3>
            <div id="section" style="display:none;">
                <table class="tablesorter">
                    <thead><tr><th>Column</th></tr></thead>
                    <tbody><tr><td>Data</td></tr></tbody>
                </table>
            </div>

        Args:
            data: Processed data previously returned by :meth:`process_files`.

        Returns:
            HTML string to be injected into the report, or empty string if no
            content should be displayed.
        """

    def get_time_range(self, data: Dict[str, Any]) -> Optional[tuple[datetime, datetime]]:
        """
        Return the time range represented by the processed data.

        This is used for temporal correlation with javacores or other time-based
        artefacts. Plugins that do not operate on time-based data may return
        ``None``.

        Args:
            data: Processed data previously returned by :meth:`process_files`.

        Returns:
            A ``(start_time, end_time)`` tuple, or ``None`` if no applicable
            time range exists.
        """
        return None

    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return key summary metrics derived from processed plugin data.

        These metrics can be used by dashboards, report summaries, or overview
        sections to highlight the most important results from the plugin.

        Args:
            data: Processed data previously returned by :meth:`process_files`.

        Returns:
            A dictionary mapping metric names to metric values.
        """
        return {}

    def get_description(self) -> str:
        """
        Return a detailed description of what the plugin does.

        This description should explain:
        - What type of data the plugin processes
        - What analysis or insights it provides
        - What file formats it supports
        - Any special requirements or limitations

        This information is useful for documentation, help text, and plugin
        discovery interfaces.

        Returns:
            A multi-line string describing the plugin's purpose and functionality.
        """
        return f"{self.get_display_name()} plugin - no description provided."

# Made with Bob
