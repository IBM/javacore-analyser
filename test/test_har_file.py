#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#
import unittest

from javacore_analyser.har_file import HarFile
from xml.dom.minidom import Element, parseString


class TestHarFile(unittest.TestCase):

    def setUp(self):
        self.path = "test/data/javacores/jazz.net_Archive [25-01-03 11-07-56].har"
        self.doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                        <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')
        self.har_file = HarFile(self.path)

    def test_har_path(self):
        self.assertEqual(self.har_file.path, self.path, "Invalid HAR path")

    def test_get_xml(self):
        element = self.har_file.get_xml(self.doc)
        self.assertTrue(element, "HAR file XML is None")
        self.assertEqual(element.__class__, Element, "Wrong DOM object returned")
        self.assertEqual(element.tagName, "har_file", "Wrong root element name")
        self.assertEqual(len(element.childNodes), 55, "Incorrect number of HTTP calls")
        http_call_node = element.childNodes[0]
        self.assertEqual(http_call_node.tagName, "http_call", "Invalid XML structure")
        self.assertEqual(http_call_node.attributes["url"].nodeValue, "https://jazz.net/jazz/service/"
                                                                     "com.ibm.team.dashboard.viewlets.service.internal"
                                                                     ".members.IMemberPhotoService"
                                                                     "?userId=PAniola&defaultIcon=banner")
        self.assertEqual(http_call_node.attributes["status"].nodeValue, "400")
        self.assertEqual(http_call_node.attributes["size"].nodeValue, "1234")
        self.assertEqual(http_call_node.attributes["success"].nodeValue, 'False')
        self.assertEqual(http_call_node.attributes["duration"].nodeValue, "900")



