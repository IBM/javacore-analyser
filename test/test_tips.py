#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os.path
import shutil
import tempfile
import unittest

from javacore_analyser import tips
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore_set import JavacoreSet
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestTips(unittest.TestCase):
    def test_TooFewJavacoresTip(self):
        jc1 = os.path.join("test", "data", "javacores", "javacore.20220606.114458.32888.0001.txt")
        jc2 = os.path.join("test", "data", "javacores", "javacore.20220606.114502.32888.0002.txt")
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        shutil.copy2(jc1, temp_dir_path)
        shutil.copy2(jc2, temp_dir_path)
        javacore_set = JavacoreSet(temp_dir_path)
        javacore_set.create(temp_dir_path)
        result = tips.TooFewJavacoresTip.generate(javacore_set)
        self.assertTrue(len(result) > 0, "Missing tip for too few javacores")
        temp_dir.cleanup()

    def test_TooExcludedJAvacoresTip(self):
        jc1 = os.path.join("test", "data", "javacores", "javacore.20220606.114458.32888.0001.txt")
        jc2 = os.path.join("test", "data", "javacores", "javacore.20220606.114502.32888.0002.txt")
        jc3 = os.path.join("test", "data", "javacores", "javacore.20220606.114948.32888.0011.txt")
        jc4 = os.path.join("test", "data", "javacores", "javacore.20220606.114949.32888.0012.txt")
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        shutil.copy2(jc1, temp_dir_path)
        shutil.copy2(jc2, temp_dir_path)
        shutil.copy2(jc3, temp_dir_path)
        shutil.copy2(jc4, temp_dir_path)
        javacore_set = JavacoreSet(temp_dir_path)
        javacore_set = javacore_set.create(temp_dir_path)
        result = tips.ExcludedJavacoresTip.generate(javacore_set)
        self.assertEqual(2, len(result), "Wrong number of excluded javacores")
        self.assertRegex(result[0], "javacore.20220606.1149",  # Excluded files are generated at 11:49
                         "javacore.20220606.114948.32888.0011.txt is not added to excluded file list")
        temp_dir.cleanup()

    def test_blockingThreadsTip(self):
        jc1 = os.path.join("test", "data", "javacores", "javacore.20220606.114458.32888.0001.txt")
        jc2 = os.path.join("test", "data", "javacores", "javacore.20220606.114502.32888.0002.txt")
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        shutil.copy2(jc1, temp_dir_path)
        shutil.copy2(jc2, temp_dir_path)
        javacore_set = JavacoreSet(temp_dir_path)
        javacore_set = javacore_set.create(temp_dir_path)
        result = tips.BlockingThreadsTip.generate(javacore_set)
        self.assertEqual(1, len(result), "Wrong number of tips for blocking threads")
        tip_text = result[0]
        self.assertIn("JTS Status check", tip_text, "Tip text does not contain blocking thread name")
        temp_dir.cleanup()

    def test_blockingThreadsTipManyBlockingThreads(self):
        jc1 = os.path.join("test", "data", "javacores", "javacore.20220606.114458.32888.0001.txt")
        jc2 = os.path.join("test", "data", "javacores", "javacore.20220606.114506.32888.0003.txt")
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        shutil.copy2(jc1, temp_dir_path)
        shutil.copy2(jc2, temp_dir_path)
        javacore_set = JavacoreSet(temp_dir_path)
        javacore_set = javacore_set.create(temp_dir_path)
        result = tips.BlockingThreadsTip.generate(javacore_set)
        self.assertEqual(5, len(result), "Wrong number of tips for blocking threads")
        temp_dir.cleanup()

    def test_highCpuUsageTip(self):
        jc1 = os.path.join("test", "data", "javacores", "javacore.20220606.114931.32888.0009.txt")
        jc2 = os.path.join("test", "data", "javacores", "javacore.20220606.114947.32888.0010.txt")
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        shutil.copy2(jc1, temp_dir_path)
        shutil.copy2(jc2, temp_dir_path)
        javacore_set = JavacoreSet(temp_dir_path)
        javacore_set = javacore_set.create(temp_dir_path)
        javacore_set.populate_snapshot_collections()
        result = tips.HighCpuUsageTip.generate(javacore_set)
        self.assertEqual(6, len(result), "Wrong number of tips for high CPU usage")
        high_gc_usage_tip_found = False
        qm_asynchronous_task_found = False
        for tip in result:
            if "The verbose GC threads are using high CPU" in tip:
                high_gc_usage_tip_found = True
            elif "qm: AsynchronousTaskRunner-12" in tip:
                qm_asynchronous_task_found = True
            self.assertFalse("dcc: AsynchronousTaskRunner-10" in tip,
                             "The thread \"dcc: AsynchronousTaskRunner-10\" should not appear in high "
                             "CPU usage tip but it is there")
        self.assertTrue(high_gc_usage_tip_found, "High CPU usage tip not found")
        self.assertTrue(qm_asynchronous_task_found,
                            "\"qm: AsynchronousTaskRunner-12\" not found in high cpu usage tip")
        temp_dir.cleanup()

    def test_InvalidAccumulatedCpuTimeTip(self):
        javacore_set = JavacoreSet("")

        t1 = Thread()
        t1.id = 1
        t1.name = "winword"

        t2 = Thread()
        t2.id = 2
        t2.name = "excel"

        t3 = Thread()
        t3.id = 3
        t3.name = "powerpnt"

        javacore_set.threads.snapshot_collections.append(t1)
        javacore_set.threads.snapshot_collections.append(t2)
        javacore_set.threads.snapshot_collections.append(t3)

        # test 1, no thread in javacore_set
        result = tips.InvalidAccumulatedCpuTimeTip.generate(JavacoreSet(""))
        logging.debug("Test 1: %s" % result)
        expected_result = []
        failure_message = "There should be no tip as all threads are with valid total CPU"
        self.assertTrue(result == expected_result, failure_message)

        # test 2, all threads with valid total CPU (>= 0)
        t1.total_cpu = 30
        t2.total_cpu = 40
        t3.total_cpu = 40
        result = tips.InvalidAccumulatedCpuTimeTip.generate(javacore_set)
        logging.debug("Test 2: %s" % result)
        expected_result = []
        failure_message = "There should be no tip as all threads are with valid total CPU"
        self.assertTrue(result == expected_result, failure_message)

        # test 3, one thread with invalid CPU (<0)
        t1.total_cpu = 30
        t2.total_cpu = -1
        t3.total_cpu = 40
        result = tips.InvalidAccumulatedCpuTimeTip.generate(javacore_set)
        logging.debug("Test 3: %s" % result)
        expected_result = '[WARNING] The CPU usage data is invalid for thread "excel". '
        failure_message = "Wrong tip is displayed"
        self.assertTrue(expected_result in result[0], failure_message)

        # test 4, two threads with invalid CPU (<0)
        t1.total_cpu = 30
        t2.total_cpu = -1
        t3.total_cpu = -2
        result = tips.InvalidAccumulatedCpuTimeTip.generate(javacore_set)
        logging.debug("Test 4: %s" % result)
        expected_result = '[WARNING] 2 threads have invalid accumulated CPU. '
        failure_message = "Wrong tip is displayed"
        self.assertTrue(expected_result in result[0], failure_message)

        # test 5, one thread with total CPU = 0
        t1.total_cpu = 0
        ts1 = ThreadSnapshot()
        ts1.cpu_usage = 0
        ts2 = ThreadSnapshot()
        ts2.cpu_usage = 0
        t1.thread_snapshots.append(ts1)
        t1.thread_snapshots.append(ts2)

        t2.total_cpu = 1
        t3.total_cpu = 2
        result = tips.InvalidAccumulatedCpuTimeTip.generate(javacore_set)
        logging.debug("Test 5: %s" % result)
        expected_result = []
        failure_message = "There should be no tip as all threads are with valid total CPU"
        self.assertTrue(result == expected_result, failure_message)
