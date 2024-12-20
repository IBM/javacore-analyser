#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import logging

# This is a module containing list of the tips.
# Each tip has to implement dynamic method generate(javacore_set)

# List of the tips on which run the tool
TIPS_LIST = ["DifferentIssuesTip", "ExcludedJavacoresTip", "InvalidAccumulatedCpuTimeTip", "TooFewJavacoresTip",
             "OOMEGenerationTip", "BlockingThreadsTip", "HighCpuUsageTip"]


class TestTip:
    # This is tip for testing purposes

    @staticmethod
    def generate(javacore_set):
        logging.info(javacore_set)
        return ["this is a test tip. Ignore it."]


class InvalidAccumulatedCpuTimeTip:
    # Usually the javacores should not have thread with accumulated CPU time < 0ms

    ONE_BAD_THREAD_WARNING = '''[WARNING] The CPU usage data is invalid for thread \"{0}\". 
                              Probably one or more javacore files are corrupted.'''

    MANY_THREADS_WARNING = '''[WARNING] {0} threads have invalid accumulated CPU. 
                                Probably one or more javacore files are corrupted.'''

    @staticmethod
    def generate(javacore_set):
        bad_thread = []
        for thread in javacore_set.threads.snapshot_collections:
            if thread.get_total_cpu() < 0:
                bad_thread.append(thread)
        if bad_thread:
            if len(bad_thread) == 1:
                # only 1 bad thread, display it thread name
                return [InvalidAccumulatedCpuTimeTip.ONE_BAD_THREAD_WARNING.format(bad_thread[0].name)]
            else:
                # more than 1 bad threads, display the number of bad threads
                return [InvalidAccumulatedCpuTimeTip.MANY_THREADS_WARNING.format(len(bad_thread))]
        else:
            return []  # if nothing wrong


class OOMEGenerationTip:
    # Tip generated when one of Javacores is generated on OOME, not by user

    SIG_INFO_TEXT = '''[WARNING] The Javacore {0} is generated on OutOfMemoryError.
    The signal that triggered the javacore: <<<{1}>>>.
    You may need another tool, like Memory Analyzer Tool, to troubleshoot the issue'''

    OUT_OF_MEMORY_ERROR = 'OutOfMemoryError'

    @staticmethod
    def generate(javacore_set):
        for jc in javacore_set.javacores:
            siginfo = jc.siginfo
            if OOMEGenerationTip.OUT_OF_MEMORY_ERROR in siginfo:
                msg = OOMEGenerationTip.SIG_INFO_TEXT.format(jc.basefilename(), jc.siginfo)
                return [msg]
        return []  # no issues with generation signal. Returning empty tip


class DifferentIssuesTip:
    # Usually the javacores should be gathered in max 1-2 minute intervals.
    # If the interval is higher, then it is probably from different issue.

    MAX_INTERVAL_FOR_JAVACORES = 330  # 330 seconds (5 minutes and a little more time)
    DIFFERENT_ISSUES_MESSAGE = """[WARNING] The time interval between javacore {0} and {1} is {2:.0f} seconds, while 
    the recommended maximum interval between two javacores is 300 seconds (5 minutes). It is likely that these
    two javacores do not correspond to one occurrence of a single issue. Please review the list of javacores received 
    from the customer and run WAIT2 only against the ones that are applicable for the issue you are investigating. """

    @staticmethod
    def generate(javacore_set):
        previous_jc = None
        max_interval = 0
        max_interval_previous_jc_base_filename = 0
        max_interval_jc_base_filename = ""
        for jc in javacore_set.javacores:
            if previous_jc is not None:
                interval = jc.timestamp - previous_jc.timestamp
                if interval > max_interval:
                    max_interval = interval
                    max_interval_previous_jc_base_filename = previous_jc.basefilename()
                    max_interval_jc_base_filename = jc.basefilename()
            previous_jc = jc
        if max_interval > DifferentIssuesTip.MAX_INTERVAL_FOR_JAVACORES:
            msg = DifferentIssuesTip.DIFFERENT_ISSUES_MESSAGE.format(max_interval_previous_jc_base_filename,
                                                                     max_interval_jc_base_filename, max_interval)
            return [msg]
        else:
            return []


