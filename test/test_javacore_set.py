#
# Copyright IBM Corp. 2024 - 2026
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

    def test_start_time(self):
        self.assertEqual(self.javacore_set_from_test_data.jvm_info.jvm_start_time, "2022/06/06 at 11:33:18:586")

    def test_cmd_line(self):
        self.assertTrue(self.javacore_set_from_test_data.jvm_info.cmd_line.startswith("C:\\jazz\\ELM703M19\\server\\jre\\bin"
                                                                                       "\\javaw"))

    def test_sort_snapshots(self):
        # tested in test_java_thread.py in function test_sort_snapshots
        pass

    def test_parse_javacores_contain_valid_file(self):
        # Check if any file in the list ends with the expected filename
        self.assertTrue(any('javacore.20220606.114458.32888.0001.txt' in f for f in self.javacore_set_from_test_data.files))

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
