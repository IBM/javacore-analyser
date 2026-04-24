#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Example Liberty SystemOut Plugin for javacore-analyser.

This plugin demonstrates how to create a custom data source plugin that processes
WebSphere Liberty systemout.log files and integrates them into the javacore-analyser report.

This serves as a reference implementation for plugin developers.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional
from xml.dom.minidom import Document, Element

from javacore_analyser.plugin_interface import DataSourcePlugin


class LibertySystemOutPlugin(DataSourcePlugin):
    """
    Simple plugin to analyze WebSphere Liberty systemout.log files.

    This plugin processes Liberty server log files and extracts basic statistics
    about log messages, errors, and warnings.

    Example Liberty log format:
        [1/3/24, 10:15:30:123 EST] 00000001 com.ibm.ws.kernel.launch A CWWKE0001I: Server launched.
        [1/3/24, 10:16:00:789 EST] 00000045 com.example.MyClass E SRVE0315E: An exception occurred
    """

    def get_plugin_name(self) -> str:
        """Return unique plugin identifier."""
        return "liberty_systemout"

    def get_display_name(self) -> str:
        """Return human-readable plugin name."""
        return "Liberty System Out"

    def get_description(self) -> str:
        """Return detailed description of the plugin."""
        return """
Liberty SystemOut Plugin - Analyzes WebSphere Liberty server log files

This plugin processes Liberty server logs (systemout.log, console.log, messages.log)
and extracts diagnostic information including:

- Message counts by severity level (Audit, Warning, Error, Info, Other)
- Most frequently occurring Liberty message IDs
- Individual log file statistics
- Error and warning summaries

Supported file formats:
- systemout.log (Liberty standard output log)
- console.log (Liberty console log)
- messages.log (Liberty messages log)
- Rotated logs matching *systemout*.log pattern

The plugin validates files by checking for Liberty-specific log format markers:
- Timestamp format: [MM/DD/YY, HH:MM:SS:mmm TZ]
- Message ID format: AAAA####X (4 letters + 4 digits + severity letter)

File size limits: 100 bytes minimum, 500MB maximum
        """.strip()

    def get_file_patterns(self) -> List[str]:
        """Return glob patterns for Liberty log file discovery."""
        return ['systemout.log', 'console.log', 'messages.log', 'trace.log', '*systemout*.log']

    def can_process(self, filepath: str) -> bool:
        """
        Validate whether this plugin can process the given file.

        Checks for Liberty log format markers in the first few lines.
        """
        try:
            if not os.path.exists(filepath):
                return False

            file_size = os.path.getsize(filepath)
            if file_size < 100 or file_size > 500 * 1024 * 1024:  # 100 bytes to 500MB
                return False

            # Check for Liberty log format in first 20 lines
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                sample = ''.join(f.readline() for _ in range(20))
                # Look for Liberty timestamp pattern and message ID pattern
                has_timestamp = bool(re.search(r'\[\d{1,2}/\d{1,2}/\d{2,4}', sample))
                has_message_id = bool(re.search(r'[A-Z]{4}\d{4}[AWEIO]:', sample))
                return has_timestamp and has_message_id

        except Exception as e:
            logging.warning(f"Error validating file {filepath}: {e}")
            return False

    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Process Liberty log files and extract structured data.

        Counts messages by severity level and identifies most common message IDs.
        """
        logging.info(f"Processing {len(filepaths)} Liberty log files")

        total_messages = 0
        severity_counts = {'A': 0, 'W': 0, 'E': 0, 'I': 0, 'O': 0}
        message_id_counts = {}
        log_files = []

        # Simple regex to match Liberty log lines
        log_pattern = re.compile(r'\[([^\]]+)\].*?([AWEIO])\s+([\w\d]+):', re.MULTILINE)

        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find all log entries
                matches = log_pattern.findall(content)
                file_message_count = len(matches)
                total_messages += file_message_count

                # Count severities and message IDs
                file_severity_counts = {'A': 0, 'W': 0, 'E': 0, 'I': 0, 'O': 0}
                for timestamp, severity, message_id in matches:
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    file_severity_counts[severity] = file_severity_counts.get(severity, 0) + 1
                    message_id_counts[message_id] = message_id_counts.get(message_id, 0) + 1

                log_files.append({
                    'file': os.path.basename(filepath),
                    'message_count': file_message_count,
                    'severity_counts': file_severity_counts
                })

                logging.info(f"Processed {filepath}: {file_message_count} messages")

            except Exception as e:
                logging.error(f"Error processing {filepath}: {e}")
                log_files.append({
                    'file': os.path.basename(filepath),
                    'error': str(e),
                    'message_count': 0
                })

        # Get top 10 message IDs
        top_message_ids = dict(sorted(message_id_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        return {
            'log_files': log_files,
            'total_files': len(filepaths),
            'total_messages': total_messages,
            'severity_counts': severity_counts,
            'top_message_ids': top_message_ids
        }

    def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Element:
        """
        Generate XML representation of Liberty log data for report integration.
        """
        root = doc.createElement('liberty_logs')
        root.setAttribute('total_files', str(data['total_files']))
        root.setAttribute('total_messages', str(data['total_messages']))

        # Add severity summary
        severity_node = doc.createElement('severity_summary')
        severity_names = {'A': 'Audit', 'W': 'Warning', 'E': 'Error', 'I': 'Info', 'O': 'Other'}
        for severity, count in data['severity_counts'].items():
            sev_node = doc.createElement('severity')
            sev_node.setAttribute('level', severity)
            sev_node.setAttribute('name', severity_names.get(severity, 'Unknown'))
            sev_node.setAttribute('count', str(count))
            severity_node.appendChild(sev_node)
        root.appendChild(severity_node)

        # Add top message IDs
        msg_ids_node = doc.createElement('top_message_ids')
        for msg_id, count in data['top_message_ids'].items():
            msg_node = doc.createElement('message_id')
            msg_node.setAttribute('id', msg_id)
            msg_node.setAttribute('count', str(count))
            msg_ids_node.appendChild(msg_node)
        root.appendChild(msg_ids_node)

        # Add individual log file information
        logs_node = doc.createElement('log_files')
        for log in data['log_files']:
            log_node = doc.createElement('log_file')
            log_node.setAttribute('file', log['file'])
            log_node.setAttribute('message_count', str(log['message_count']))

            if 'error' in log:
                log_node.setAttribute('error', log['error'])
            else:
                # Add severity distribution for this log
                for severity, count in log.get('severity_counts', {}).items():
                    sev_node = doc.createElement('severity')
                    sev_node.setAttribute('level', severity)
                    sev_node.setAttribute('count', str(count))
                    log_node.appendChild(sev_node)

            logs_node.appendChild(log_node)
        root.appendChild(logs_node)

        return root

    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return key summary metrics for dashboard display."""
        severity_counts = data['severity_counts']

        metrics = {
            'Total Log Files': data['total_files'],
            'Total Messages': data['total_messages'],
            'Errors': severity_counts.get('E', 0),
            'Warnings': severity_counts.get('W', 0)
        }

        # Add most frequent message ID if available
        if data['top_message_ids']:
            top_msg = list(data['top_message_ids'].items())[0]
            metrics['Most Frequent Message'] = f"{top_msg[0]} ({top_msg[1]})"

        return metrics

    def generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML content for Liberty log data to be injected into the report.
        
        This method converts the processed Liberty log data into HTML format using
        Python string formatting and the html.escape() function for safe output.
        The generated HTML uses CSS classes from the existing report for consistent
        styling.
        
        Args:
            data: Processed data previously returned by process_files()
        
        Returns:
            HTML string to be injected into the report
        """
        from html import escape
        
        # Return empty string if no data
        if not data or data.get('total_files', 0) == 0:
            return ''
        
        # Build HTML content using f-strings
        # Start with collapsible section header
        html = '''<h3><a id="toggle_liberty_logs" href="javascript:expand_it(liberty_logs,toggle_liberty_logs)" class="expandit">Liberty System Out</a></h3>
<div id="liberty_logs" style="display:none;">
    <a id="togglelibertydoc" href="javascript:expand_it(libertydoc,togglelibertydoc)" class="expandit">
        What does this section tell me?</a>
    <div id="libertydoc" style="display:none;">
        This section shows analysis of WebSphere Liberty server log files (systemout.log, console.log, messages.log).
        The data includes:
        <ul>
            <li><strong>Summary Statistics</strong>
                - Total number of log files processed and total messages found.
            </li>
            <li><strong>Severity Distribution</strong>
                - Breakdown of messages by severity level (Audit, Warning, Error, Info, Other).
            </li>
            <li><strong>Top Message IDs</strong>
                - Most frequently occurring Liberty message IDs with their counts.
            </li>
            <li><strong>Individual Log Files</strong>
                - Details for each processed log file including message counts and severity distribution.
            </li>
        </ul>
    </div>

    <!-- Summary Statistics -->
    <h4>Summary</h4>
    <table class="tablesorter">
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Log Files</td>
                <td>{total_files}</td>
            </tr>
            <tr>
                <td>Total Messages</td>
                <td>{total_messages}</td>
            </tr>
        </tbody>
    </table>

    <!-- Severity Distribution -->
    <h4>Severity Distribution</h4>
    <table class="tablesorter">
        <thead>
            <tr>
                <th>Severity</th>
                <th>Level</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
'''.format(
            total_files=data.get('total_files', 0),
            total_messages=data.get('total_messages', 0)
        )
        
        # Add severity distribution rows
        severity_names = {'A': 'Audit', 'W': 'Warning', 'E': 'Error', 'I': 'Info', 'O': 'Other'}
        severity_counts = data.get('severity_counts', {})
        
        for severity in ['A', 'W', 'E', 'I', 'O']:
            count = severity_counts.get(severity, 0)
            name = severity_names.get(severity, 'Unknown')
            
            # Add CSS class for errors and warnings
            row_class = ''
            if severity == 'E':
                row_class = ' class="error_row"'
            elif severity == 'W':
                row_class = ' class="warning_row"'
            
            html += f'''            <tr{row_class}>
                <td>{escape(name)}</td>
                <td>{escape(severity)}</td>
                <td>{count}</td>
            </tr>
'''
        
        html += '''        </tbody>
    </table>
'''
        
        # Add top message IDs section if available
        top_message_ids = data.get('top_message_ids', {})
        if top_message_ids:
            html += '''
    <!-- Top Message IDs -->
    <h4>Top Message IDs</h4>
    <table class="tablesorter">
        <thead>
            <tr>
                <th>Message ID</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
'''
            for msg_id, count in top_message_ids.items():
                html += f'''            <tr>
                <td>{escape(msg_id)}</td>
                <td>{count}</td>
            </tr>
'''
            html += '''        </tbody>
    </table>
'''
        
        # Add individual log files section
        html += '''
    <!-- Individual Log Files -->
    <h4>Log Files</h4>
    <table class="tablesorter">
        <thead>
            <tr>
                <th>File Name</th>
                <th>Total Messages</th>
                <th>Audit</th>
                <th>Warning</th>
                <th>Error</th>
                <th>Info</th>
                <th>Other</th>
            </tr>
        </thead>
        <tbody>
'''
        
        # Add rows for each log file
        log_files = data.get('log_files', [])
        for log in log_files:
            file_name = escape(log.get('file', 'Unknown'))
            message_count = log.get('message_count', 0)
            
            # Check if there was an error processing this file
            if 'error' in log:
                error_msg = escape(log['error'])
                html += f'''            <tr class="error_row">
                <td>{file_name}</td>
                <td>{message_count}</td>
                <td colspan="5" class="error_cell">Error: {error_msg}</td>
            </tr>
'''
            else:
                # Get severity counts for this file
                file_severity = log.get('severity_counts', {})
                audit_count = file_severity.get('A', 0)
                warning_count = file_severity.get('W', 0)
                error_count = file_severity.get('E', 0)
                info_count = file_severity.get('I', 0)
                other_count = file_severity.get('O', 0)
                
                html += f'''            <tr>
                <td>{file_name}</td>
                <td>{message_count}</td>
                <td>{audit_count}</td>
                <td>{warning_count}</td>
                <td>{error_count}</td>
                <td>{info_count}</td>
                <td>{other_count}</td>
            </tr>
'''
        
        # Close the tables and divs
        html += '''        </tbody>
    </table>
</div>
'''
        
        return html


# Made with Bob