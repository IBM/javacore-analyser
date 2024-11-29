#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import time
import unittest
from xml.dom.minidom import parseString

from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.stack_trace import StackTrace
from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestThreadSnapshot(unittest.TestCase):

    def setUp(self):
        self.snapshot = ThreadSnapshot()
        self.doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
                                              <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')

    def test_parse_allocated_mem(self):
        line = "3XMHEAPALLOC             Heap bytes allocated since last GC cycle=3000 (0x0)"
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 3000, "Invalid number of bytes allocated")
        #
        line = ""
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 0, "Invalid number of bytes allocated")
        #
        line = ""
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 0, "More than zero bytes allocated for empty line")
        #
        line = "3XMHEAPALLOC             Heap bytes allocated since last GC cycle=0 (0x0)"
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 0, "Invalid number of bytes allocated")
        #
        line = "3XMHEAPALLOC             Heap bytes allocated since last GC cycle= (0x0)"
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 0, "More than zero bytes allocated for invalid line")
        #
        line = "3XMHEAPALLOC             Heap bytes allocated since last GC cycle=m (0x0)"
        self.snapshot.parse_allocated_mem(line)
        self.assertEqual(self.snapshot.allocated_mem, 0, "More than zero bytes allocated for invalid line")

    def test_get_thread_id(self):
        line = '3XMJAVALTHREAD            (java/lang/Thread getId:0x1D, isDaemon:false)'
        self.snapshot.parse_thread_id(line)
        self.assertEqual(self.snapshot.thread_id, '0x1D')

    def test_parse_state(self):
        line = '3XMTHREADINFO      "kernel-command-listener" J9VMThread:0x0000000000602500, \
        omrthread_t:0x000000A813EC05B8, java/lang/Thread:0x00000008008915F0, state:R, prio=5"'
        self.snapshot.parse_state(line)
        self.assertEqual(self.snapshot.state, "R")
        line = '3XMTHREADINFO      "kernel-command-listener" J9VMThread:0x0000000000602500, \
               omrthread_t:0x000000A813EC05B8, java/lang/Thread:0x00000008008915F0, state:CW, prio=5"'
        self.snapshot.parse_state(line)
        self.assertEqual(self.snapshot.state, "CW")

    def test_parse_blocker(self):
        line = '3XMTHREADBLOCK     Blocked on: com/ibm/team/repository/common/json/JSONObject@0x00000005247F78A0 Owned by: "WebContainer : 90 @@ 07:02 test <Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.25@10.141.118.75> /qm/service/com.ibm.team.repository.service.internal.webuiInitializer.IWebUIInitializerRestService/initializationData" (J9VMThread:0x0000000007EBB000, java/lang/Thread:0x00000007E6B18050)'
        self.snapshot.parse_blocker(line)
        blocker_name = 'WebContainer : 90 @@ 07:02 test <Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.25@10.141.118.75> /qm/service/com.ibm.team.repository.service.internal.webuiInitializer.IWebUIInitializerRestService/initializationData'
        self.assertEqual(self.snapshot.blocker_name, blocker_name)
        #
        line = '3XMTHREADBLOCK     Blocked on: com/ibm/ws/security/wim/adapter/ldap/context/ContextManager$1@0x0000000801010040 Owned by: "Default Executor-thread-22846" (J9VMThread:0x0000000007523000, java/lang/Thread:0x0000000832175560)'
        self.snapshot.parse_blocker(line)
        blocker_name = 'Default Executor-thread-22846'
        self.assertEqual(self.snapshot.blocker_name, blocker_name)

    def test_get_cpu_percentage(self):
        self.snapshot.cpu_usage_inc = 100
        self.snapshot.elapsed_time = 200
        self.assertEqual(self.snapshot.get_cpu_percentage(), 50)
        self.snapshot.elapsed_time = 0
        self.assertEqual(self.snapshot.get_cpu_percentage(), 0)
        self.snapshot.cpu_usage_inc = 0
        self.assertEqual(self.snapshot.get_cpu_percentage(), 0)

    def test_get_xml(self):
        self.snapshot.stack_trace = StackTrace()
        stack_trace_element = StackTraceElement()
        stack_trace_element.line = "at com.ibm.wait2.test.test_get_xml"
        self.snapshot.stack_trace.append(stack_trace_element)
        self.snapshot.name = "test name"
        self.snapshot.javacore = Javacore()
        self.snapshot.javacore.timestamp = time.time()
        snapshot_element = self.doc.createElement("snapshot")
        element = self.snapshot.get_xml(self.doc, snapshot_element)
        line_elements = element.getElementsByTagName("line")
        count = len(line_elements)
        assert(count == 1)
        line_element = line_elements[0]
        assert(line_element.getAttribute("kind") == "java")

    def test_get_thread_name(self):
        snap = ThreadSnapshot()
        snap.javacore = Javacore()
        snap.javacore._Javacore__encoding = "850"

        #
        line = '3XMTHREADINFO      "JIT Compilation Thread-001 Suspended" J9VMThread:0x0000000000767700, ' \
               'omrthread_t:0x00000219B181D8F0, java/lang/Thread:0x00000000FFF3D4C0, state:R, prio=10'
        name = snap.get_thread_name(line)
        self.assertEqual(name, 'JIT Compilation Thread-001 Suspended')
        #
        line = '3XMTHREADINFO      Anonymous native thread'
        name = snap.get_thread_name(line)
        self.assertEqual(name, '')
        #
        line = '3XMTHREADINFO      "thread name with " quotation" J9VMThread:0x0000000000894A00, ' \
               'omrthread_t:0x00000219B1D904F0, java/lang/Thread:0x00000000FFF90B20, state:R, prio=5'
        name = snap.get_thread_name(line)
        self.assertEqual(name, 'thread name with ? quotation')

    def test_get_cpu_usage_inc(self):
        self.snapshot.cpu_usage_inc = 1000
        self.assertEqual(self.snapshot.get_cpu_usage_inc(), 1000)
        #
        self.snapshot.cpu_usage_inc = None
        snap0 = ThreadSnapshot()
        snap0.cpu_usage = 100
        thread = Thread()
        snap0.thread = thread
        self.snapshot.thread = thread
        self.snapshot.cpu_usage = 200
        thread.thread_snapshots.append(snap0)
        thread.thread_snapshots.append(self.snapshot)
        inc = self.snapshot.get_cpu_usage_inc()
        self.assertEqual(inc, 100)

