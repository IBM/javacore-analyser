#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.ai.prompter import Prompter
import javacore_analyser


class PerformanceRecommendationsPrompter(Prompter):
    """
    PerformanceRecommendationsPrompter generates a comprehensive prompt for LLM
    to analyze performance data and provide specific recommendations.
    
    This prompter collects and formats:
    - CPU usage over time
    - Memory usage and configuration
    - Top CPU-consuming threads
    - Top blocking threads
    - GC performance metrics
    """

    def construct_prompt(self):
        """
        Constructs a detailed performance analysis prompt with system metrics.
        
        Returns:
            str: Formatted prompt with performance data for LLM analysis
        """
        # Collect CPU usage over time from javacores
        cpu_usage_data = self._get_cpu_usage_over_time()
        
        # Collect memory information
        memory_info = self._get_memory_info()
        
        # Get application parameters
        app_params = self._get_application_parameters()
        
        # Get top CPU-consuming threads
        top_cpu_threads = self._get_top_cpu_threads(5)
        
        # Get top blocking threads
        top_blocking_threads = self._get_top_blocking_threads(5)
        
        # Get GC thread CPU usage
        gc_cpu_usage: str = self._get_gc_cpu_usage()
        
        # Construct the prompt
        prompt: str = f"""Context:
CPU usage of entire application over time: 
{cpu_usage_data}
Memory usage by the application: 
{memory_info}
Application parameters: 
{app_params}

Top threads using most of CPU: 
{top_cpu_threads}
Top 5 blocking threads: 
{top_blocking_threads}
GC Threads CPU usage: 
{gc_cpu_usage}

Based on that data search for potential bottlenecks and provide the recommendations how the performance can be improved.
Limit to maximum 5 recommendations.
Avoid providing generic recommendations, like using profilers.
If you do not find the recommendations, write that you do not have any recommendations."""

        return prompt

    def _get_cpu_usage_over_time(self):
        """
        Extracts CPU usage percentage from each javacore snapshot.
        
        Returns:
            str: Formatted string of CPU usage over time
        """
        if not self.javacore_set.javacores:
            return "No CPU data available"
        
        cpu_data = []
        for javacore in self.javacore_set.javacores:
            cpu_pct = javacore.get_cpu_percentage()
            timestamp = javacore.datetime.strftime("%Y-%m-%d %H:%M:%S") if javacore.datetime else "Unknown"
            cpu_data.append(f"{timestamp}: {cpu_pct:.2f}%")
        
        return ", ".join(cpu_data) if cpu_data else "No CPU data available"

    def _get_memory_info(self):
        """
        Collects memory usage information from javacores.
        
        Returns:
            str: Formatted memory usage information
        """
        memory_parts = []
        
        # Add heap configuration
        if self.javacore_set.xmx:
            memory_parts.append(f"Max heap (Xmx): {self.javacore_set.xmx}")
        if self.javacore_set.xms:
            memory_parts.append(f"Initial heap (Xms): {self.javacore_set.xms}")
        if self.javacore_set.xmn:
            memory_parts.append(f"Young generation (Xmn): {self.javacore_set.xmn}")
        
        # Add GC memory data if available
        if self.javacore_set.gc_parser and self.javacore_set.gc_parser.get_collects():
            collects = self.javacore_set.gc_parser.get_collects()
            if collects:
                avg_free_before = sum(int(c.free_before) for c in collects) / len(collects)
                avg_free_after = sum(int(c.free_after) for c in collects) / len(collects)
                memory_parts.append(f"Avg free before GC: {avg_free_before:.0f} bytes")
                memory_parts.append(f"Avg free after GC: {avg_free_after:.0f} bytes")
        
        return ", ".join(memory_parts) if memory_parts else "No memory data available"

    def _get_application_parameters(self):
        """
        Collects application configuration parameters.
        
        Returns:
            str: Formatted application parameters
        """
        params = []
        
        if self.javacore_set.number_of_cpus:
            params.append(f"CPUs: {self.javacore_set.number_of_cpus}")
        if self.javacore_set.gc_policy:
            params.append(f"GC Policy: {self.javacore_set.gc_policy}")
        if self.javacore_set.compressed_refs:
            params.append(f"Compressed References: {self.javacore_set.compressed_refs}")
        if self.javacore_set.java_version:
            params.append(f"Java Version: {self.javacore_set.java_version}")
        if self.javacore_set.os_level:
            params.append(f"OS: {self.javacore_set.os_level}")
        if self.javacore_set.cmd_line: 
            params.append(f"Command Line: {self.javacore_set.cmd_line}")
        
        return ", ".join(params) if params else "No parameter data available"

    def _get_top_cpu_threads(self, count=5):
        """
        Gets the top N threads by CPU usage.
        
        Args:
            count: Number of top threads to return
            
        Returns:
            str: Formatted list of top CPU-consuming threads
        """
        if not self.javacore_set.threads or not self.javacore_set.threads.snapshot_collections:
            return "No thread CPU data available"
        
        # Get all threads and sort by total CPU
        all_threads = self.javacore_set.threads.snapshot_collections
        sorted_threads = sorted(all_threads, key=lambda t: t.get_total_cpu(), reverse=True)
        
        top_threads = []
        for i, thread in enumerate(sorted_threads[:count]):
            cpu: float = thread.get_total_cpu() / thread.get_total_time() * 100
            if cpu > 0:  # Only include threads with CPU usage
                # Get top of stack trace if available
                stack_top = "No stack trace available" #TODO share the stack trace in the future
                if thread.thread_snapshots and len(thread.thread_snapshots) > 0:
                    snapshot = thread.thread_snapshots[0]
                    if hasattr(snapshot, 'stack') and snapshot.stack and len(snapshot.stack.elements) > 0:
                        stack_top = snapshot.stack.elements[0].method if hasattr(snapshot.stack.elements[0], 'method') else str(snapshot.stack.elements[0])
                
                top_threads.append(f"{i+1}. {thread.name} (ID: {thread.id}): CPU={cpu:.2f}%, Stack top: {stack_top}")
        
        return "\n".join(top_threads) if top_threads else "No threads with significant CPU usage"

    def _get_top_blocking_threads(self, count=5):
        """
        Gets the top N blocking threads.
        
        Args:
            count: Number of top blocking threads to return
            
        Returns:
            str: Formatted list of top blocking threads
        """
        if not self.javacore_set.blocked_snapshots:
            return "No blocking thread data available"
        
        # Count how many threads each blocker is blocking
        blocker_counts = {}
        blocked_data = self.javacore_set.blocked_snapshots
        for blocked_collection in blocked_data:
            blocked_collection_snapshots = blocked_collection.snapshots
            if len(blocked_collection_snapshots) > 0:
                blocker = blocked_collection_snapshots[0].blocker
                if blocker and blocker.thread:
                    blocker_id = blocker.thread.id
                    blocker_name: str = blocker.name
                    blocked_count: int = len(blocker.blocking)
                    
                    if blocker_id not in blocker_counts:
                        blocker_counts[blocker_id] = {
                            'name': blocker_name,
                            'id': blocker_id,
                            'count': 0
                        }
                    blocker_counts[blocker_id]['count'] += blocked_count
        
        # Sort by number of blocked threads
        sorted_blockers = sorted(blocker_counts.values(), key=lambda x: x['count'], reverse=True)
        
        top_blockers = []
        for i, blocker in enumerate(sorted_blockers[:count]):
            top_blockers.append(f"{i+1}. {blocker['name']} (ID: {blocker['id']}): Blocking {blocker['count']} thread(s)")
        
        return "\n".join(top_blockers) if top_blockers else "No blocking threads found"

    def _get_gc_cpu_usage(self):
        """
        Calculates GC-related CPU usage and metrics.
        
        Returns:
            str: Formatted GC CPU usage information
        """
        if not self.javacore_set.gc_parser or not self.javacore_set.gc_parser.get_collects():
            return "No GC data available"
        
        collects = self.javacore_set.gc_parser.get_collects()
        if not collects:
            return "No GC collections recorded"
        
        # Calculate GC statistics
        total_duration = sum(c.duration for c in collects)
        avg_duration = total_duration / len(collects)
        max_duration = max(c.duration for c in collects)
        
        gc_info = [
            f"Total GC collections: {len(collects)}",
            f"Average GC duration: {avg_duration:.2f}ms",
            f"Max GC duration: {max_duration:.2f}ms",
            f"Total GC time: {total_duration:.2f}ms"
        ]
        
        return ", ".join(gc_info)

# Made with Bob
