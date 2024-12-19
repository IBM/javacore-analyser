#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.stack_trace_kind import StackTraceKind


class StackTrace:
    java_stack_depth: int
    EMPTY_STACK = "No stack"

    """
    how many first lines of the stack need to be equal
    in order to declare the entire stacks equal"""
    STACK_COMPARISON_DEPTH = 5

    def __init__(self):
        self.stack_trace_elements = []
        self.java_stack_depth = 0

    def append(self, element: StackTraceElement):
        self.stack_trace_elements.append(element)

    def __iter__(self):
        return self.stack_trace_elements.__iter__()

    # def __next__(self):
    #    return self.stack_trace_elements.__next__()

    def equals(self, stack_trace):
        self_stack_trace_size = len(self.stack_trace_elements)
        stack_trace_size = len(stack_trace.stack_trace_elements)
        if (StackTrace.STACK_COMPARISON_DEPTH >= min(self_stack_trace_size, stack_trace_size)) \
                and (self_stack_trace_size != stack_trace_size):
            return False
        for i, element in enumerate(self.stack_trace_elements):
            if i == StackTrace.STACK_COMPARISON_DEPTH:
                return True
            if element.equals(stack_trace.stack_trace_elements[i]):
                continue
            elif not element.equals(stack_trace.stack_trace_elements[i]):
                return False
        return True

    def get_java_stack_depth(self):
        filtered = filter(lambda e: e.kind == StackTraceKind.JAVA, self.stack_trace_elements)
        return len(list(filtered))
