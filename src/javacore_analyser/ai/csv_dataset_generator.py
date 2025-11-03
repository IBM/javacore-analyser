#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import sys

import pandas as pd

from javacore_analyser.javacore_analyser_batch import generate_javecore_set_data


def main(input_files):
    """
    Generates data.csv files with input parameters which can be used for a model.

    This function processes one or more javacore files (or archives with javacores) and generates a csv file named 'data.csv'.
    It extracts various parameters from the javacore data such as thread name, CPU usage, allocated memory, state, number of blocking threads, and stack trace.

    :param input_files: one or more javacore files (or archives with javacores) from which to generate csv file
    :return: No value returned. Generates csv file 'data.csv'
    """
    javacore_set = generate_javecore_set_data(input_files)
    data = []
    for thread in javacore_set.threads:
        for snapshot in thread.thread_snapshots:
            name = snapshot.name
            cpu_usage = snapshot.cpu_usage
            allocated_mem = snapshot.allocated_mem
            state = snapshot.state
            blocking_threads = len(snapshot.blocking)
            stack_trace = snapshot.stack_trace
            stack_trace_depth = snapshot.get_java_stack_depth()
            if stack_trace is None:
                stack_trace = ""
            else:
                stack_trace = stack_trace.to_string().replace("\n", " ").replace("\r", " ")
            data.append({'name': name, 'cpu_usage': cpu_usage, 'allocated_mem': allocated_mem, 'state': state,
                         'blocking_threads': blocking_threads, 'stack_trace': stack_trace,
                         'stack_trace_depth': stack_trace_depth})
    data.sort(key = lambda java_thread : len(java_thread['stack_trace']), reverse=True)
    pd.DataFrame.from_records(data).to_csv('data.csv', index=False)

    # Check if we can load data
    df = pd.read_csv('data.csv')
    print("Displaying data:")
    print(df)


if __name__ == '__main__':
    main(sys.argv[1:])
