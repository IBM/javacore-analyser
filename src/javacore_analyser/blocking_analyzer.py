#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging

from javacore_analyser.snapshot_collection import SnapshotCollection


class BlockingAnalyzer:
    """Analyses thread blocking relationships within a set of javacore snapshots.

    Builds the blocked_snapshots list on a JavacoreAnalyzer (or JavacoreSet) instance
    by walking all javacore snapshots and recording which threads are blocked and by whom.
    """

    @staticmethod
    def blocked_collection(blocked_snapshots, blocker):
        """Return the SnapshotCollection for *blocker*, or None if not found.

        Args:
            blocked_snapshots (list): The current list of SnapshotCollection objects.
            blocker: The blocking thread snapshot to look up.

        Returns:
            SnapshotCollection or None
        """
        if blocker:
            for snapshot_collection in blocked_snapshots:
                if snapshot_collection.size() > 0:
                    if snapshot_collection.get(0).get_blocker().thread_id == blocker.thread_id:
                        return snapshot_collection
        return None

    @staticmethod
    def generate_blocked_snapshots_list(javacore_analyzer):
        """Populate javacore_analyzer.blocked_snapshots from its javacores.

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance with
                ``javacores`` and ``blocked_snapshots`` attributes.
        """
        for javacore in javacore_analyzer.javacores:
            for snapshot in javacore.snapshots:
                blocker = snapshot.get_blocker()
                if blocker:
                    blocked = BlockingAnalyzer.blocked_collection(javacore_analyzer.blocked_snapshots, blocker)
                    if not blocked:
                        blocked = SnapshotCollection()
                        javacore_analyzer.blocked_snapshots.append(blocked)
                    blocked.add(snapshot)
                    blocker.blocking.add(snapshot)
        javacore_analyzer.blocked_snapshots.sort(
            reverse=True, key=lambda collection: len(collection.get_threads_set())
        )

    @staticmethod
    def print_blockers(javacore_analyzer):
        """Log debug information about blocking threads.

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance with a
                ``blocked_snapshots`` attribute.
        """
        logging.debug("List of blockers")
        for blocked in javacore_analyzer.blocked_snapshots:
            logging.debug(blocked.get(0).blocker.name + ": " + str(blocked.size()))
