#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.ai.prompter import Prompter
from javacore_analyser.constants import GC_PAUSE_DETAIL_THRESHOLD


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
        cpu_usage_data: str = self._get_cpu_usage_over_time()
        
        # Collect memory information
        memory_info: str = self._get_memory_info()
        
        # Get application parameters
        app_params: str = self._get_application_parameters()
        
        # Get top CPU-consuming threads
        top_cpu_threads: str = self._get_top_cpu_threads(5)
        
        # Get top blocking threads
        top_blocking_threads: str = self._get_top_blocking_threads(5)
        
        # Get GC thread CPU usage
        gc_cpu_usage: str = self._get_gc_cpu_usage()
        
        # Get GC pause times
        gc_pause_times: str = self._get_gc_pause_times()
        
        # Get main thread stack trace
        main_thread_stack: str = self._get_main_thread_stack_trace()
        
        # Get shutdown status
        shutdown_status: str = self._get_shutdown_status()
        
        # Load the prompt template from file
        template: str = self._load_prompt_template('performance_recommendations_prompt.txt')
        
        # Format the template with collected data
        prompt: str = template.format(
            cpu_usage_data=cpu_usage_data,
            memory_info=memory_info,
            app_params=app_params,
            top_cpu_threads=top_cpu_threads,
            top_blocking_threads=top_blocking_threads,
            gc_cpu_usage=gc_cpu_usage,
            gc_pause_times=gc_pause_times,
            main_thread_stack=main_thread_stack,
            shutdown_status=shutdown_status
        )

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


    def _get_gc_pause_times(self):
        """
        Collects detailed GC pause time statistics including long pauses.
        For small datasets (< 100 pauses), shows individual pause times.
        For large datasets (>= 100 pauses), shows summary statistics.
        
        Returns:
            str: Formatted GC pause time information
        """
        if not self.javacore_set.gc_parser or not self.javacore_set.gc_parser.get_collects():
            return "No GC pause data available"
        
        collects = self.javacore_set.gc_parser.get_collects()
        if not collects:
            return "No GC collections recorded"
        
        # Threshold for switching between detailed and summary view
        if len(collects) < GC_PAUSE_DETAIL_THRESHOLD:
            # Show individual pause times with timestamps
            pause_details = []
            for collect in collects:
                pause_details.append(f"{collect.start_time_str}:{collect.duration:.0f}ms")
            return ", ".join(pause_details)
        else:
            # Show summary statistics for large datasets
            pause_times = [c.duration for c in collects]
            avg_pause = sum(pause_times) / len(pause_times)
            max_pause = max(pause_times)
            min_pause = min(pause_times)
            
            # Count pauses exceeding thresholds (1000ms and 2000ms)
            pauses_over_1s = sum(1 for p in pause_times if p > 1000)
            pauses_over_2s = sum(1 for p in pause_times if p > 2000)
            
            # Find the longest pause with timestamp
            longest_collect = max(collects, key=lambda c: c.duration)
            longest_pause_time = longest_collect.start_time_str
            
            pause_info = [
                f"Total GC pauses: {len(collects)}",
                f"Average GC pause: {avg_pause:.2f}ms",
                f"Min GC pause: {min_pause:.2f}ms",
                f"Max GC pause: {max_pause:.2f}ms at {longest_pause_time}",
                f"Pauses > 1000ms: {pauses_over_1s}",
                f"Pauses > 2000ms: {pauses_over_2s}"
            ]
            
            return ", ".join(pause_info)

    def _get_main_thread_stack_trace(self):
        """
        Retrieves the stack trace of the main thread from the most recent javacore.
        
        Returns:
            str: Formatted main thread stack trace or message if not found
        """
        if not self.javacore_set.javacores:
            return "No javacores available"
        
        # Get the most recent javacore (last one in the list)
        latest_javacore = self.javacore_set.javacores[-1]
        
        # Find the main thread
        main_thread = None
        for snapshot in latest_javacore.snapshots:
            if snapshot.name and "main" in snapshot.name.lower():
                main_thread = snapshot
                break
        
        if not main_thread:
            return "Main thread not found in javacore"
        
        # Extract stack trace
        if not main_thread.stack_trace or not main_thread.stack_trace.stack_trace_elements:
            return "Main thread has no stack trace"
        
        # Format stack trace (limit to first 20 lines for readability)
        stack_lines = []
        max_lines = 20
        for i, element in enumerate(main_thread.stack_trace.stack_trace_elements):
            if i >= max_lines:
                stack_lines.append(f"... ({len(main_thread.stack_trace.stack_trace_elements) - max_lines} more lines)")
                break
            # Format: at class.method(file:line)
            stack_lines.append(f"  at {element}")
        
        return "\n".join(stack_lines) if stack_lines else "Empty stack trace"

    def _get_shutdown_status(self):
        """
        Checks if the application is shutting down by detecting System.exit in any thread.
        
        Returns:
            str: Shutdown status message (CRITICAL if System.exit detected, OK otherwise)
        """
        if not self.javacore_set.javacores:
            return "Unknown - No javacores available"
        
        # Check all javacores for System.exit in any thread
        shutdown_detected = False
        shutdown_javacore = None
        shutdown_thread = None
        
        for javacore in self.javacore_set.javacores:
            # Check all threads in this javacore
            for snapshot in javacore.snapshots:
                # Check if stack trace contains System.exit
                if snapshot.stack_trace and snapshot.stack_trace.stack_trace_elements:
                    for element in snapshot.stack_trace.stack_trace_elements:
                        element_str = str(element)
                        if "System.exit" in element_str or "java.lang.System.exit" in element_str:
                            shutdown_detected = True
                            shutdown_javacore = javacore.basefilename()
                            shutdown_thread = snapshot.name if snapshot.name else "Unknown"
                            break
                if shutdown_detected:
                    break
            if shutdown_detected:
                break
        
        if shutdown_detected:
            return f"CRITICAL - Application is shutting down (System.exit detected in thread '{shutdown_thread}' in {shutdown_javacore})"
        else:
            return "OK - No shutdown detected"
