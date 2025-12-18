#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import unittest

from javacore_analyser.code_snapshot_collection import CodeSnapshotCollection
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore_set import JavacoreSet
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestCodeSnapshotCollection(unittest.TestCase):

    def setUp(self):
        self.empty_javacore_set = JavacoreSet('', {"use_ai": False, "skip_boring": True})

    def test_get_threads(self):
        snapshot_collection1 = CodeSnapshotCollection(self.empty_javacore_set)
        thread0 = Thread(self.empty_javacore_set)
        thread0.id = '0x0'
        thread1 = Thread(self.empty_javacore_set)
        thread1.id = '0x1'

        for i in range(5):
            snapshot = ThreadSnapshot()
            if i % 2 == 0:
                snapshot.thread = thread0
            else:
                snapshot.thread = thread1

            snapshot_collection1.thread_snapshots.append(snapshot)

        self.assertEqual(len(snapshot_collection1.get_threads()), 2)

    def test_is_interesting(self):
        code_snapshot_collection = CodeSnapshotCollection(self.empty_javacore_set)
        self.assertTrue(code_snapshot_collection.is_interesting())
