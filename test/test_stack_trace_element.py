#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import unittest

from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.stack_trace_kind import StackTraceKind


class TestStackTraceElement(unittest.TestCase):

    def test_add_element(self):
        element = StackTraceElement()
        assert(element.kind == StackTraceKind.JAVA)
        line = '4XENATIVESTACK               setup_native_thread+0x18a (omrintrospect.c:305, 0x00007FFF6C148A7A [j9prt29+0x28a7a])'
        element.set_line(line)
        assert(element.kind == StackTraceKind.NATIVE)

    def test_get_kind_str(self):
        element = StackTraceElement()
        assert(element.get_kind_str() == "java")
        element.kind = StackTraceKind.JAVA
        assert (element.get_kind_str() == "java")
        element.kind = StackTraceKind.NATIVE
        assert (element.get_kind_str() == "native")
