#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#
from javacore_analyser.abstract_snapshot_collection import AbstractSnapshotCollection
from javacore_analyser.properties import Properties
from javacore_analyser.stack_trace import StackTrace


class Thread(AbstractSnapshotCollection):

    def __init__(self):
        super().__init__()
        self.thread_address = ""

    def create(self, thread_snapshot):
        super().create(thread_snapshot)
        self.thread_address = thread_snapshot.thread_address

    def is_interesting(self):
        if self.get_total_cpu() > 0: return True
        if self.get_avg_mem() // (1024 * 1024) > 0: return True     # memory in megabytes
        if len(self.get_blocker_threads()) > 0: return True
        if len(self.get_blocking_threads()) > 0: return True
        if self.has_tall_stacks(): return True
        return False

    def get_hash(self):
        id_str = self.name + str(self.id)
        hashcode = abs(hash(id_str))
        return str(hashcode)

    def get_xml(self, doc):
        thread_node = super().get_xml(doc)

        thread_node.setAttribute("has_drill_down",
                                 str(self.is_interesting() or not Properties.get_instance().skip_boring))

        # thread ID
        id_node = doc.createElement("thread_id")
        id_node.appendChild(doc.createTextNode(str(self.id)))
        thread_node.appendChild(id_node)

        # thread name
        name_node = doc.createElement("thread_name")
        name_node.appendChild(doc.createTextNode(self.name + " (" + str(self.id) + ")"))
        thread_node.appendChild(name_node)

        # thread address
        thread_address_node = doc.createElement("thread_address")
        thread_address_node.appendChild(doc.createTextNode(self.thread_address))
        thread_node.appendChild(thread_address_node)

        # hash
        hash_node = doc.createElement("thread_hash")
        hash_node.appendChild(doc.createTextNode(self.get_hash()))
        thread_node.appendChild(hash_node)

        # continuous running states
        continuous_running_states_node = doc.createElement("continuous_running_states")
        continuous_running_states_node.appendChild(doc.createTextNode(str(self.get_continuous_running_states())))
        thread_node.appendChild(continuous_running_states_node)

        # stack trace
        i = 0
        for s in self.thread_snapshots:
            stack_trace_node = doc.createElement("stack")
            stack_trace_node.setAttribute("order", str(i))
            s.get_xml(doc, stack_trace_node)
            thread_node.appendChild(stack_trace_node)
            i = i + 1

        # blocking
        blockings_node = doc.createElement("blocking")
        for blocking in self.get_blocking_threads():
            blocking_node = doc.createElement("thread")
            blockings_node.appendChild(blocking_node)
            blocking_node.setAttribute("id", blocking.id)
            blocking_node.setAttribute("hash", blocking.get_hash())
            blocking_node.setAttribute("name", blocking.name)
        thread_node.appendChild(blockings_node)

        # blocker
        blockers_node = doc.createElement("blocker")
        for blocker in self.get_blocker_threads():
            blocker_node = doc.createElement("thread")
            blockers_node.appendChild(blocker_node)
            blocker_node.setAttribute("hash", blocker.get_hash())
            blocker_node.setAttribute("id", blocker.id)
            blocker_node.setAttribute("name", blocker.name)
        thread_node.appendChild(blockers_node)

        return thread_node

    def matches_snapshot(self, snapshot):
        return self.id == snapshot.thread_id and \
                self.name == snapshot.name

    def get_continuous_running_states(self):
        i = 0
        maxi = 0
        for snapshot in self.thread_snapshots:
            if snapshot.state == "R":
                i += 1
            else:
                if i > maxi: maxi = i
                i = 0
        if i > maxi: maxi = i
        return maxi

    # overrides the method from superclass
    # the overridden method also works correctly, but requires more setup
    # which makes the automated testing more challenging
    def compute_total_cpu(self):
        first_snapshot = self.thread_snapshots[0]
        last_snapshot = self.thread_snapshots[-1]
        self.total_cpu = last_snapshot.cpu_usage - first_snapshot.cpu_usage

    # overrides the method from superclass
    # the overridden method also works correctly, but requires more setup
    # which makes the automated testing more challenging
    def compute_total_time(self):
        first_snapshot = self.thread_snapshots[0]
        last_snapshot = self.thread_snapshots[-1]
        self.total_time = last_snapshot.get_timestamp() - first_snapshot.get_timestamp()

    def add(self, snapshot):
        super().add(snapshot)
        snapshot.thread = self

    # Returns all the threads which given thread is blocking over the time
    def get_blocking_threads(self):
        result = set()
        for s in self.thread_snapshots:
            for blocking in s.blocking:
                result.add(blocking.thread)
        return result

    # Returns all the threads which given thread is blocked by
    def get_blocker_threads(self):
        result = set()
        for s in self.thread_snapshots:
            if s.blocker:
                result.add(s.blocker.thread)
        return result

    def get_id(self):
        return self.get_hash()

    def has_tall_stacks(self):
        for snapshot in self.thread_snapshots:
            if snapshot.stack_trace and snapshot.stack_trace.get_java_stack_depth() > StackTrace.TRUNCATION_DEPTH:
                return True
        return False
