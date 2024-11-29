#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.abstract_snapshot_collection import AbstractSnapshotCollection
from javacore_analyser.stack_trace import StackTrace
from javacore_analyser.thread_snapshot import ThreadSnapshot


class CodeSnapshotCollection(AbstractSnapshotCollection):
    """
    returns the stack trace that is common for all the
    snapshots in this collection """

    def get_stack_trace(self):
        snapshot = self.thread_snapshots[0]  # they all have the same stack,
        # so we can just take the first one
        return snapshot.stack_trace

    """
    Returns list of the threads for which given stack appears
    """

    def get_threads(self):
        result = set()
        for snapshot in self.thread_snapshots:
            thread = snapshot.thread
            result.add(thread)
        return result

    def get_xml(self, doc):
        snapshot_collection_node = super().get_xml(doc)
        stack_strace = self.get_stack_trace()
        if not stack_strace:
            no_stack_node = doc.createElement('stack_trace0')
            no_stack_node.appendChild(doc.createTextNode(StackTrace.EMPTY_STACK))
            snapshot_collection_node.appendChild(no_stack_node)
        else:
            i = 0
            for el in stack_strace:
                stack_trace_element_node = doc.createElement('stack_trace' + str(i))
                stack_trace_element_node.appendChild(doc.createTextNode(el.line))
                snapshot_collection_node.appendChild(stack_trace_element_node)
                i += 1
                if i >= StackTrace.STACK_COMPARISON_DEPTH:
                    break

        threads_node = doc.createElement('threads')
        threads = self.get_threads()
        for thread in threads:
            thread_node = doc.createElement('thread')
            thread_node.setAttribute('id', thread.id)
            thread_node.setAttribute('name', thread.name)
            thread_node.setAttribute('hash', thread.get_hash())
            threads_node.appendChild(thread_node)
        snapshot_collection_node.appendChild(threads_node)

        return snapshot_collection_node

    # returns a dictionary representing this CodeSnapshotCollection object
    def matches_snapshot(self, snapshot: ThreadSnapshot):
        if not snapshot.stack_trace and not self.get_stack_trace():
            return True  # group anonymous native threads together
        if not snapshot.stack_trace or not self.get_stack_trace():
            return False  # group anonymous native threads together
        return snapshot.stack_trace.equals(self.get_stack_trace())
