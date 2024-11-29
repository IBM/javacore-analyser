#
# Copyright IBM Corp. 2024 - 2024
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
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        self.assertEqual(len(parser.get_file_paths()), 3, "Wrong number of files")

    def test_parse_files(self):
        os.chmod("test/data/verboseGc/", 0o555)
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        self.assertEqual(len(parser.get_collects()), 39, "Not all GC collections parsed")
        # testing the time limits
        parser = VerboseGcParser()
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.txt.001")
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
        parser.add_file("test/data/verboseGc/verbosegc.230105.19308.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230413.19984.txt.001")
        parser.add_file("test/data/verboseGc/verbosegc.230420.33424.txt.001")
        start = datetime.strptime('2000-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        stop = datetime.strptime('2100-04-25T11:04:13.857', '%Y-%m-%dT%H:%M:%S.%f')
        parser.parse_files(start, stop)
        element = parser.get_xml(self.doc)
        self.assertEqual(len(element.getElementsByTagName(GC_COLLECTION)), 39, "Wrong number of GC collects in XML")
