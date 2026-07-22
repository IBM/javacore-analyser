#
# Copyright IBM Corp. 2024 - 2026
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

from javacore_analyser.verbose_gc import GcCollection


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

    def test_LongGcPauseTip_no_verbose_gc(self):
        """Test LongGcPauseTip when no verbose GC data is available"""
        javacore_set = JavacoreSet("")
        result = tips.LongGcPauseTip.generate(javacore_set)
        self.assertEqual(0, len(result), "Should return empty list when no verbose GC data")

    def test_LongGcPauseTip_no_long_pauses(self):
        """Test LongGcPauseTip when all GC pauses are below threshold"""
        from javacore_analyser.verbose_gc import GcCollection
        
        javacore_set = JavacoreSet("")
        
        # Create mock GC collections with short pauses
        collect1 = GcCollection()
        collect1.duration = 500.0  # 500ms - below threshold
        collect1.start_time_str = "2023-04-25T11:04:13.857"
        
        collect2 = GcCollection()
        collect2.duration = 800.0  # 800ms - below threshold
        collect2.start_time_str = "2023-04-25T11:04:14.857"
        
        javacore_set.gc_parser._VerboseGcParser__collects = [collect1, collect2]
        
        result = tips.LongGcPauseTip.generate(javacore_set)
        self.assertEqual(0, len(result), "Should return empty list when no long pauses")

    def test_LongGcPauseTip_with_long_pauses(self):
        """Test LongGcPauseTip when GC pauses exceed thresholds"""
        
        javacore_set = JavacoreSet("")
        
        # Create mock GC collections with long pauses
        collect1 = GcCollection()
        collect1.duration = 1200.0  # 1200ms - exceeds threshold 1
        collect1.start_time_str = "2023-04-25T11:04:13.857"
        
        collect2 = GcCollection()
        collect2.duration = 2500.0  # 2500ms - exceeds both thresholds
        collect2.start_time_str = "2023-04-25T11:04:15.857"
        
        collect3 = GcCollection()
        collect3.duration = 1500.0  # 1500ms - exceeds threshold 1
        collect3.start_time_str = "2023-04-25T11:04:17.857"
        
        collect4 = GcCollection()
        collect4.duration = 500.0  # 500ms - below threshold
        collect4.start_time_str = "2023-04-25T11:04:18.857"
        
        javacore_set.gc_parser._VerboseGcParser__collects = [collect1, collect2, collect3, collect4]
        
        result = tips.LongGcPauseTip.generate(javacore_set)
        self.assertEqual(1, len(result), "Should return one warning message")
        
        tip_text = result[0]
        self.assertIn("[WARNING]", tip_text, "Tip should contain WARNING")
        self.assertIn("3 GC pause(s) longer than 1000ms", tip_text, 
                     "Should report 3 pauses over 1000ms threshold")
        self.assertIn("1 GC pause(s) longer than 2000ms", tip_text,
                     "Should report 1 pause over 2000ms threshold")
        self.assertIn("2500", tip_text, "Should report longest pause of 2500ms")
        self.assertIn("2023-04-25T11:04:15.857", tip_text, 
                     "Should report timestamp of longest pause")


    def test_SystemExitInMainThreadTip_with_system_exit(self):
        """Test SystemExitInMainThreadTip when System.exit is present in main thread"""
        from javacore_analyser.javacore import Javacore
        from javacore_analyser.stack_trace import StackTrace
        from javacore_analyser.stack_trace_element import StackTraceElement

        javacore_set = JavacoreSet("")

        # Create a mock javacore
        jc = Javacore()
        jc.filename = "test_javacore.txt"
        jc.datetime = None
        jc.timestamp = 0
        jc.siginfo = "test"

        # Create a main thread snapshot with System.exit in stack trace
        main_snapshot = ThreadSnapshot()
        main_snapshot.name = "main"
        main_snapshot.thread_id = "1"
        main_snapshot.cpu_usage = 0

        # Create stack trace with System.exit
        stack_trace = StackTrace()
        element = StackTraceElement()
        element.line = "at java.lang.System.exit(System.java:123)"
        stack_trace.append(element)
        main_snapshot.stack_trace = stack_trace

        jc.snapshots = [main_snapshot]
        javacore_set.javacores = [jc]

        result = tips.SystemExitInMainThreadTip.generate(javacore_set)
        self.assertEqual(1, len(result), "Should return one warning message")
        self.assertIn("[WARNING]", result[0], "Tip should contain WARNING")
        self.assertIn("System.exit", result[0], "Tip should mention System.exit")
        self.assertIn("test_javacore.txt", result[0], "Tip should mention the javacore filename")
        self.assertIn("main", result[0], "Tip should mention the thread name")

    def test_SystemExitInMainThreadTip_without_system_exit(self):
        """Test SystemExitInMainThreadTip when System.exit is not present"""
        from javacore_analyser.javacore import Javacore
        from javacore_analyser.stack_trace import StackTrace
        from javacore_analyser.stack_trace_element import StackTraceElement

        javacore_set = JavacoreSet("")

        # Create a mock javacore
        jc = Javacore()
        jc.filename = "test_javacore.txt"
        jc.datetime = None
        jc.timestamp = 0
        jc.siginfo = "test"

        # Create a main thread snapshot without System.exit
        main_snapshot = ThreadSnapshot()
        main_snapshot.name = "main"
        main_snapshot.thread_id = "1"
        main_snapshot.cpu_usage = 0

        # Create stack trace without System.exit
        stack_trace = StackTrace()
        element = StackTraceElement()
        element.line = "at com.example.MyClass.doWork(MyClass.java:45)"
        stack_trace.append(element)
        main_snapshot.stack_trace = stack_trace

        jc.snapshots = [main_snapshot]
        javacore_set.javacores = [jc]

        result = tips.SystemExitInMainThreadTip.generate(javacore_set)
        self.assertEqual(0, len(result), "Should return empty list when no System.exit")

    def test_SystemExitInMainThreadTip_in_worker_thread(self):
        """Test SystemExitInMainThreadTip when System.exit is in a worker thread"""
        from javacore_analyser.javacore import Javacore
        from javacore_analyser.stack_trace import StackTrace
        from javacore_analyser.stack_trace_element import StackTraceElement

        javacore_set = JavacoreSet("")

        # Create a mock javacore
        jc = Javacore()
        jc.filename = "test_javacore.txt"
        jc.datetime = None
        jc.timestamp = 0
        jc.siginfo = "test"

        # Create a non-main thread snapshot with System.exit
        worker_snapshot = ThreadSnapshot()
        worker_snapshot.name = "Worker-Thread-1"
        worker_snapshot.thread_id = "2"
        worker_snapshot.cpu_usage = 0

        # Create stack trace with System.exit
        stack_trace = StackTrace()
        element = StackTraceElement()
        element.line = "at java.lang.System.exit(System.java:123)"
        stack_trace.append(element)
        worker_snapshot.stack_trace = stack_trace

        jc.snapshots = [worker_snapshot]
        javacore_set.javacores = [jc]

        result = tips.SystemExitInMainThreadTip.generate(javacore_set)
        self.assertEqual(1, len(result), "Should return one warning message")
        self.assertIn("[WARNING]", result[0], "Tip should contain WARNING")
        self.assertIn("System.exit", result[0], "Tip should mention System.exit")
        self.assertIn("Worker-Thread-1", result[0], "Tip should mention the worker thread name")
        self.assertIn("test_javacore.txt", result[0], "Tip should mention the javacore filename")

    def _make_thread(self, name, thread_id, states):
        """Helper: build a Thread with one ThreadSnapshot per state string."""
        thread = Thread()
        thread.name = name
        thread.id = thread_id
        for state in states:
            s = ThreadSnapshot()
            s.state = state
            s.cpu_usage = 0
            thread.thread_snapshots.append(s)
        return thread

    # ------------------------------------------------------------------
    # PermanentlyBlockedThreadsTip
    # ------------------------------------------------------------------

    def test_PermanentlyBlockedThreadsTip_no_threads(self):
        """Returns empty list when javacore_set has no threads."""
        javacore_set = JavacoreSet("")
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual([], result, "Should return empty list when no threads present")

    def test_PermanentlyBlockedThreadsTip_no_blocked_threads(self):
        """Returns empty list when all threads are running (state R)."""
        javacore_set = JavacoreSet("")
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("worker-1", "0x1", ["R", "R", "R"])
        )
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("worker-2", "0x2", ["R", "CW", "R"])
        )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual([], result, "Should return empty list when no thread is permanently blocked")

    def test_PermanentlyBlockedThreadsTip_one_blocked_thread(self):
        """Returns one warning when exactly one thread is blocked in all snapshots."""
        javacore_set = JavacoreSet("")
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("stuck-thread", "0x10", ["B", "B", "B"])
        )
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("healthy-thread", "0x11", ["R", "R", "R"])
        )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual(1, len(result), "Should return one warning for one permanently blocked thread")
        self.assertIn("[WARNING]", result[0], "Tip should contain WARNING")
        self.assertIn("stuck-thread", result[0], "Tip should contain the thread name")
        self.assertIn("3", result[0], "Tip should mention the number of snapshots")

    def test_PermanentlyBlockedThreadsTip_partially_blocked_thread(self):
        """Returns empty list when a thread is blocked in some but not all snapshots."""
        javacore_set = JavacoreSet("")
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("sometimes-blocked", "0x20", ["B", "B", "R"])
        )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual([], result, "Should not flag a thread that is only sometimes blocked")

    def test_PermanentlyBlockedThreadsTip_below_min_snapshots(self):
        """Returns empty list when thread appears in fewer snapshots than MIN_SNAPSHOTS."""
        javacore_set = JavacoreSet("")
        min_snaps = tips.PermanentlyBlockedThreadsTip.MIN_SNAPSHOTS
        # Build a thread with one fewer snapshot than the minimum
        states = ["B"] * (min_snaps - 1)
        javacore_set.threads.snapshot_collections.append(
            self._make_thread("short-lived-blocked", "0x30", states)
        )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual([], result,
                         "Should not flag a thread with fewer snapshots than MIN_SNAPSHOTS")

    def test_PermanentlyBlockedThreadsTip_multiple_blocked_threads(self):
        """Returns one warning per permanently blocked thread."""
        javacore_set = JavacoreSet("")
        for i in range(3):
            javacore_set.threads.snapshot_collections.append(
                self._make_thread(f"stuck-{i}", f"0x{i}", ["B", "B", "B", "B"])
            )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual(3, len(result), "Should return one warning per permanently blocked thread")
        for tip_text in result:
            self.assertIn("[WARNING]", tip_text)

    def test_PermanentlyBlockedThreadsTip_capped_at_max(self):
        """Never returns more warnings than MAX_TIPS."""
        javacore_set = JavacoreSet("")
        max_tips = tips.PermanentlyBlockedThreadsTip.MAX_TIPS
        for i in range(max_tips + 3):
            javacore_set.threads.snapshot_collections.append(
                self._make_thread(f"stuck-{i}", f"0x{i}", ["B", "B", "B"])
            )
        result = tips.PermanentlyBlockedThreadsTip.generate(javacore_set)
        self.assertEqual(max_tips, len(result),
                         f"Should cap output at MAX_TIPS ({max_tips})")
