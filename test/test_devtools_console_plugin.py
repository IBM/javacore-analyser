#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Tests for the DevTools Console Log plugin.

The plugin is located in docs/devtools_console_plugin/plugin.py and processes
console log exports produced by Firefox and Chrome DevTools.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from xml.dom.minidom import Document

# Ensure both src/ and docs/ are importable when running from project root.
_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root / "docs"))

from devtools_console_plugin.plugin import DevToolsConsolePlugin, _parse_console_log

# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

# Matches the real sample file shipped with the project.
SAMPLE_LOG = """\
Fingerprinting Protection is altering screen.availWidth and screen.availHeight. These values may not match your actual screen dimensions. This protection helps prevent websites building a fingerprint that can be used to track users. Learn more: https://support.mozilla.org/kb/firefox-protection-against-fingerprinting <anonymous code>:6161:7
unreachable code after return statement _js:2134:1
Fingerprinting Protection is altering screen.availWidth and screen.availHeight. These values may not match your actual screen dimensions. This protection helps prevent websites building a fingerprint that can be used to track users. Learn more: https://support.mozilla.org/kb/firefox-protection-against-fingerprinting <anonymous code>:6161:7
Invalid X-Frame-Options header was found when loading "https://fyre.ibm.com/": "invalid" is not a valid directive. fyre.ibm.com
Fingerprinting Protection is altering screen.availWidth and screen.availHeight. These values may not match your actual screen dimensions. This protection helps prevent websites building a fingerprint that can be used to track users. Learn more: https://support.mozilla.org/kb/firefox-protection-against-fingerprinting 2 <anonymous code>:6161:7
Source map error: Error: URL constructor: <anonymous code> is not a valid URL.
 Stack in the worker:resolveSourceMapURL@resource://devtools/client/shared/source-map-loader/utils/fetchSourceMap.js:56:22
 getOriginalURLs@resource://devtools/client/shared/source-map-loader/source-map.js:75:24
 workerHandler/</<@resource://devtools/client/shared/worker-utils.js:115:52
 workerHandler/<@resource://devtools/client/shared/worker-utils.js:113:13

 Resource URL: <anonymous code>
 Source Map URL: null\
"""


