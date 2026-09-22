#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
DevTools Console Log Plugin for javacore-analyser.

This plugin processes console log exports produced by the Web Developer Tools
in Firefox and Chrome browsers.

Firefox: open DevTools → Console → right-click → "Save All Messages to File"
Chrome:  open DevTools → Console → right-click → "Save as…"

The exported file is a plain-text file where every logical message occupies one
or more consecutive lines.  The last line of each message optionally ends with a
source location token in one of these forms:

    <filename>:<line>:<col>         – e.g.  _js:2134:1
    <url or domain>                 – e.g.  fyre.ibm.com
    <count> <filename>:<line>:<col> – e.g.  2 <anonymous code>:6161:7

Lines that carry no such trailing token are treated as continuation lines
belonging to the previous message.

This file serves as a reference / example plugin implementation and can also be
installed as a working plugin by copying the ``docs/devtools_console_plugin/``
directory into ``~/.javacore_analyser/plugins/``.
"""

from __future__ import annotations

import logging
import os
import re
from html import escape
from typing import Any, Dict, List
from xml.dom.minidom import Document, Element

from javacore_analyser.plugin_interface import DataSourcePlugin

# Regex for Case A: trailing  [count ]<token_no_spaces>
#   e.g.  "_js:2134:1"  or  "2 _js:2134:1"  or  "fyre.ibm.com"
_LOCATION_NOSPACE_RE = re.compile(
    r"""
    \s                           # whitespace before the token
    (?:(\d+)\s+)?                # group 1: optional repeat count
    (\S+)                        # group 2: source token (no spaces)
    $                            # at end of line
    """,
    re.VERBOSE,
)

# Regex for Case B: trailing  [count ]<token_with_angle_brackets> e.g.:
#   "<anonymous code>:6161:7"  or  "2 <anonymous code>:6161:7"
_LOCATION_ANON_RE = re.compile(
    r"""
    \s                           # whitespace before the token
    (?:(\d+)\s+)?                # group 1: optional repeat count
    (<[^>]+>[^<\s]*)             # group 2: <tag> followed by optional :line:col
    $                            # at end of line
    """,
    re.VERBOSE,
)

# A source token is considered a *location* when it fully matches either:
#   A) ends with  :digits  (or  :digits:digits)  – file with line/col
#   B) looks like a hostname/domain (possibly multi-label, e.g. fyre.ibm.com)
_IS_LOCATION_RE = re.compile(
    r"""
    \A                           # match full string from start
    (?:
        .*:\d+(?::\d+)?          # option A: ends with :digits or :digits:digits
        |
        [A-Za-z0-9][A-Za-z0-9\-]*  # option B: hostname label
        (?:\.[A-Za-z0-9][A-Za-z0-9\-]*)*  # optional further labels
        \.[A-Za-z]{2,}           # TLD (letters only, >=2 chars)
    )
    \Z                           # match full string to end
    """,
    re.VERBOSE,
)


def _parse_console_log(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse a DevTools console export file into a list of message dictionaries.

    Each dictionary has the keys:

    ``text``
        The full message text (may be multi-line, joined with newlines).
    ``source``
        Source location string, or empty string when absent.
    ``count``
        Repeat count extracted from the location token (default 1).
    """
    messages: List[Dict[str, Any]] = []
    current_lines: List[str] = []

    def _flush():
        if not current_lines:
            return
        raw = "\n".join(current_lines).strip()
        if not raw:
            return

        # Try to peel off a trailing location token from the *last* line.
        # We check for angle-bracket tokens (e.g. "<anonymous code>:6161:7")
        # first, then fall back to plain no-space tokens (e.g. "_js:2134:1"
        # or "fyre.ibm.com").
        last = current_lines[-1]
        last_stripped = last.rstrip()
        count = 1
        source = ""
        token_start = None

        for pattern in (_LOCATION_ANON_RE, _LOCATION_NOSPACE_RE):
            m = pattern.search(last_stripped)
            if m and _IS_LOCATION_RE.match(m.group(2)):
                source = m.group(2)
                if m.group(1):
                    count = int(m.group(1))
                # +1 to skip the leading whitespace captured by the pattern.
                token_start = m.start() + 1
                break

        if token_start is not None:
            # Reconstruct text without the trailing location/count token.
            trimmed_last = last[:token_start].rstrip()
            if len(current_lines) == 1:
                text = trimmed_last
            else:
                text = "\n".join(current_lines[:-1]) + (("\n" + trimmed_last) if trimmed_last else "")
        else:
            text = raw

        text = text.strip()
        if text:
            messages.append({"text": text, "source": source, "count": count})

    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n").rstrip("\r")
            # A blank line separates logical messages in some exports.
            if line.strip() == "":
                _flush()
                current_lines = []
            else:
                # Heuristic: if the line begins with whitespace it is a
                # continuation of the previous message (e.g. stack frames).
                if current_lines and (line.startswith(" ") or line.startswith("\t")):
                    current_lines.append(line)
                else:
                    # New message starts; flush the previous one first.
                    _flush()
                    current_lines = [line]

    _flush()
    return messages


