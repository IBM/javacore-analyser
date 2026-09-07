#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest
from datetime import datetime
from xml.dom.minidom import parseString

from javacore_analyser.verbose_gc import VerboseGcParser, GC_COLLECTIONS, GC_COLLECTION


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
