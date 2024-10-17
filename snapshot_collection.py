#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

class SnapshotCollection:

    def __init__(self):
        self.snapshots = []

    def add(self, snapshot):
        self.snapshots.append(snapshot)

    def size(self):
        return len(self.snapshots)

    def get(self, index):
        return self.snapshots[index]

    def get_threads_set(self):
        return {element.thread_id for element in self.snapshots}
