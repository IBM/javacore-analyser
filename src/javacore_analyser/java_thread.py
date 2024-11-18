#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.abstract_snapshot_collection import AbstractSnapshotCollection


class Thread(AbstractSnapshotCollection):

    def get_hash(self):
        id_str = self.name + str(self.id)
        hashcode = abs(hash(id_str))
        return str(hashcode)

    def get_xml(self, doc):
        thread_node = super().get_xml(doc)

        # thread ID
        id_node = doc.createElement("thread_id")
        id_node.appendChild(doc.createTextNode(str(self.id)))
        thread_node.appendChild(id_node)

        # thread name
        name_node = doc.createElement("thread_name")
        name_node.appendChild(doc.createTextNode(self.name + " (" + str(self.id) + ")"))
        thread_node.appendChild(name_node)

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
