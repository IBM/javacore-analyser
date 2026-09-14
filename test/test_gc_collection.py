#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import unittest
from xml.dom.minidom import Element, parseString

from javacore_analyser.verbose_gc import GcCollection, DURATION, COMP_RATIO


class TestGcCollection(unittest.TestCase):

    def setUp(self):
        self.gc_collection = GcCollection()
        self.doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')

    def test_freed(self):
        self.assertEqual(self.gc_collection.freed(), 0)
        self.gc_collection.free_after = 100
        self.assertEqual(self.gc_collection.freed(), 100)
        self.gc_collection.free_before = 50
        self.assertEqual(self.gc_collection.freed(), 50)

    def test_get_start_time(self):
        self.gc_collection.start_time_str = "2023-04-25T11:04:13.857"
        self.assertIsNotNone(self.gc_collection.get_start_time(), "Start time is none")
        self.assertEqual(self.gc_collection.get_start_time().day, 25, "Wrong day parsed")

    def test_comp_ratio_zero_when_no_heap(self):
        self.assertEqual(self.gc_collection.comp_ratio(), 0.0)

    def test_comp_ratio_calculated_correctly(self):
        self.gc_collection.nursery_total = "200"
        self.gc_collection.tenure_total = "800"
        self.gc_collection.free_before = "0"   # heap_used_before = 200 + 800 - 0 = 1000
        self.gc_collection.free_after = "500"  # freed = 500 - 0 = 500
        # comp_ratio = 500 / 1000 * 100 = 50.0
        self.assertAlmostEqual(self.gc_collection.comp_ratio(), 50.0)

    def test_comp_ratio_with_partial_free_before(self):
        self.gc_collection.nursery_total = "400"
        self.gc_collection.tenure_total = "600"
        self.gc_collection.free_before = "200"  # heap_used_before = 400 + 600 - 200 = 800
        self.gc_collection.free_after = "400"   # freed = 400 - 200 = 200
        # comp_ratio = 200 / 800 * 100 = 25.0
        self.assertAlmostEqual(self.gc_collection.comp_ratio(), 25.0)

    def test_get_xml(self):
        self.gc_collection.duration = 100
        element = self.gc_collection.get_xml(self.doc)
        self.assertEqual(element.__class__, Element, "Wrong DOM object returned")
        self.assertTrue(element.hasAttributes(), "No attributes")
        self.assertTrue(element.hasAttribute(DURATION), "Missing " + DURATION + " attribute")
        duration = element.getAttribute(DURATION)
        self.assertEqual(duration, "100", "Wrong " + DURATION + " value")
        self.assertTrue(element.hasAttribute(COMP_RATIO), "Missing " + COMP_RATIO + " attribute")


