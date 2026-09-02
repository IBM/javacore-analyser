#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import os
import unittest

from javacore_analyser.javacore import Javacore
from javacore_analyser.javacore_set import JavacoreSet
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestJavacore(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join('test', 'data', 'javacores')
        self.javacore_set = JavacoreSet('data' + os.path.sep + 'javacores')
        self.filename = 'test' + os.path.sep + 'data' + os.path.sep + 'javacores' + os.path.sep + 'javacore.20220606.114458.32888.0001.txt'
        self.javacore = Javacore.create(self.filename, self.javacore_set)
        self.filename2 = 'test' + os.path.sep + 'data' + os.path.sep + 'encoding' + os.path.sep + 'javacore.20220606.114458.32888.0001.txt'
        self.javacore2 = Javacore.create(self.filename2, self.javacore_set)
        
        # Additional test file for comparison
        self.filename3 = os.path.join(self.test_data_dir, 'javacore.20220606.114502.32888.0002.txt')
        self.javacore3 = Javacore.create(self.filename3, self.javacore_set)

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

    # ========== Tests for parse() method covering all _parse* private methods ==========

    def test_parse_extracts_all_attributes(self):
        """
        Test that parse() successfully extracts all attributes by calling private _parse* methods.
        This test verifies the code paths of all private parsing methods are covered.
        """
        # Verify siginfo extraction (tests _parse_siginfo)
        self.assertIsNotNone(self.javacore.siginfo)
        self.assertEqual(
            self.javacore.siginfo,
            'Dump Requested By User (00100000) Through com.ibm.jvm.Dump.javaDumpToFile'
        )
        
        # Verify datetime extraction (tests _parse_datetime)
        self.assertIsNotNone(self.javacore.datetime)
        self.assertIsInstance(self.javacore.datetime, datetime.datetime)
        self.assertEqual(self.javacore.datetime.year, 2022)
        self.assertEqual(self.javacore.datetime.month, 6)
        self.assertEqual(self.javacore.datetime.day, 6)
        self.assertEqual(self.javacore.datetime.hour, 11)
        self.assertEqual(self.javacore.datetime.minute, 44)
        self.assertEqual(self.javacore.datetime.second, 58)
        
        # Verify timestamp calculation (tests _parse_datetime)
        self.assertIsNotNone(self.javacore.timestamp)
        self.assertIsInstance(self.javacore.timestamp, float)
        self.assertEqual(self.javacore.timestamp, self.javacore.datetime.timestamp())
        
        # Verify header data extraction (tests _parse_header_data)
        self.assertIsNotNone(self.javacore.jvm_info.number_of_cpus)
        self.assertEqual(self.javacore.jvm_info.number_of_cpus, '8')
        self.assertIsNotNone(self.javacore.jvm_info.os_level)
        self.assertIn('Windows', self.javacore.jvm_info.os_level)
        self.assertIsNotNone(self.javacore.jvm_info.architecture)
        self.assertEqual(self.javacore.jvm_info.architecture, 'amd64')
        self.assertIsNotNone(self.javacore.jvm_info.java_version)
        self.assertIn('JRE 1.8.0', self.javacore.jvm_info.java_version)
        self.assertIsNotNone(self.javacore.jvm_info.jvm_start_time)
        self.assertIn('2022/06/06', self.javacore.jvm_info.jvm_start_time)
        self.assertIsNotNone(self.javacore.jvm_info.cmd_line)
        self.assertIn('javaw', self.javacore.jvm_info.cmd_line)

        # Verify user arguments extraction (tests _parse_user_args and _add_user_arg)
        self.assertIsNotNone(self.javacore.jvm_info.user_args)
        self.assertGreater(len(self.javacore.jvm_info.user_args), 0)
        user_args_str = ' '.join(self.javacore.jvm_info.user_args)
        self.assertIn('-Xmx', user_args_str)
        self.assertIn('-Xms', user_args_str)
        self.assertIn('-Xmn', user_args_str)

        # Verify memory settings extraction (tests _parse_xmx, _parse_xms, _parse_xmn, _parse_mem_arg)
        self.assertIsNotNone(self.javacore.jvm_info.xmx)
        self.assertEqual(self.javacore.jvm_info.xmx, '4294967296')
        self.assertIsNotNone(self.javacore.jvm_info.xms)
        self.assertEqual(self.javacore.jvm_info.xms, '4G')
        self.assertIsNotNone(self.javacore.jvm_info.xmn)
        self.assertEqual(self.javacore.jvm_info.xmn, '1G')

        # Verify GC policy extraction (tests _parse_gc_policy)
        self.assertIsNotNone(self.javacore.jvm_info.gc_policy)
        self.assertEqual(self.javacore.jvm_info.gc_policy, 'gencon')

        # Verify compressed refs detection (tests _parse_compressed_refs)
        self.assertTrue(self.javacore.jvm_info.compressed_refs)

        # Verify verbose GC detection (tests _parse_verbose_gc)
        self.assertTrue(self.javacore.jvm_info.verbose_gc)
        
        # Verify thread snapshots creation (tests _parse_thread_snapshots)
        self.assertIsNotNone(self.javacore.snapshots)
        self.assertGreater(len(self.javacore.snapshots), 0)
        self.assertEqual(len(self.javacore.snapshots), 201)
        first_snapshot = self.javacore.snapshots[0]
        self.assertIsNotNone(first_snapshot.name)

    def test_parse_multiple_javacores_consistency(self):
        """
        Test parsing multiple javacore files to ensure all _parse* methods work consistently.
        """
        # Parse multiple files from test data
        test_files = [
            'javacore.20220606.114458.32888.0001.txt',
            'javacore.20220606.114502.32888.0002.txt',
            'javacore.20220606.114506.32888.0003.txt',
        ]
        
        javacores = []
        for filename in test_files:
            filepath = os.path.join(self.test_data_dir, filename)
            if os.path.exists(filepath):
                jc = Javacore.create(filepath, self.javacore_set)
                javacores.append(jc)
        
        # All should parse successfully
        self.assertGreaterEqual(len(javacores), 2)
        
        # All should have required attributes populated by _parse* methods
        for jc in javacores:
            self.assertIsNotNone(jc.siginfo)
            self.assertIsNotNone(jc.datetime)
            self.assertIsNotNone(jc.jvm_info.number_of_cpus)
            self.assertGreater(len(jc.snapshots), 0)
            self.assertIsNotNone(jc.jvm_info.xmx)
            self.assertIsNotNone(jc.jvm_info.gc_policy)

    def test_parse_with_different_encodings(self):
        """
        Test that parse() correctly handles files with different encodings.
        This verifies the encoding detection logic in parse().
        """
        # Test with encoding test file
        encoding = self.javacore2.get_encoding()
        self.assertEqual(encoding, '850')
        
        # Verify parse() still extracted all key attributes despite different encoding
        self.assertIsNotNone(self.javacore2.siginfo)
        self.assertIsNotNone(self.javacore2.datetime)
        self.assertIsNotNone(self.javacore2.jvm_info.number_of_cpus)
