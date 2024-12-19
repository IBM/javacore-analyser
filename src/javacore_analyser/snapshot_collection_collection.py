#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
from tqdm import tqdm


class SnapshotCollectionCollection:

    def __init__(self, snapshot_collection_type):
        self.snapshot_collections = []
        self.highest_cpu = None
        self.highest_mem = None
        self.snapshot_collection_type = snapshot_collection_type

    def add_snapshot(self, snapshot):
        for snapshot_collection in self.snapshot_collections:
            if snapshot_collection.matches_snapshot(snapshot):
                snapshot_collection.add(snapshot)
                return
        snapshot_collection = self.snapshot_collection_type()
        snapshot_collection.create(snapshot)
        self.snapshot_collections.append(snapshot_collection)

    def __iter__(self):
        return self.snapshot_collections.__iter__()

    # def __next__(self):
    #    return self.snapshot_collections.__next__()

    def get_xml(self, doc):
        info_node = doc.createElement(self.snapshot_collection_type.__name__)

        all_threads_node = doc.createElement('all_snapshot_collection')
        info_node.appendChild(all_threads_node)
        for collection in tqdm(self.snapshot_collections, desc=" Generating threads data", unit=" thread"):
            all_threads_node.appendChild(collection.get_xml(doc))

        return info_node
