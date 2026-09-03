#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest

from javacore_analyser.jvm_info import JvmInfo
from javacore_analyser.javacore_set import JavacoreSet


class TestJvmInfo(unittest.TestCase):

    def setUp(self):
        self.verbose_gc_file = os.path.join("test", "data", "verboseGc", "verbosegc.230105.19308.log")
        self.verbose_gc_dir = os.path.join("test", "data", "verboseGc")

    def test_parse_verbose_gc(self):
        jvm_info = JvmInfo()
        jvm_info.parse_verbose_gc(self.verbose_gc_file)

        # Verify parsed properties
        self.assertEqual(jvm_info.number_of_cpus, "16")
        self.assertEqual(jvm_info.xmx, "4G")
        self.assertEqual(jvm_info.xms, "4G")
        self.assertEqual(jvm_info.xmn, "1G")
        self.assertEqual(jvm_info.gc_policy, "gencon")
        self.assertTrue(jvm_info.compressed_refs)
        self.assertTrue(jvm_info.verbose_gc)
        self.assertEqual(jvm_info.os_level, "Windows 10 10.0")
        self.assertEqual(jvm_info.architecture, "amd64")
        self.assertEqual(jvm_info.jvm_start_time, "2023/01/05 at 13:56:13:727")
        self.assertGreater(len(jvm_info.user_args), 0)
        self.assertIn("-Xmx4G", jvm_info.user_args)
        self.assertIn("-Xms4G", jvm_info.user_args)
        self.assertIn("-Xmn1G", jvm_info.user_args)
        self.assertIn("-Xgcpolicy:gencon", jvm_info.user_args)
        self.assertTrue(jvm_info.cmd_line.startswith("java"))

    def test_javacore_set_with_only_verbose_gc(self):
        # Create a JavacoreSet on a directory containing ONLY verbose GC and no javacores
        jset = JavacoreSet.create(self.verbose_gc_dir)

        # Assert that javacores list is indeed empty
        self.assertEqual(len(jset.javacores), 0)

        # Assert that jvm_info is correctly populated from the verbosegc log
        self.assertIsNotNone(jset.jvm_info)
        jvm_info = jset.jvm_info
        self.assertEqual(jvm_info.number_of_cpus, "16")
        self.assertEqual(jvm_info.xmx, "4G")
        self.assertEqual(jvm_info.xms, "4G")
        self.assertEqual(jvm_info.xmn, "1G")
        self.assertEqual(jvm_info.gc_policy, "gencon")
        self.assertTrue(jvm_info.compressed_refs)
        self.assertTrue(jvm_info.verbose_gc)
        self.assertEqual(jvm_info.os_level, "Windows 10 10.0")
        self.assertEqual(jvm_info.architecture, "amd64")
        self.assertEqual(jvm_info.jvm_start_time, "2023/01/05 at 13:56:13:727")

    def test_javacore_set_report_xml_has_system_info_with_only_verbose_gc(self):
        import tempfile
        from xml.dom.minidom import parse
        with tempfile.TemporaryDirectory() as tmp_dir:
            jset = JavacoreSet.create(self.verbose_gc_dir)
            report_path = os.path.join(tmp_dir, "report.xml")
            jset._JavacoreSet__create_report_xml(report_path)

            # Read and parse report.xml from disk
            doc = parse(report_path)

            # Verify that the generated XML doc contains system_info
            system_info_nodes = doc.getElementsByTagName("system_info")
            self.assertEqual(len(system_info_nodes), 1)

            # Verify details inside system_info
            jvm_info_nodes = system_info_nodes[0].getElementsByTagName("jvm_info")
            self.assertEqual(len(jvm_info_nodes), 1)

            # Verify property values inside jvm_info
            xmx_node = jvm_info_nodes[0].getElementsByTagName("xmx")[0]
            self.assertEqual(xmx_node.firstChild.nodeValue, "4G")
