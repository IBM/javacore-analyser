#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import unittest

from javacore_analyser.stack_trace import StackTrace
from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.stack_trace_kind import StackTraceKind


class TestStackTrace(unittest.TestCase):

    def setUp(self):
        self.equal_stack_trace_1 = StackTrace()
        list_with_stack_trace_lines = [
            '4XESTACKTRACE                at com/ibm/jvm/Dump.triggerDumpsImpl(Native Method)',
            '4XESTACKTRACE                at com/ibm/jvm/Dump.triggerDump(Dump.java:570)',
            '4XESTACKTRACE                at com/ibm/jvm/Dump.javaDumpToFile(Dump.java:236)',
            '4XESTACKTRACE                at sun/reflect/NativeMethodAccessorImpl.invoke0(Native Method)',
            '4XESTACKTRACE                at sun/reflect/NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:90(Compiled Code))',
            '4XESTACKTRACE                at sun/reflect/DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:55(Compiled Code))',
            '4XESTACKTRACE                at com/ibm/ws/kernel/launch/internal/ServerCommandListener.startListening(ServerCommandListener.java:315)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/launch/internal/FrameworkManager$4.run(FrameworkManager.java:763)',
            '4XENATIVESTACK               setup_native_thread+0x18a (omrintrospect.c:305, 0x00007FFF6C148A7A [j9prt29+0x28a7a])',
            '4XENATIVESTACK               omrintrospect_threads_startDo_with_signal+0x1ee (omrintrospect.c:410, 0x00007FFF6C14826E [j9prt29+0x2826e])']
        for line in list_with_stack_trace_lines:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.equal_stack_trace_1.stack_trace_elements.append(stack_trace_element)

        self.equal_stack_trace_2 = StackTrace()
        for line in list_with_stack_trace_lines:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.equal_stack_trace_2.stack_trace_elements.append(stack_trace_element)

        self.not_equal_stack_trace = StackTrace()
        list_with_stack_trace_lines_2 = [
            '4XESTACKTRACE                at com/ibm/jvm/Dump.triggerDumpsImpl(Native Method)',
            '4XESTACKTRACE                at com/ibm/jvm/Dump.dumpStoolToToilet(Dump.java:570)',
            '4XESTACKTRACE                at com/ibm/jvm/Dump.javaDumpToFile(Dump.java:236)',
            '4XESTACKTRACE                at sun/reflect/NativeMethodAccessorImpl.whyJavaSoSlow(Native Method)',
            '4XESTACKTRACE                at sun/reflect/NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:90(Compiled Code))',
            '4XESTACKTRACE                at sun/reflect/DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:55(Compiled Code))',
            '4XESTACKTRACE                at com/ibm/ws/kernel/launch/internal/ServerCommandListener.anyOneReadThisLinesPleaseLetMeKnowXD(ServerCommandListener.java:315)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/launch/internal/FrameworkManager$4.run(FrameworkManager.java:763)']
        for line in list_with_stack_trace_lines_2:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.not_equal_stack_trace.stack_trace_elements.append(stack_trace_element)

        self.equal_4_lines_stack_trace = StackTrace()
        list_with_stack_trace_lines_3 = [
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/Launcher.handleActions(Launcher.java:241)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/Launcher.createPlatform(Launcher.java:117)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/cmdline/EnvCheck.main(EnvCheck.java:59)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/cmdline/EnvCheck.main(EnvCheck.java:35)']
        for line in list_with_stack_trace_lines_3:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.equal_4_lines_stack_trace.stack_trace_elements.append(stack_trace_element)

        self.equal_4_lines_stack_trace_2 = StackTrace()
        for line in list_with_stack_trace_lines_3:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.equal_4_lines_stack_trace_2.stack_trace_elements.append(stack_trace_element)

        self.not_equal_4_lines_stack_trace = StackTrace()
        list_with_stack_trace_lines_4 = [
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/Launcher.handleActions(Launcher.java:241)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/Launcher.fakeCreatePlatform(Launcher.java:117)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/cmdline/EnvCheck.main(EnvCheck.java:59)',
            '4XESTACKTRACE                at com/ibm/ws/kernel/boot/cmdline/EnvCheck.mainMain(EnvCheck.java:35)']
        for line in list_with_stack_trace_lines_4:
            stack_trace_element = StackTraceElement()
            stack_trace_element.set_line(line)
            self.not_equal_4_lines_stack_trace.stack_trace_elements.append(stack_trace_element)

    def test_stack_traces_equal(self):
        result = self.equal_stack_trace_1.equals(self.equal_stack_trace_2)
        self.assertTrue(result)
        assert(len(self.equal_stack_trace_1.stack_trace_elements) == 10)
        assert(self.equal_stack_trace_1.stack_trace_elements[9].kind == StackTraceKind.NATIVE)

    def test_stack_traces_not_equal(self):
        result = self.equal_stack_trace_1.equals(self.not_equal_stack_trace)
        self.assertFalse(result)

    def test_stack_trace_equal_less_than_5_lines(self):
        result = self.equal_4_lines_stack_trace.equals(self.equal_4_lines_stack_trace_2)
        self.assertTrue(result)

    def test_stack_trace_not_equal_less_than_5_lines(self):
        result = self.equal_4_lines_stack_trace.equals(self.not_equal_4_lines_stack_trace)
        self.assertFalse(result)

    # see defect #253
    def test_short_stack_traces_one_longer_than_other(self):
        stack_trace_lines1 = \
            ['4XENATIVESTACK               setup_native_thread+0x18a (omrintrospect.c:305, 0x00007FFF6C148A7A [j9prt29+0x28a7a])',
            '4XENATIVESTACK               omrintrospect_threads_startDo_with_signal+0x1ee (omrintrospect.c:410, 0x00007FFF6C14826E [j9prt29+0x2826e])']
        stack_trace_lines2 = [stack_trace_lines1[0]]
        stack_trace1 = StackTrace()
        stack_trace1.stack_trace_elements.append(StackTraceElement(stack_trace_lines1[0]))
        stack_trace1.stack_trace_elements.append(StackTraceElement(stack_trace_lines1[1]))

        stack_trace2 = StackTrace()
        stack_trace2.stack_trace_elements.append(StackTraceElement(stack_trace_lines2[0]))

        self.assertFalse(stack_trace1.equals(stack_trace2))
        self.assertFalse(stack_trace2.equals(stack_trace1))



