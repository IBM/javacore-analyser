#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
import re
from datetime import datetime

from javacore_analyser.constants import *
from javacore_analyser.stack_trace import StackTrace
from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.stack_trace_kind import StackTraceKind


class ThreadSnapshot:

    def __init__(self):
        """ dummy constructor for tests only """
        self.cpu_usage = 0
        self.allocated_mem = 0
        self.name = None
        self.thread_id = None
        self.thread = None
        self.javacore = None
        self.blocker = None
        self.blocker_name = None
        self.stack_trace = None
        self.file = None
        self.state = UNKNOWN
        self.elapsed_time = None
        self.cpu_usage_inc = None
        self.blocking = set()  # set of snapshots blocking by this thread

    @staticmethod
    def create(line, file, javacore):
        snapshot = ThreadSnapshot()
        snapshot.file = file
        snapshot.javacore = javacore
        snapshot.name = snapshot.get_thread_name(line)
        snapshot.parse_state(line)
        snapshot.parse_snapshot_data()
        return snapshot

    def parse_snapshot_data(self):
        """Parses cpu time line and allocated memory line from provided file and saves as instance attributes"""
        while True:
            line = self.file.readline()
            line = self.javacore.encode(line)
            if not line: break
            if line.startswith("NULL"): break
            if line.startswith(THREAD_ID): self.parse_thread_id(line)
            if line.startswith(CPU_TIME): self.parse_cpu_usage(line)
            if line.startswith(ALLOCATED_MEM): self.parse_allocated_mem(line)
            if line.startswith(THREAD_BLOCK): self.parse_blocker(line)
            if line.startswith(STACK_TRACE):
                self.parse_stack_trace(line)
                return  # stack trace is the last part of a thread in a javacore,
                # so once we're done with it, we move on to parsing the next thread

    def get_thread_name(self, line):
        """ assuming line format:
        3XMTHREADINFO      "Default Executor-thread-27781" J9VMThread:0x0000000009443300,
        omrthread_t:0x000000A8B62C3758, java/lang/Thread:0x00000008432D4140, state:B, prio=5 """
        tokens = line.split('"')
        if len(tokens) < 2: return ""  # skipping anonymous native threads
        name = ""
        for i in range(1, len(tokens) - 1):
            if i > 1: name = name + "?"
            name = name + tokens[i]
        name = name.strip()
        name = self.javacore.encode(name)

        # fix for https://trello.com/c/W0tS9b4K/116-processing-javacores-fail-with-xmletreeelementtreeparseerror-not-
        # well-formed-invalid-token-line-1-column-13722
        name = name.translate(str.maketrans({"\01": "[SOH]"}))
        return name

    def get_thread_hash(self):
        if self.thread:
            return self.thread.get_hash()
        return ""

    def get_thread_id(self):
        if self.thread:
            return self.thread.id
        return 0

    def get_previous_snapshot(self):
        previous_thread_snapshot = None
        if self.thread is None: return None
        for snapshot in self.thread.thread_snapshots:
            if snapshot == self:
                return previous_thread_snapshot
            previous_thread_snapshot = snapshot
        return None

    def get_cpu_percentage(self):
        elapsed_time = self.get_elapsed_time()
        cpu_usage_inc = self.get_cpu_usage_inc()
        if elapsed_time == 0: return 0
        return 100 * cpu_usage_inc / elapsed_time

    def parse_state(self, line):
        matches = re.findall("state:[A-Z]+", line)
        if len(matches) == 0:
            return
        state_string = matches[0]
        tokens = state_string.split(':')
        self.state = tokens[-1]

    def parse_thread_id(self, line):
        tokens = line.split(':')
        thread_id = tokens[1].split(',')[0]
        self.thread_id = thread_id

    def parse_cpu_usage(self, line):
        """ assuming line format:
        3XMCPUTIME    CPU usage total: 0.218750000 secs, user: 0.171875000 secs,
        system: 0.046875000 secs, current category="Application" """
        m = re.search("CPU usage total: ([0-9]+\\.[0-9]+) secs,", line)

        try:
            token = m.group(1)
            self.cpu_usage = float(token)
        except Exception as ex:
            logging.warning(ex)
            self.cpu_usage = 0
        # tokens = re.findall("[0-9]+\.[0-9]+", line)
        # if len(tokens) == 0:
        #     self.cpu_usage = 0
        #     return
        # self.cpu_usage = float(tokens[0])  # assuming the first number is the CPU usage total

    def get_timestamp(self):
        return self.javacore.timestamp

    def parse_allocated_mem(self, line):
        """ assuming line format:
        3XMHEAPALLOC             Heap bytes allocated since last GC cycle=0 (0x0) """
        tokens = re.findall("cycle=[0-9]+", line)
        if len(tokens) == 0:
            self.allocated_mem = 0
            return
        line = tokens[0]
        tokens = re.findall("[0-9]+", line)
        if len(tokens) == 0:
            self.allocated_mem = 0
            return
        self.allocated_mem = int(tokens[0])

    def parse_blocker(self, line):
        tokens = line.split('"')
        if len(tokens) == 3:
            self.blocker_name = tokens[1]
            return
        if line.__contains__("<") and line.__contains__(">"):
            start = line.rindex("<")
            stop = line.rindex(">")
            self.blocker_name = line[start: stop]

    def get_blocker(self):
        if not self.blocker_name: return None
        if not self.blocker:
            self.blocker = self.javacore.get_snapshot_by_name(self.blocker_name)
        return self.blocker

    def get_blocker_name(self):
        if self.get_blocker(): return self.get_blocker().name + "(" + self.get_blocker().thread_id + ")"
        return ""

    def get_blocker_id(self):
        if self.get_blocker(): return self.get_blocker().thread_id
        return ""

    def get_blocker_hash(self):
        if self.get_blocker(): return self.get_blocker().get_thread_hash()
        return ""

    def get_java_stack_depth(self):
        if self.stack_trace is None:
            return 0
        return self.stack_trace.get_java_stack_depth()

    def get_stack_depth(self):
        if self.stack_trace is None:
            return 0
        return len(self.stack_trace.stack_trace_elements)

    def __str__(self):
        s = self.name + '(' + str(self.thread_id) + ') ' \
            + "State: " + self.state \
            + " Blocking thread: " + self.get_blocker_name()
        s = str.encode(s, self.javacore.get_encoding(), 'ignore').decode('utf-8', 'ignore')
        return s

    def get_xml(self, doc, thread_snapshot_node):
        file_name = ""
        if self.file:
            file_name = self.javacore.filename.split(os.sep)[-1].strip()
        # thread name
        thread_name_node = doc.createElement("thread_name")
        thread_name_node.appendChild(doc.createTextNode(self.name))
        thread_snapshot_node.appendChild(thread_name_node)
        # thread id
        thread_name_node = doc.createElement("thread_id")
        thread_name_node.appendChild(doc.createTextNode(str(self.get_thread_id())))
        thread_snapshot_node.appendChild(thread_name_node)
        # thread hash
        thread_hash_node = doc.createElement("thread_hash")
        thread_hash_node.appendChild(doc.createTextNode(str(self.get_thread_hash())))
        thread_snapshot_node.appendChild(thread_hash_node)
        # CPU usage
        cpu_usage_node = doc.createElement("cpu_usage")
        cpu_usage_node.appendChild(doc.createTextNode(str(self.get_cpu_usage_inc())))
        thread_snapshot_node.appendChild(cpu_usage_node)
        # CPU percentage
        cpu_percentage_node = doc.createElement("cpu_percentage")
        cpu_percentage_node.appendChild(doc.createTextNode(str(self.get_cpu_percentage())))
        thread_snapshot_node.appendChild(cpu_percentage_node)
        # allocated memory
        allocated_memory_node = doc.createElement("allocated_memory")
        allocated_memory_node.appendChild(doc.createTextNode(str(self.allocated_mem)))
        thread_snapshot_node.appendChild(allocated_memory_node)
        # file name
        file_name_node = doc.createElement("file_name")
        file_name_node.appendChild(doc.createTextNode(file_name))
        thread_snapshot_node.appendChild(file_name_node)
        # state
        state_node = doc.createElement("state")
        state_node.appendChild(doc.createTextNode(self.state))
        thread_snapshot_node.appendChild(state_node)
        # timestamp
        timestamp_node = doc.createElement("timestamp")
        timestamp_node.appendChild(
            doc.createTextNode(datetime.fromtimestamp(self.javacore.timestamp).strftime('%d-%m-%y %H:%M:%S')))
        thread_snapshot_node.appendChild(timestamp_node)
        # elapsed time
        elapsed_time_node = doc.createElement("elapsed_time")
        elapsed_time_node.appendChild(doc.createTextNode(str(self.get_elapsed_time())))
        thread_snapshot_node.appendChild(elapsed_time_node)
        # java stack depth
        java_stack_depth_node = doc.createElement("java_stack_depth")
        java_stack_depth_node.appendChild(doc.createTextNode(str(self.get_java_stack_depth())))
        thread_snapshot_node.appendChild(java_stack_depth_node)
        # stack depth
        java_stack_depth_node = doc.createElement("stack_depth")
        java_stack_depth_node.appendChild(doc.createTextNode(str(self.get_stack_depth())))
        thread_snapshot_node.appendChild(java_stack_depth_node)
        # blocked by
        blocked_by_node = doc.createElement("blocked_by")

        # The line below left from historical reasons. This was the original line and I do not know if this node is used
        # anywhere or not.
        blocked_by_node.appendChild(doc.createTextNode(self.get_blocker_id()))

        blocked_by_node.setAttribute("thread_id", self.get_blocker_id())
        blocked_by_node.setAttribute("thread_hash", self.get_blocker_hash())
        blocked_by_node.setAttribute("name", self.get_blocker_name())
        thread_snapshot_node.appendChild(blocked_by_node)
        # blocking
        if len(self.blocking) > 0:
            blocking_node = doc.createElement("blocking")
            for thread in self.blocking:
                blocking_thread_node = doc.createElement("thread")
                blocking_thread_node.setAttribute("thread_id", thread.thread_id)
                blocking_thread_node.setAttribute("thread_hash", thread.get_thread_hash())
                blocking_thread_node.setAttribute("name", thread.name)
                blocking_node.appendChild(blocking_thread_node)
            thread_snapshot_node.appendChild(blocking_node)
        # stack
        i = 0
        if not self.stack_trace:
            empty_stack_node = doc.createElement("line")
            empty_stack_node.setAttribute("order", "none")
            empty_stack_node.appendChild(doc.createTextNode(StackTrace.EMPTY_STACK))
            thread_snapshot_node.appendChild(empty_stack_node)
        else:
            for el in self.stack_trace:
                line_node = doc.createElement("line")
                line_node.setAttribute("order", str(i))
                line_node.setAttribute("kind", str(el.get_kind_str()))
                line_node.appendChild(doc.createTextNode(el.get_line()))
                thread_snapshot_node.appendChild(line_node)
                i = i + 1
        return thread_snapshot_node

    def compute_elapsed_time(self):
        previous = self.get_previous_snapshot()
        if previous is None:
            self.elapsed_time = 0
        else:
            self.elapsed_time = self.javacore.timestamp - previous.javacore.timestamp

    def get_elapsed_time(self):
        if self.elapsed_time is None: self.compute_elapsed_time()
        return self.elapsed_time

    def compute_cpu_usage_inc(self):
        # gets the CPU usage increment since last snapshot
        previous = self.get_previous_snapshot()
        if previous is None:
            self.cpu_usage_inc = 0
        else:
            self.cpu_usage_inc = self.cpu_usage - previous.cpu_usage

    def get_cpu_usage_inc(self):
        if self.cpu_usage_inc is None: self.compute_cpu_usage_inc()
        return self.cpu_usage_inc

    def parse_stack_trace(self, line_in):
        stack_trace = StackTrace()
        line = line_in

        while True:
            if not line: break
            if line.startswith("NULL"): break
            if line.startswith(STACK_TRACE) or line.startswith(NATIVE_STACK_TRACE):
                stack_trace_element = StackTraceElement()
                if line.startswith(NATIVE_STACK_TRACE):
                    stack_trace_element.kind = StackTraceKind.NATIVE
                stack_trace_element.set_line(line)
                stack_trace.stack_trace_elements.append(stack_trace_element)
            line = self.file.readline()
        self.stack_trace = stack_trace
