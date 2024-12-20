#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.constants import STACK_TRACE, NATIVE_STACK_TRACE
from javacore_analyser.stack_trace_kind import StackTraceKind


class StackTraceElement:

    def __init__(self, line=None):
        if line is None:
            self.line = None
            self.kind = StackTraceKind.JAVA
        else:
            self.set_line(line)

    def set_line(self, line):
        if line.startswith(STACK_TRACE):
            tokens = line.split('at ')
            self.line = ''.join(tokens[1])
        elif line.startswith(NATIVE_STACK_TRACE):
            line = line[len(NATIVE_STACK_TRACE):]
            line = line.strip()
            self.line = line
            self.kind = StackTraceKind.NATIVE

    def get_line(self):
        return self.line

    def get_kind_str(self):
        if self.kind == StackTraceKind.JAVA: return "java"
        if self.kind == StackTraceKind.NATIVE: return "native"
        return ""

    def equals(self, stack_trace_element):
        if self.line == stack_trace_element.get_line():
            return True
        return False
