#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest

from javacore_analyser.constants import UNKNOWN
from javacore_analyser.javacore_set import JavacoreSet


class TestJavacoreSet(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        javacores_path = os.getcwd() + os.sep + 'test' + os.sep + 'data' + os.sep + 'javacores'
        self.javacore_set_from_test_data = JavacoreSet(javacores_path)
        self.javacore_set_from_test_data = self.javacore_set_from_test_data.create(javacores_path)
        self.javacore_set_from_test_data.generate_tips()

    def setUp(self):
        self.dummy_javacore_set = JavacoreSet("")

    def test_parse_mem_arg(self):
        line = "2CIUSERARG               -Xmx32g"
        mem = self.dummy_javacore_set.parse_mem_arg(line)
        self.assertEqual(mem, "32g")
        #
        line = "2CIUSERARG               -Xmx"
        mem = self.dummy_javacore_set.parse_mem_arg(line)
        self.assertEqual(mem, UNKNOWN)

    def test_parse_xmx(self):
        line = "2CIUSERARG               -Xmx32g"
        self.dummy_javacore_set.parse_xmx(line)
        self.assertEqual(self.dummy_javacore_set.xmx, "32g")
        #
        line = "2CIUSERARG               -Xmxg"
        self.dummy_javacore_set.parse_xmx(line)
        self.assertEqual(self.dummy_javacore_set.xmx, UNKNOWN)
        #
        line = "2CIUSERARG               -Xmx32k"
        mem = self.javacore_set_from_test_data.parse_mem_arg(line)
        self.assertEqual(mem, "32k")
        #
        line = "2CIUSERARG               -Xmx32K"
        mem = self.javacore_set_from_test_data.parse_mem_arg(line)
        self.assertEqual(mem, "32K")
        #
        line = "2CIUSERARG               -Xmx323232"
        mem = self.javacore_set_from_test_data.parse_mem_arg(line)
        self.assertEqual(mem, "323232")
        #
        line = "2CIUSERARG               -Xmx32B"
        mem = self.javacore_set_from_test_data.parse_mem_arg(line)
        self.assertEqual(mem, UNKNOWN)

    def test_parse_xms(self):
        line = "2CIUSERARG               -Xms32g"
        self.dummy_javacore_set.parse_xms(line)
        self.assertEqual(self.dummy_javacore_set.xms, "32g")
        #
        line = "2CIUSERARG               -Xmsg"
        self.dummy_javacore_set.parse_xms(line)
        self.assertEqual(self.dummy_javacore_set.xms, UNKNOWN)

    def test_parse_xmn(self):
        line = "2CIUSERARG               -Xmn2g"
        self.dummy_javacore_set.parse_xmn(line)
        self.assertEqual(self.dummy_javacore_set.xmn, "2g")
        #
        line = "2CIUSERARG               -Xmng"
        self.dummy_javacore_set.parse_xmn(line)
        self.assertEqual(self.dummy_javacore_set.xmn, UNKNOWN)

    def test_parse_gc_policy(self):
        line = "2CIUSERARG               -Xgcpolicy:gencon"
        self.dummy_javacore_set.parse_gc_policy(line)
        self.assertEqual(self.dummy_javacore_set.gc_policy, "gencon")

    def test_parse_compressed_refs(self):
        line = "2CIUSERARG               -Xcompressedrefs"
        self.dummy_javacore_set.parse_compressed_refs(line)
        self.assertTrue(self.dummy_javacore_set.compressed_refs)
        #
        line = "2CIUSERARG               -Xnocompressedrefs"
        self.dummy_javacore_set.parse_compressed_refs(line)
        self.assertFalse(self.dummy_javacore_set.compressed_refs)

    def test_parse_verbose_gc(self):
        line = ""
        self.dummy_javacore_set.verbose_gc = False
        self.dummy_javacore_set.parse_verbose_gc(line)
        self.assertFalse(self.dummy_javacore_set.verbose_gc)
        #
        line = "2CIUSERARG               -verbose:gc"
        self.dummy_javacore_set.parse_verbose_gc(line)
        self.assertTrue(self.dummy_javacore_set.verbose_gc)

    def test_parse_user_args(self):
        line = "2CIUSERARG               -Xmx32g"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertEqual(self.dummy_javacore_set.xmx, "32g")
        self.assertTrue("-Xmx32g" in self.dummy_javacore_set.user_args)
        #
        line = "2CIUSERARG               -Xms32g"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertEqual(self.dummy_javacore_set.xms, "32g")
        #
        line = "2CIUSERARG               -Xmn2g"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertEqual(self.dummy_javacore_set.xmn, "2g")
        #
        line = "2CIUSERARG               -Xgcpolicy:gencon"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertEqual(self.dummy_javacore_set.gc_policy, "gencon")
        #
        line = "2CIUSERARG               -Xcompressedrefs"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertTrue(self.dummy_javacore_set.compressed_refs)
        #
        line = "2CIUSERARG               -Xnocompressedrefs"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertFalse(self.dummy_javacore_set.compressed_refs)
        #
        line = ""
        self.dummy_javacore_set.parse_user_args(line)
        self.assertFalse(self.dummy_javacore_set.verbose_gc)
        #
        line = "2CIUSERARG               -verbose:gc"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertTrue(self.dummy_javacore_set.verbose_gc)
        self.assertTrue("-verbose:gc" in self.dummy_javacore_set.user_args)

        line = "2CIUSERARG               -Ddefault.client.encoding=UTF-8"
        self.dummy_javacore_set.parse_user_args(line)
        self.assertTrue("-Ddefault.client.encoding=UTF-8" in self.dummy_javacore_set.user_args)

    def test_sort_snapshots(self):
        # tested in test_java_thread.py in function test_sort_snapshots
        pass

    def test_parse_javacores_contain_valid_file(self):
        self.assertTrue(self.javacore_set_from_test_data.files.index('javacore.20220606.114458.32888.0001.txt') >= 0) #Object is on the list

    def test_parse_javacores_not_contain_wrong_file(self):
        # Check whether javacore.wrong.corr is in the list
        with self.assertRaises(ValueError):
            self.javacore_set_from_test_data.files.index('javacore.wrong.corr')

    # Note: the test below rely on the javacores stored in test directory
    def test_have_tips(self):
        self.assertTrue(any("OutOfMemoryError" in tip for tip in self.javacore_set_from_test_data.tips))
        self.assertTrue(any("[WARNING] The time interval between javacore" in tip for tip in
                            self.javacore_set_from_test_data.tips))

    # Note: the test below rely on the javacores stored in test directory
    def test_generate_blocked_snapshots_list(self):
        self.assertEqual(len(self.javacore_set_from_test_data.blocked_snapshots), 7,
                         "The javacores from test dir have different number of blocking threads")
        self.assertEqual(len(self.javacore_set_from_test_data.blocked_snapshots[0].get_threads_set()), 14)