class DevToolsConsolePlugin(DataSourcePlugin):
    """
    Plugin to process Web Developer Tools console log exports.

    Supports files exported from:

    * **Firefox** – DevTools → Console → right-click → *Save All Messages to File*
    * **Chrome**  – DevTools → Console → right-click → *Save as…*

    The plugin identifies candidate files by the ``console-export-*.log`` name
    pattern and validates them by looking for typical DevTools console content.
    """

    # ------------------------------------------------------------------ #
    # Identity                                                             #
    # ------------------------------------------------------------------ #

    def get_plugin_name(self) -> str:
        return "devtools_console"

    def get_display_name(self) -> str:
        return "DevTools Console Log"

    def get_description(self) -> str:
        return (
            "This section shows console log messages exported from the Web Developer "
            "Tools in Firefox or Chrome browsers.<br>"
            "To export: open DevTools → Console → right-click → <em>Save All Messages "
            "to File</em> (Firefox) or <em>Save as…</em> (Chrome).<br><br>"
            "The data includes:<ul>"
            "<li><strong>Summary Statistics</strong> – total files, total messages, "
            "and how many were deduplicated by the browser (repeat count &gt; 1).</li>"
            "<li><strong>Messages</strong> – full message text, source location, and "
            "repeat count for every entry.</li>"
            "</ul>"
        )

    # ------------------------------------------------------------------ #
    # File discovery and validation                                        #
    # ------------------------------------------------------------------ #

    def get_file_patterns(self) -> List[str]:
        return ["console-export-*.log", "console*.log", "*console-export*.log"]

    def can_process(self, filepath: str) -> bool:
        """
        Validate whether the file looks like a DevTools console export.

        Checks file existence, a minimum size of 10 bytes, and that the
        content is plain text (no null bytes in the first 8 KB).
        """
        try:
            if not os.path.exists(filepath):
                return False
            size = os.path.getsize(filepath)
            if size < 10:
                return False
            # Check that the file is plain text (no null bytes).
            with open(filepath, "rb") as fh:
                sample = fh.read(8192)
            return b"\x00" not in sample
        except Exception as exc:
            logging.warning(f"DevToolsConsolePlugin: error validating {filepath}: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # Processing                                                           #
    # ------------------------------------------------------------------ #

    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Parse all matching console log files.

        Returns a dictionary with:

        ``log_files``
            List of per-file result dictionaries (``file``, ``messages``,
            ``message_count``).
        ``total_files``
            Number of files processed.
        ``total_messages``
            Summed message count across all files.
        ``total_repeated``
            Number of messages that were repeated more than once.
        """
        logging.info(f"DevToolsConsolePlugin: processing {len(filepaths)} file(s)")
        log_files = []
        total_messages = 0
        total_repeated = 0

        for filepath in filepaths:
            try:
                messages = _parse_console_log(filepath)
                repeated = sum(1 for m in messages if m["count"] > 1)
                log_files.append(
                    {
                        "file": os.path.basename(filepath),
                        "messages": messages,
                        "message_count": len(messages),
                    }
                )
                total_messages += len(messages)
                total_repeated += repeated
                logging.info(
                    f"DevToolsConsolePlugin: {filepath} → {len(messages)} messages "
                    f"({repeated} repeated)"
                )
            except Exception as exc:
                logging.error(f"DevToolsConsolePlugin: error processing {filepath}: {exc}")
                log_files.append(
                    {
                        "file": os.path.basename(filepath),
                        "messages": [],
                        "message_count": 0,
                        "error": str(exc),
                    }
                )

        return {
            "log_files": log_files,
            "total_files": len(filepaths),
            "total_messages": total_messages,
            "total_repeated": total_repeated,
        }

    # ------------------------------------------------------------------ #
    # XML generation                                                       #
    # ------------------------------------------------------------------ #

    def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Element:
        root = doc.createElement("devtools_console")
        root.setAttribute("total_files", str(data["total_files"]))
        root.setAttribute("total_messages", str(data["total_messages"]))
        root.setAttribute("total_repeated", str(data["total_repeated"]))

        for log in data.get("log_files", []):
            log_node = doc.createElement("log_file")
            log_node.setAttribute("file", log["file"])
            log_node.setAttribute("message_count", str(log["message_count"]))
            if "error" in log:
                log_node.setAttribute("error", log["error"])
            else:
                for msg in log.get("messages", []):
                    msg_node = doc.createElement("message")
                    msg_node.setAttribute("source", msg["source"])
                    msg_node.setAttribute("count", str(msg["count"]))
                    msg_node.appendChild(doc.createTextNode(msg["text"]))
                    log_node.appendChild(msg_node)
            root.appendChild(log_node)

        return root

    # ------------------------------------------------------------------ #
    # HTML generation                                                      #
    # ------------------------------------------------------------------ #

    def generate_html(self, data: Dict[str, Any]) -> str:
        if not data or data.get("total_files", 0) == 0:
            return ""

        html_parts: List[str] = []

        # Summary table
        html_parts.append(
            """    <h4>Summary</h4>
    <table class="tablesorter">
        <thead>
            <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
            <tr><td>Total Log Files</td><td>{total_files}</td></tr>
            <tr><td>Total Messages</td><td>{total_messages}</td></tr>
            <tr><td>Repeated Messages</td><td>{total_repeated}</td></tr>
        </tbody>
    </table>
""".format(
                total_files=data["total_files"],
                total_messages=data["total_messages"],
                total_repeated=data["total_repeated"],
            )
        )

        # Per-file message tables
        for log in data.get("log_files", []):
            file_name = escape(log["file"])
            html_parts.append(f"    <h4>File: {file_name}</h4>\n")

            if "error" in log:
                html_parts.append(
                    f'    <p class="error_row">Error processing file: {escape(log["error"])}</p>\n'
                )
                continue

            if not log["messages"]:
                html_parts.append("    <p>No messages found.</p>\n")
                continue

            html_parts.append(
                """    <table class="tablesorter">
        <thead>
            <tr>
                <th>Message</th>
                <th>Source</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
"""
            )
            for msg in log["messages"]:
                msg_text = escape(msg["text"])
                # Preserve newlines within a message as <br> so stack traces
                # remain readable inside the table cell.
                msg_text = msg_text.replace("\n", "<br>")
                source = escape(msg["source"]) if msg["source"] else ""
                count = msg["count"]
                html_parts.append(
                    f"            <tr>\n"
                    f"                <td>{msg_text}</td>\n"
                    f"                <td>{source}</td>\n"
                    f"                <td>{count}</td>\n"
                    f"            </tr>\n"
                )
            html_parts.append("        </tbody>\n    </table>\n")

        return "".join(html_parts)

    # ------------------------------------------------------------------ #
    # Optional: summary metrics                                            #
    # ------------------------------------------------------------------ #

    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "Total Log Files": data.get("total_files", 0),
            "Total Messages": data.get("total_messages", 0),
            "Repeated Messages": data.get("total_repeated", 0),
        }


# Made with Bob
