#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import abc


class AbstractSnapshotCollection(abc.ABC):

    def __init__(self):
        self.name = None
        self.id = None
        self.total_cpu = 0
        self.total_time = 0
        self.avg_mem = 0
        self.avg_memory = 0
        self.thread_snapshots = []

    def create(self, thread_snapshot):
        self.name = thread_snapshot.name
        self.id = thread_snapshot.thread_id
        self.add(thread_snapshot)

    def get_xml(self, doc):
        snapshot_collection_node = doc.createElement('snapshot_collection')
        # total CPU usage
        total_cpu_usage_node = doc.createElement('total_cpu_usage')
        total_cpu_usage_node.appendChild(doc.createTextNode(str(self.get_total_cpu())))
        snapshot_collection_node.appendChild(total_cpu_usage_node)
        # total time
        total_time_node = doc.createElement('total_time')
        total_time_node.appendChild(doc.createTextNode(str(self.get_total_time())))
        snapshot_collection_node.appendChild(total_time_node)
        # CPU percentage
        cpu_percentage_node = doc.createElement('cpu_percentage')
        cpu_percentage_node.appendChild(doc.createTextNode(str(self.get_cpu_percentage_usage())))
        snapshot_collection_node.appendChild(cpu_percentage_node)
        # average memory
        average_memory_node = doc.createElement('average_memory')
        average_memory_node.appendChild(doc.createTextNode(str(self.get_avg_mem())))
        snapshot_collection_node.appendChild(average_memory_node)
        # maximum java stack depth
        max_java_stack_depth_node = doc.createElement('max_java_stack_depth')
        max_java_stack_depth_node.appendChild(doc.createTextNode(str(self.max_java_stack_trace_depth())))
        snapshot_collection_node.appendChild(max_java_stack_depth_node)
        # average java stack depth
        average_stack_depth_node = doc.createElement('average_stack_depth')
        average_stack_depth_node.appendChild(doc.createTextNode(str(self.avg_java_stack_trace_depth())))
        snapshot_collection_node.appendChild(average_stack_depth_node)
        #
        return snapshot_collection_node

    @abc.abstractmethod
    def matches_snapshot(self, snapshot):
        pass

    def add(self, snapshot):
        self.thread_snapshots.append(snapshot)

    def index_of(self, snapshot):
        for i in range(len(self.thread_snapshots)):
            if self.thread_snapshots[i] == snapshot: return i
        return -1

    def is_empty(self):
        return len(self.thread_snapshots) == 0

    def sort_snapshots(self):
        i = 0
        while i <= len(self.thread_snapshots) - 2:
            if self.thread_snapshots[i].get_timestamp() > self.thread_snapshots[i + 1].get_timestamp():
                s = self.thread_snapshots[i]
                self.thread_snapshots[i] = self.thread_snapshots[i + 1]
                self.thread_snapshots[i + 1] = s
                i = 0
            else:
                i += 1

    def calculate_snapshot_states(self):
        snapshot_states = {}
        for snapshot in self.thread_snapshots:
            state = snapshot.state
            if snapshot_states.keys().__contains__(state):
                snapshot_states[snapshot.state] += 1
            else:
                snapshot_states[snapshot.state] = 1
        return snapshot_states

    def get_snapshot_states(self):
        s = ""
        snapshot_states = self.calculate_snapshot_states()
        keys = snapshot_states.keys()
        for key in keys:
            s += key + ": " + str(snapshot_states[key]) + ";"
        return s

    def get_total_cpu(self):
        if not self.total_cpu:
            self.compute_total_cpu()
        return self.total_cpu

    def compute_total_cpu(self):
        total_cpu_time = 0
        for snapshot in self.thread_snapshots:
            previous_snapshot = snapshot.get_previous_snapshot()
            if previous_snapshot:
                total_cpu_time += snapshot.cpu_usage - previous_snapshot.cpu_usage
        self.total_cpu = total_cpu_time

    def compute_total_time(self):
        total_time = 0
        for snapshot in self.thread_snapshots:
            previous_snapshot = snapshot.get_previous_snapshot()
            if previous_snapshot:
                total_time += snapshot.get_timestamp() - previous_snapshot.get_timestamp()
        self.total_time = total_time

    def get_total_time(self):
        if not self.total_time:
            self.compute_total_time()
        return self.total_time

    def get_cpu_percentage_usage(self):
        if self.get_total_time() > 0:
            return 100 * self.get_total_cpu() / self.get_total_time()
        else:
            return 0

    def compute_avg_mem(self):
        mem_sum = 0
        for snapshot in self.thread_snapshots:
            mem_sum += snapshot.allocated_mem
        self.avg_mem = mem_sum / len(self.thread_snapshots)

    def get_avg_mem(self):
        if not self.avg_mem:
            self.compute_avg_mem()
        return self.avg_mem

    def max_java_stack_trace_depth(self):
        result = 0
        for i in self.thread_snapshots:
            el = i.get_java_stack_depth()
            if el > result:
                result = el
        return result

    def avg_java_stack_trace_depth(self):
        total = 0
        count = 0
        for i in self.thread_snapshots:
            el = i.get_java_stack_depth()
            total += el
            count += 1
        return total/count

    def get_id(self):
        return self.id
