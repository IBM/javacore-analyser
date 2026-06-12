#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Local test/demo code for the Javacore thread function classifier.

This module contains example usage that was previously embedded in
classify_javacore_inference.py.
"""

import traceback

import pandas as pd

from javacore_analyser.javacore_analyser_batch import generate_javecore_set_data
from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier


def main():
    """
    Example usage of the JavacoreClassifier.
    Loads sample data and runs prediction on the first row.

    ONLY RUN FOR LOCAL TESTING
    """
    print("=" * 60)
    print("Javacore Thread Function Classifier - Example Usage")
    print("=" * 60)

    # Load sample data
    filename_data = 'test/data/ml/ML_test_data.csv'
    try:
        data = pd.read_csv(filename_data, sep=';', index_col=0)
        print(f"\n✓ Loaded sample data from {filename_data}")
        print(f"  Dataset shape: {data.shape}")
    except FileNotFoundError:
        print(f"\n✗ Sample data file not found: {filename_data}")
        print("  Please ensure the data file exists in the current directory.")
        return

    # Initialize classifier
    try:
        print("\n" + "-" * 60)
        print("Initializing classifier...")
        classifier = JavacoreClassifier()
        print("✓ Classifier initialized successfully")
        print(f"  - Model loaded from: {classifier.model_path}")
        print(f"  - Thread name vocabulary size: {len(classifier.tn_vocabulary)}")
        print(f"  - Stack trace vocabulary size: {len(classifier.st_vocabulary)}")
    except Exception as e:
        print(f"\n✗ Error initializing classifier: {e}")
        return

    # Select sample row
    sample_row = 3711
    print("\n" + "-" * 60)
    print(f"Running prediction on row {sample_row}...")

    # Extract sample data
    sample_name = data['name'].iloc[sample_row]
    sample_cpu_usage = data['cpu_usage'].iloc[sample_row]
    sample_allocated_mem = data['allocated_mem'].iloc[sample_row]
    sample_state = data['state'].iloc[sample_row]
    sample_blocking_threads = data['blocking_threads'].iloc[sample_row]
    sample_stack_trace = data['stack_trace'].iloc[sample_row]
    sample_stack_trace_depth = data['stack_trace_depth'].iloc[sample_row]
    print("\nInput parameters:")
    print(f"  - Name: {sample_name}")
    print(f"  - CPU Usage: {sample_cpu_usage}")
    print(f"  - Allocated Memory: {sample_allocated_mem}")
    print(f"  - State: {sample_state}")
    print(f"  - Blocking Threads: {sample_blocking_threads}")
    print(f"  - Stack Trace Depth: {sample_stack_trace_depth}")
    if isinstance(sample_stack_trace, str) and len(sample_stack_trace) > 100:
        print(f"  - Stack Trace: {sample_stack_trace[:100]}...")
    else:
        print(f"  - Stack Trace: {sample_stack_trace}")

    # Run prediction
    try:
        predicted_function = classifier.predict(
            name=sample_name,
            cpu_usage=sample_cpu_usage,
            allocated_mem=sample_allocated_mem,
            state=sample_state,
            blocking_threads=sample_blocking_threads,
            stack_trace=sample_stack_trace,
            stack_trace_depth=sample_stack_trace_depth
        )
        print("\n" + "=" * 60)
        print(f"✓ PREDICTION RESULT: {predicted_function}")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error during prediction: {e}")
        traceback.print_exc()

    # Test with ThreadSnapshot
    input_files = [
        "./test/data/javacores/javacore.20220606.114458.32888.0001.txt",
        "./test/data/javacores/javacore.20220606.114502.32888.0002.txt"
    ]
    print(f"Opening: {input_files}")
    javacore_set = generate_javecore_set_data(input_files)

    for thread in javacore_set.threads:
        for snapshot in thread.thread_snapshots:
            print("\n" + "=" * 60)
            print(f"Running prediction on thread:\n {snapshot.name}")
            try:
                predicted_function = classifier.predict_thread_snapshot(snapshot)
                print("-" * 60)
                print(f"✓ PREDICTION RESULT: {predicted_function}")
                print("=" * 60)
            except Exception as e:
                print(f"\n✗ Error during prediction: {e}")
                traceback.print_exc()


if __name__ == "__main__":
    main()

# Made with Bob
