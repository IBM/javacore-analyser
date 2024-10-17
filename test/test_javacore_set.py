#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest

from constants import UNKNOWN
from javacore_set import JavacoreSet


class TestJavacoreSet(unittest.TestCase):

    def setUp(self):
        self.snapshot = JavacoreSet("")
        self.javacore_set = JavacoreSet('data' + os.path.sep + 'javacores')
        javacores_path = os.getcwd() + os.sep + 'test' + os.sep + 'data' + os.sep + 'javacores'
        self.jset = self.javacore_set.create(javacores_path)
        self.jset.generate_tips()

    def test_parse_mem_arg(self):
        line = "2CIUSERARG               -Xmx32g"
        mem = self.snapshot.parse_mem_arg(line)
        self.assertEqual(mem, "32g")
        #
        line = "2CIUSERARG               -Xmx"
        mem = self.snapshot.parse_mem_arg(line)
        self.assertEqual(mem, UNKNOWN)

    def test_parse_xmx(self):
        line = "2CIUSERARG               -Xmx32g"
        self.snapshot.parse_xmx(line)
        self.assertEqual(self.snapshot.xmx, "32g")
        #
        line = "2CIUSERARG               -Xmxg"
        self.snapshot.parse_xmx(line)
        self.assertEqual(self.snapshot.xmx, UNKNOWN)

    def test_parse_xms(self):
        line = "2CIUSERARG               -Xms32g"
        self.snapshot.parse_xms(line)
        self.assertEqual(self.snapshot.xms, "32g")
        #
        line = "2CIUSERARG               -Xmsg"
        self.snapshot.parse_xms(line)
        self.assertEqual(self.snapshot.xms, UNKNOWN)

    def test_parse_xmn(self):
        line = "2CIUSERARG               -Xmn2g"
        self.snapshot.parse_xmn(line)
        self.assertEqual(self.snapshot.xmn, "2g")
        #
        line = "2CIUSERARG               -Xmng"
        self.snapshot.parse_xmn(line)
        self.assertEqual(self.snapshot.xmn, UNKNOWN)

    def test_parse_gc_policy(self):
        line = "2CIUSERARG               -Xgcpolicy:gencon"
        self.snapshot.parse_gc_policy(line)
        self.assertEqual(self.snapshot.gc_policy, "gencon")

    def test_parse_compressed_refs(self):
        line = "2CIUSERARG               -Xcompressedrefs"
        self.snapshot.parse_compressed_refs(line)
        self.assertTrue(self.snapshot.compressed_refs)
        #
        line = "2CIUSERARG               -Xnocompressedrefs"
        self.snapshot.parse_compressed_refs(line)
        self.assertFalse(self.snapshot.compressed_refs)

    def test_parse_verbose_gc(self):
        line = ""
        self.snapshot.parse_verbose_gc(line)
        self.assertFalse(self.snapshot.verbose_gc)
        #
        line = "2CIUSERARG               -verbose:gc"
        self.snapshot.parse_verbose_gc(line)
        self.assertTrue(self.snapshot.verbose_gc)

    def test_parse_user_args(self):
        line = "2CIUSERARG               -Xmx32g"
        self.snapshot.parse_user_args(line)
        self.assertEqual(self.snapshot.xmx, "32g")
        self.assertTrue("-Xmx32g" in self.snapshot.user_args)
        #
        line = "2CIUSERARG               -Xms32g"
        self.snapshot.parse_user_args(line)
        self.assertEqual(self.snapshot.xms, "32g")
        #
        line = "2CIUSERARG               -Xmn2g"
        self.snapshot.parse_user_args(line)
        self.assertEqual(self.snapshot.xmn, "2g")
        #
        line = "2CIUSERARG               -Xgcpolicy:gencon"
        self.snapshot.parse_user_args(line)
        self.assertEqual(self.snapshot.gc_policy, "gencon")
        #
        line = "2CIUSERARG               -Xcompressedrefs"
        self.snapshot.parse_user_args(line)
        self.assertTrue(self.snapshot.compressed_refs)
        #
        line = "2CIUSERARG               -Xnocompressedrefs"
        self.snapshot.parse_user_args(line)
        self.assertFalse(self.snapshot.compressed_refs)
        #
        line = ""
        self.snapshot.parse_user_args(line)
        self.assertFalse(self.snapshot.verbose_gc)
        #
        line = "2CIUSERARG               -verbose:gc"
        self.snapshot.parse_user_args(line)
        self.assertTrue(self.snapshot.verbose_gc)
        self.assertTrue("-verbose:gc" in self.snapshot.user_args)

        line = "2CIUSERARG               -Ddefault.client.encoding=UTF-8"
        self.snapshot.parse_user_args(line)
        self.assertTrue("-Ddefault.client.encoding=UTF-8" in self.snapshot.user_args)

    def test_sort_snapshots(self):
        # tested in test_java_thread.py in function test_sort_snapshots
        pass

    def test_parse_javacores_contain_valid_file(self):
        self.assertTrue(self.jset.files.index('javacore.20220606.114458.32888.0001.txt') >= 0) #Object is on the list

    def test_parse_javacores_not_contain_wrong_file(self):
        # Check whether javacore.wrong.corr is in the list
        with self.assertRaises(ValueError):
            self.jset.files.index('javacore.wrong.corr')

    # Note: the test below rely on the javacores stored in test directory
    def test_have_tips(self):
        self.assertTrue(any("OutOfMemoryError" in tip for tip in self.jset.tips))
        self.assertTrue(any("[WARNING] The time interval between javacore" in tip for tip in self.jset.tips))

    # Note: the test below rely on the javacores stored in test directory
    def test_generate_blocked_snapshots_list(self):
        self.assertEqual(len(self.jset.blocked_snapshots),7, "The javacores from test dir have different number of "
                                                             "blocking threads")
        self.assertEqual(len(self.jset.blocked_snapshots[0].get_threads_set()), 14)