class TooFewJavacoresTip:
    # Generates the tip if the number of Javacores is too small.

    MIN_NUMBER_OF_JAVACORES = 10

    ONE_JAVACORE_WARNING = '''[WARNING] You generated this WAIT2 report with only one javacore. 
                                CPU usage calculation is not possible.'''

    NOT_ENOUGH_JAVACORES_MESSAGE = """[WARNING] You ran the tool against {0} Javacores. The analysis 
    might not be reliable. The minimal number of Javacores should be 5. The recommended number of Javacores 
    is at least 10."""

    @staticmethod
    def generate(javacore_set):
        jc_number = len(javacore_set.javacores)
        if jc_number == 1:
            return [TooFewJavacoresTip.ONE_JAVACORE_WARNING]
        elif jc_number < TooFewJavacoresTip.MIN_NUMBER_OF_JAVACORES:
            return [TooFewJavacoresTip.NOT_ENOUGH_JAVACORES_MESSAGE.format(jc_number)]
        else:
            return []


class ExcludedJavacoresTip:
    # Generates the tip if we excluded some javacores

    SMALL_SIZE_JAVACORES = """[WARNING] The file {0} has very small size of {1} bytes. It is probably corrupted.
     It has been excluded from processing."""

    @staticmethod
    def generate(javacore_set):
        result = []
        for excluded in javacore_set.excluded_javacores:
            result.append(excluded["reason"])
        return result


class BlockingThreadsTip:
    # Generates the tip that one or more threads are blocking many another threads

    BLOCKING_THREADS_TEXT = """[TIP] a thread \"{0}\" is blocking on average {1:.1f} another threads per javacore. 
    This lock might cause performance degradation."""

    MAX_BLOCKING_THREADS_NO = 5

    @staticmethod
    def generate(javacore_set):
        javacores_no = len(javacore_set.javacores)
        result = []
        for blocked in javacore_set.blocked_snapshots:
            blocked_size = len(blocked.get_threads_set())
            blocker_name = blocked.get(0).blocker.name

            """ 
            Explicitly deciding, that if the threads blocks more threads totally, than there are javacores,
            then this is potential blocker.
            """
            if blocked_size > javacores_no:
                result.append(BlockingThreadsTip.BLOCKING_THREADS_TEXT.format(blocker_name,
                                                                              blocked_size / javacores_no))
                if len(result) >= BlockingThreadsTip.MAX_BLOCKING_THREADS_NO:
                    break
        return result


class HighCpuUsageTip:
    # Generates the tip if the thread is using above x percent of CPU. Also informs, if this is verbose gc thread.

    # Report as high cpu usage for the application using the cpu usage above this value
    CRITICAL_CPU_USAGE = 50

    CRITICAL_USAGE_FOR_GC = 5

    MAX_NUMBER_OF_HIGH_CPU_USAGE_THREADS = 5

    HIGH_CPU_USAGE_TEXT = """[TIP] The following thread is using {0:.0f}% CPU: \"{1}\". 
    This thread might cause performance issues. Consider checking what this thread is doing"""

    HIGH_GC_USAGE_TEXT = """[TIP] The verbose GC threads are using high CPU. You are likely having memory issues. 
    Consider revieving verbose GC for further investigation."""

    @staticmethod
    def generate(javacore_set):
        has_gc_performance_issues = False
        high_blocking_threads_no = 0
        result = []
        threads = javacore_set.threads.snapshot_collections
        threads = sorted(threads, key=lambda t: -t.get_cpu_percentage_usage())
        for thread in threads:
            cpu_percent_usage = thread.get_cpu_percentage_usage()
            thread_name = thread.name
            if "GC Slave" in thread_name or "GC Worker" in thread_name:
                if cpu_percent_usage > HighCpuUsageTip.CRITICAL_USAGE_FOR_GC:
                    has_gc_performance_issues = True
            else:
                if cpu_percent_usage > HighCpuUsageTip.CRITICAL_CPU_USAGE:
                    if high_blocking_threads_no < HighCpuUsageTip.MAX_NUMBER_OF_HIGH_CPU_USAGE_THREADS:
                        result.append(HighCpuUsageTip.HIGH_CPU_USAGE_TEXT.format(cpu_percent_usage, thread_name))
                        high_blocking_threads_no += 1
                    else:
                        continue

        if has_gc_performance_issues:
            result.append(HighCpuUsageTip.HIGH_GC_USAGE_TEXT)
        return result
