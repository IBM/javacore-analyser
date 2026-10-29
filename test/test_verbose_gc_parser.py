#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest
from datetime import datetime
from xml.dom.minidom import parseString

from javacore_analyser.verbose_gc import (VerboseGcParser, GC_COLLECTIONS, GC_COLLECTION,
                                           GC_OVERHEAD_PERCENT, CUMULATIVE_GC_OVERHEAD_PERCENT)


class TestVerboseGcParser(unittest.TestCase):

    def setUp(self):
        self.doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                                       <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')

    def test_add_file(self):
        os.chmod("test/data/verboseGc/", 0o555)
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        self.assertEqual(len(parser.get_file_paths()), 3, "Wrong number of files")

    def test_parse_files(self):
        os.chmod("test/data/verboseGc/", 0o555)
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        self.assertEqual(len(parser.get_collects()), 39, "Not all GC collections parsed")
        # testing the time limits
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2023-04-25T11:04:18.149', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2023-04-25T11:04:18.149', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        self.assertEqual(len(parser.get_collects()), 1, "Time limit failure")
        self.assertEqual(parser.get_files()[0].get_number_of_collects(), 0)
        self.assertEqual(parser.get_files()[1].get_number_of_collects(), 0)
        self.assertEqual(parser.get_files()[2].get_number_of_collects(), 1)

    def test_get_xml(self):
        parser = VerboseGcParser()
        element = parser.get_xml(self.doc)
        self.assertEqual(element.tagName, GC_COLLECTIONS, "Wrong XML element name")
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        element = parser.get_xml(self.doc)
        self.assertEqual(len(element.getElementsByTagName(GC_COLLECTION)), 39, "Wrong number of GC collects in XML")

    def test_collects_sorted_by_time_when_files_added_out_of_order(self):
        """Collections from multiple files must be sorted chronologically (Fixes #366)."""
        parser = VerboseGcParser()
        # Add files in reverse chronological order to trigger the sorting bug
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        start = datetime.strptime('2000-01-01T00:00:00.000', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-01-01T00:00:00.000', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        collects = parser.get_collects()
        self.assertGreater(len(collects), 0, "No collections parsed")
        times = [c.get_start_time() for c in collects]
        self.assertEqual(times, sorted(times), "GC collections are not sorted by start time")

    def test_gc_overhead_percent_no_collects(self):
        """Returns 0.0 when no collections are available."""
        parser = VerboseGcParser()
        self.assertEqual(0.0, parser.gc_overhead_percent())

    def test_gc_overhead_percent_single_collect(self):
        """With a single collection elapsed == duration, so overhead == 100%."""
        from javacore_analyser.verbose_gc import GcCollection
        parser = VerboseGcParser()
        collect = GcCollection()
        collect.start_time_str = "2023-04-25T11:04:13.857"
        collect.duration = 500.0
        parser._VerboseGcParser__collects = [collect]
        self.assertAlmostEqual(100.0, parser.gc_overhead_percent())

    def test_gc_overhead_percent_with_real_files(self):
        """Overhead is a non-negative float in [0, 100] when real files are parsed."""
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        overhead = parser.gc_overhead_percent()
        self.assertGreaterEqual(overhead, 0.0)
        self.assertLessEqual(overhead, 100.0)

    def test_get_xml_contains_gc_overhead_attribute(self):
        """The gc-collections XML element must carry a gc-overhead-percent attribute."""
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                               <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')
        element = parser.get_xml(doc)
        self.assertTrue(element.hasAttribute(GC_OVERHEAD_PERCENT),
                        "gc-collections element must have gc-overhead-percent attribute")
        overhead_str = element.getAttribute(GC_OVERHEAD_PERCENT)
        overhead = float(overhead_str)
        self.assertGreaterEqual(overhead, 0.0)
        self.assertLessEqual(overhead, 100.0)

    def test_get_xml_cumulative_gc_overhead_per_collection(self):
        """Every gc-collection child element must carry a cumulative-gc-overhead-percent attribute
        whose value is a non-negative float in [0, 100] and is non-decreasing across collections."""
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.log")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                               <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')
        element = parser.get_xml(doc)
        children = element.getElementsByTagName(GC_COLLECTION)
        self.assertGreater(len(children), 0, "Need at least one gc-collection")
        for child in children:
            self.assertTrue(child.hasAttribute(CUMULATIVE_GC_OVERHEAD_PERCENT),
                            "gc-collection must have cumulative-gc-overhead-percent attribute")
            value = float(child.getAttribute(CUMULATIVE_GC_OVERHEAD_PERCENT))
            self.assertGreaterEqual(value, 0.0, "Cumulative overhead must be non-negative")
            self.assertLessEqual(value, 100.0, "Cumulative overhead must not exceed 100%")