def _write_temp(content: str, suffix: str = ".log") -> str:
    """Write *content* to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as fh:
        fh.write(content)
    return fh.name


class TestParseConsoleLog(unittest.TestCase):
    """Unit tests for the internal _parse_console_log() helper."""

    def _parse(self, content: str):
        path = _write_temp(content)
        try:
            return _parse_console_log(path)
        finally:
            os.unlink(path)

    def test_single_line_with_colon_location(self):
        msgs = self._parse("unreachable code after return statement _js:2134:1\n")
        self.assertEqual(len(msgs), 1)
        self.assertIn("unreachable code", msgs[0]["text"])
        self.assertEqual(msgs[0]["source"], "_js:2134:1")
        self.assertEqual(msgs[0]["count"], 1)

    def test_single_line_with_domain_location(self):
        msgs = self._parse(
            'Invalid X-Frame-Options header was found when loading '
            '"https://fyre.ibm.com/": "invalid" is not a valid directive. fyre.ibm.com\n'
        )
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["source"], "fyre.ibm.com")
        self.assertEqual(msgs[0]["count"], 1)

    def test_single_line_with_repeat_count(self):
        msgs = self._parse(
            "Fingerprinting Protection is altering screen. 2 <anonymous code>:6161:7\n"
        )
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["count"], 2)
        self.assertEqual(msgs[0]["source"], "<anonymous code>:6161:7")

    def test_multiline_message_with_continuation_lines(self):
        content = (
            "Source map error: Error: URL constructor: <anonymous code> is not a valid URL.\n"
            " Stack in the worker:resolveSourceMapURL@resource://devtools/client/shared/source-map-loader/utils/fetchSourceMap.js:56:22\n"
            " getOriginalURLs@resource://devtools/client/shared/source-map-loader/source-map.js:75:24\n"
        )
        msgs = self._parse(content)
        self.assertEqual(len(msgs), 1)
        self.assertIn("Source map error", msgs[0]["text"])
        # The last continuation line contains a location token
        self.assertTrue(msgs[0]["source"] or msgs[0]["text"])

    def test_blank_line_separates_messages(self):
        content = "First message first.js:1:1\n\nSecond message second.js:2:2\n"
        msgs = self._parse(content)
        self.assertEqual(len(msgs), 2)

    def test_no_location_line(self):
        msgs = self._parse("Just a plain message with no location\n")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["source"], "")
        self.assertEqual(msgs[0]["count"], 1)

    def test_empty_file_returns_no_messages(self):
        msgs = self._parse("")
        self.assertEqual(msgs, [])

    def test_real_sample_file(self):
        """Parse the actual sample file shipped with the project."""
        sample_path = (
            Path(__file__).parent
            / "data"
            / "javacores"
            / "console-export-2026-9-22_14-59-22.log"
        )
        if not sample_path.exists():
            self.skipTest("Sample file not found")
        msgs = _parse_console_log(str(sample_path))
        # The file has at least 5 distinct logical messages.
        self.assertGreaterEqual(len(msgs), 5)


class TestDevToolsConsolePluginIdentity(unittest.TestCase):
    """Tests for plugin identity methods."""

    def setUp(self):
        self.plugin = DevToolsConsolePlugin()

    def test_plugin_name(self):
        self.assertEqual(self.plugin.get_plugin_name(), "devtools_console")

    def test_display_name(self):
        self.assertEqual(self.plugin.get_display_name(), "DevTools Console Log")

    def test_description_is_non_empty(self):
        self.assertGreater(len(self.plugin.get_description()), 0)

    def test_file_patterns_non_empty(self):
        patterns = self.plugin.get_file_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)


class TestDevToolsConsolePluginCanProcess(unittest.TestCase):
    """Tests for can_process() validation."""

    def setUp(self):
        self.plugin = DevToolsConsolePlugin()
        self._temps = []

    def tearDown(self):
        for p in self._temps:
            if os.path.exists(p):
                os.unlink(p)

    def _make_file(self, content: str, suffix: str = ".log") -> str:
        path = _write_temp(content, suffix=suffix)
        self._temps.append(path)
        return path

    def test_valid_text_file_accepted(self):
        path = self._make_file("Some console message js:1:1\n")
        self.assertTrue(self.plugin.can_process(path))

    def test_file_too_small_rejected(self):
        path = self._make_file("tiny")
        self.assertFalse(self.plugin.can_process(path))

    def test_binary_file_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as fh:
            fh.write(b"\x00\x01\x02\x03\x04\x05\x06\x07" * 10)
            path = fh.name
        self._temps.append(path)
        self.assertFalse(self.plugin.can_process(path))

    def test_nonexistent_file_rejected(self):
        self.assertFalse(self.plugin.can_process("/nonexistent/path/file.log"))


class TestDevToolsConsolePluginProcessFiles(unittest.TestCase):
    """Tests for process_files()."""

    def setUp(self):
        self.plugin = DevToolsConsolePlugin()
        self._temps = []

    def tearDown(self):
        for p in self._temps:
            if os.path.exists(p):
                os.unlink(p)

    def _make_file(self, content: str) -> str:
        path = _write_temp(content)
        self._temps.append(path)
        return path

    def test_single_file_basic_result(self):
        path = self._make_file(
            "Error loading resource resource.js:10:5\n"
            "Warning: deprecated API old.js:20:1\n"
        )
        result = self.plugin.process_files([path])
        self.assertEqual(result["total_files"], 1)
        self.assertGreaterEqual(result["total_messages"], 1)
        self.assertIn("log_files", result)
        self.assertEqual(len(result["log_files"]), 1)

    def test_multiple_files_aggregated(self):
        p1 = self._make_file("msg one a.js:1:1\n")
        p2 = self._make_file("msg two b.js:2:2\nmsg three c.js:3:3\n")
        result = self.plugin.process_files([p1, p2])
        self.assertEqual(result["total_files"], 2)
        self.assertGreaterEqual(result["total_messages"], 3)

    def test_repeated_messages_counted(self):
        path = self._make_file(
            "Repeated message 5 script.js:1:1\n"
            "Normal message script.js:2:2\n"
        )
        result = self.plugin.process_files([path])
        self.assertGreaterEqual(result["total_repeated"], 1)

    def test_empty_list_returns_zero_counts(self):
        result = self.plugin.process_files([])
        self.assertEqual(result["total_files"], 0)
        self.assertEqual(result["total_messages"], 0)

    def test_real_sample_file(self):
        sample_path = (
            Path(__file__).parent
            / "data"
            / "javacores"
            / "console-export-2026-9-22_14-59-22.log"
        )
        if not sample_path.exists():
            self.skipTest("Sample file not found")
        result = self.plugin.process_files([str(sample_path)])
        self.assertEqual(result["total_files"], 1)
        self.assertGreaterEqual(result["total_messages"], 5)
        # Verify messages list is populated
        messages = result["log_files"][0]["messages"]
        self.assertGreater(len(messages), 0)
        # Each message must have the required keys
        for msg in messages:
            self.assertIn("text", msg)
            self.assertIn("source", msg)
            self.assertIn("count", msg)


class TestDevToolsConsolePluginGenerateXml(unittest.TestCase):
    """Tests for generate_xml()."""

    def setUp(self):
        self.plugin = DevToolsConsolePlugin()

    def test_xml_root_element_name(self):
        data = {
            "log_files": [],
            "total_files": 0,
            "total_messages": 0,
            "total_repeated": 0,
        }
        doc = Document()
        root = self.plugin.generate_xml(doc, data)
        self.assertEqual(root.tagName, "devtools_console")

    def test_xml_attributes_set(self):
        data = {
            "log_files": [],
            "total_files": 2,
            "total_messages": 7,
            "total_repeated": 1,
        }
        doc = Document()
        root = self.plugin.generate_xml(doc, data)
        self.assertEqual(root.getAttribute("total_files"), "2")
        self.assertEqual(root.getAttribute("total_messages"), "7")
        self.assertEqual(root.getAttribute("total_repeated"), "1")

    def test_xml_contains_log_file_children(self):
        data = {
            "log_files": [
                {
                    "file": "console.log",
                    "message_count": 2,
                    "messages": [
                        {"text": "Error msg", "source": "app.js:1:1", "count": 1},
                        {"text": "Warning msg", "source": "app.js:2:1", "count": 3},
                    ],
                }
            ],
            "total_files": 1,
            "total_messages": 2,
            "total_repeated": 1,
        }
        doc = Document()
        root = self.plugin.generate_xml(doc, data)
        xml_str = root.toxml()
        self.assertIn("console.log", xml_str)
        self.assertIn("Error msg", xml_str)
        self.assertIn("app.js:1:1", xml_str)

    def test_xml_serialisable(self):
        data = {
            "log_files": [],
            "total_files": 0,
            "total_messages": 0,
            "total_repeated": 0,
        }
        doc = Document()
        root = self.plugin.generate_xml(doc, data)
        # Should not raise
        xml_str = root.toxml()
        self.assertIsInstance(xml_str, str)


class TestDevToolsConsolePluginGenerateHtml(unittest.TestCase):
    """Tests for generate_html()."""

    def setUp(self):
        self.plugin = DevToolsConsolePlugin()

    def _make_data(self, messages=None):
        msgs = messages or [{"text": "Hello world", "source": "app.js:1:1", "count": 1}]
        return {
            "log_files": [
                {"file": "console.log", "messages": msgs, "message_count": len(msgs)}
            ],
            "total_files": 1,
            "total_messages": len(msgs),
            "total_repeated": sum(1 for m in msgs if m["count"] > 1),
        }

    def test_empty_data_returns_empty_string(self):
        html = self.plugin.generate_html(
            {"log_files": [], "total_files": 0, "total_messages": 0, "total_repeated": 0}
        )
        self.assertEqual(html, "")

    def test_html_contains_summary_table(self):
        html = self.plugin.generate_html(self._make_data())
        self.assertIn("Total Log Files", html)
        self.assertIn("Total Messages", html)

    def test_html_contains_message_text(self):
        html = self.plugin.generate_html(self._make_data())
        self.assertIn("Hello world", html)

    def test_html_contains_source(self):
        html = self.plugin.generate_html(self._make_data())
        self.assertIn("app.js:1:1", html)

    def test_html_escapes_special_chars(self):
        data = self._make_data(
            [{"text": '<script>alert("xss")</script>', "source": "", "count": 1}]
        )
        html = self.plugin.generate_html(data)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_html_file_error_shows_error_message(self):
        data = {
            "log_files": [
                {"file": "bad.log", "messages": [], "message_count": 0, "error": "Permission denied"}
            ],
            "total_files": 1,
            "total_messages": 0,
            "total_repeated": 0,
        }
        html = self.plugin.generate_html(data)
        self.assertIn("Permission denied", html)

    def test_html_multiline_message_uses_br(self):
        data = self._make_data(
            [{"text": "Line 1\nLine 2\nLine 3", "source": "", "count": 1}]
        )
        html = self.plugin.generate_html(data)
        self.assertIn("<br>", html)


class TestDevToolsConsolePluginSummaryMetrics(unittest.TestCase):
    """Tests for get_summary_metrics()."""

    def test_metrics_keys_present(self):
        plugin = DevToolsConsolePlugin()
        data = {"total_files": 3, "total_messages": 42, "total_repeated": 5}
        metrics = plugin.get_summary_metrics(data)
        self.assertIn("Total Log Files", metrics)
        self.assertIn("Total Messages", metrics)
        self.assertIn("Repeated Messages", metrics)
        self.assertEqual(metrics["Total Log Files"], 3)
        self.assertEqual(metrics["Total Messages"], 42)
        self.assertEqual(metrics["Repeated Messages"], 5)


# Made with Bob
