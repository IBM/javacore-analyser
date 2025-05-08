#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import unittest

from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.stack_trace import StackTrace
from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestJavaThread(unittest.TestCase):

    def setUp(self):
        self.thread = Thread()

        self.javacore1 = Javacore()
        self.javacore1.timestamp = datetime.datetime.strptime("2022/06/06 at 11:44:58:407",
                                                              "%Y/%m/%d at %H:%M:%S:%f").timestamp()

        self.thread.name = 'kernel-command-listener'
        self.thread.id = '0x1D'

        self.snapshot1 = ThreadSnapshot()
        self.snapshot1.javacore = self.javacore1
        self.snapshot1.cpu_usage = 4.020266638
        self.snapshot1.allocated_mem = 20456

        self.javacore2 = Javacore()
        self.javacore2.timestamp = datetime.datetime.strptime("2022/06/06 at 11:45:02:868",
                                                              "%Y/%m/%d at %H:%M:%S:%f").timestamp()
        self.snapshot2 = ThreadSnapshot()
        self.snapshot2.javacore = self.javacore2
        self.snapshot2.cpu_usage = 5.020266638
        self.snapshot2.allocated_mem = 20456

        self.javacore3 = Javacore()
        self.javacore3.timestamp = datetime.datetime.strptime("2022/06/06 at 11:45:06:334",
                                                              "%Y/%m/%d at %H:%M:%S:%f").timestamp()
        self.snapshot3 = ThreadSnapshot()
        self.snapshot3.javacore = self.javacore3
        self.snapshot3.cpu_usage = 6.020266638
        self.snapshot3.allocated_mem = 76456

        self.javacore4 = Javacore()
        self.javacore4.timestamp = datetime.datetime.strptime("2022/06/06 at 11:45:13:333",
                                                              "%Y/%m/%d at %H:%M:%S:%f").timestamp()
        self.snapshot4 = ThreadSnapshot()
        self.snapshot4.javacore = self.javacore4
        self.snapshot4.cpu_usage = 6.266638
        self.snapshot4.allocated_mem = 98456

        self.thread.thread_snapshots.append(self.snapshot1)
        self.thread.thread_snapshots.append(self.snapshot2)
        self.thread.thread_snapshots.append(self.snapshot3)
        self.thread.thread_snapshots.append(self.snapshot4)

        self.thread.compute_total_cpu()
        self.thread.compute_total_time()
        self.thread.compute_avg_mem()

    def test_sort_snapshots(self):
        self.thread.sort_snapshots()
        self.assertEqual(
            self.thread.thread_snapshots[0].get_timestamp() <
            self.thread.thread_snapshots[1].get_timestamp() <
            self.thread.thread_snapshots[2].get_timestamp() <
            self.thread.thread_snapshots[3].get_timestamp(), True)

    def test_compute_total_cpu(self):
        self.thread.compute_total_cpu()
        self.assertEqual(self.thread.total_cpu, 2.2463713620000005)

    def test_get_total_cpu(self):
        self.assertEqual(self.thread.get_total_cpu(), 2.2463713620000005)

    def test_compute_total_time(self):
        self.thread.compute_total_time()
        self.assertEqual(self.thread.total_time, 14.925999879837036)

    def test_get_total_time(self):
        self.assertEqual(self.thread.get_total_time(), 14.925999879837036)

    def test_get_cpu_percentage_usage(self):
        self.assertEqual(self.thread.get_cpu_percentage_usage(), 15.050056144208723)

    def test_compute_avg_mem(self):
        self.thread.compute_avg_mem()
        self.assertEqual(self.thread.avg_mem, 53956.0)

    def test_get_avg_mem(self):
        self.assertEqual(self.thread.get_avg_mem(), 53956.0)

    def test_is_interesting(self):
        thread = Thread()
        thread_snapshot1 = ThreadSnapshot()
        thread.thread_snapshots.append(thread_snapshot1)
        self.assertFalse(thread.is_interesting(),
                         "A thread with one empty snapshot is not interesting")
        thread_snapshot2 = ThreadSnapshot()
        thread_snapshot2.cpu_usage = 100
        thread.thread_snapshots.append(thread_snapshot2)
        self.assertTrue(thread.is_interesting(), "This thread consumes CPU")

        thread = Thread()
        thread_snapshot1 = ThreadSnapshot()
        thread_snapshot2 = ThreadSnapshot()
        thread_snapshot2.allocated_mem = 1024 * 1023 - 1 # just shy of a megabyte
        thread.thread_snapshots.append(thread_snapshot1)
        thread.thread_snapshots.append(thread_snapshot2)
        self.assertFalse(thread.is_interesting(),
                         "This thread allocated less than a megabyte of memory so should be boring")

        thread = Thread()
        thread_snapshot1 = ThreadSnapshot()
        thread_snapshot2 = ThreadSnapshot()
        thread_snapshot2.allocated_mem = 1024 * 1024  # 1 megabyte
        thread.thread_snapshots.append(thread_snapshot1)
        thread.thread_snapshots.append(thread_snapshot2)
        self.assertFalse(thread.is_interesting(),
                         "This thread allocated a megabyte of memory, so should be interesting")

        thread = Thread()
        thread_snapshot1 = ThreadSnapshot()
        thread_snapshot2 = ThreadSnapshot()
        thread.thread_snapshots.append(thread_snapshot1)
        thread_snapshot1.blocker = thread_snapshot2
        self.assertTrue(thread.is_interesting(), "This thread is blocked, so should be interesting")

        thread = Thread()
        thread_snapshot = ThreadSnapshot()
        stack_trace = StackTrace()
        for i in range(51):
            stack_trace_element = StackTraceElement()
            stack_trace.stack_trace_elements.append(stack_trace_element)
        thread.thread_snapshots.append(thread_snapshot)
        thread_snapshot.stack_trace = stack_trace
        self.assertTrue(thread.is_interesting(), "This thread has a tall stack, so should be interesting")

    def test_has_tall_stacks(self):
        thread = Thread()
        thread_snapshot = ThreadSnapshot()
        stack_trace = StackTrace()
        assert(not thread.has_tall_stacks())
        for i in range(50):
            stack_trace_element = StackTraceElement()
            stack_trace.stack_trace_elements.append(stack_trace_element)
        thread.thread_snapshots.append(thread_snapshot)
        thread_snapshot.stack_trace = stack_trace
        assert (not thread.has_tall_stacks())
        stack_trace.stack_trace_elements.append(StackTraceElement())
        assert (thread.has_tall_stacks())


