#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest

from javacore_analyser.javacore import Javacore
from javacore_analyser.javacore_set import JavacoreSet
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestJavacore(unittest.TestCase):

    def setUp(self):
        self.javacore_set = JavacoreSet('data' + os.path.sep + 'javacores')
        self.filename = 'test' + os.path.sep + 'data' + os.path.sep + 'javacores' + os.path.sep + 'javacore.20220606.114458.32888.0001.txt'
        self.javacore = Javacore.create(self.filename, self.javacore_set)
        self.filename2 = 'test' + os.path.sep + 'data' + os.path.sep + 'encoding' + os.path.sep + 'javacore.20220606.114458.32888.0001.txt'
        self.javacore2 = Javacore.create(self.filename2, self.javacore_set)

    def test_get_encoding(self):
        encoding = self.javacore.get_encoding()
        self.assertEqual(encoding, '1252')
        encoding = self.javacore2.get_encoding()
        self.assertEqual(encoding, '850')

    def test_parse_snapshot_data(self):
        self.assertEqual(201, len(self.javacore.snapshots))

    def test_parse_siginfo(self):
        t = self.javacore.siginfo
        self.assertEqual(t, 'Dump Requested By User (00100000) Through com.ibm.jvm.Dump.javaDumpToFile')

    def test_get_snapshot_by_name(self):
        snapshot_name = self.javacore.get_snapshot_by_name('kernel-command-listener').name
        snapshot_name_from_test_javacore = self.javacore.snapshots[0].name
        self.assertEqual(snapshot_name, snapshot_name_from_test_javacore)

    def test_basefilename(self):
        self.assertEqual(self.javacore.basefilename(), 'javacore.20220606.114458.32888.0001.txt')
