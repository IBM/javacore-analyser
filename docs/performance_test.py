#!/usr/bin/env python3

#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Performance testing script to compare execution times of javacore_analyser_batch.py
"""
import subprocess
import time
import os

def run_command_with_timing(command, description):
    """Run a command and measure its execution time"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Exit code: {result.returncode}")
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
        
        print(f"Execution time: {elapsed_time:.2f} seconds")
        return elapsed_time, result.returncode == 0
    except subprocess.TimeoutExpired:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"TIMEOUT after {elapsed_time:.2f} seconds")
        return elapsed_time, False
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"ERROR: {e}")
        return elapsed_time, False

def main():
    # Check if waitData-reindex.zip exists
    waitdata_path = os.path.expanduser("~/Documents/waitdata/waitData-reindex.zip")
    waitdata_exists = os.path.exists(waitdata_path)
    
    # Define test commands (ordered as requested: 7z, directory, large ZIP)
    tests = [
        {
            'name': 'Test 1: 7z archive',
            'command': 'python src/javacore_analyser/javacore_analyser_batch.py test/data/archives/javacores.7z /tmp/javacores --use_ai=False',
            'skip': False
        },
        {
            'name': 'Test 2: Directory with javacores',
            'command': 'python src/javacore_analyser/javacore_analyser_batch.py test/data/javacores /tmp/javacores --use_ai=False',
            'skip': False
        },
        {
            'name': 'Test 3: Large ZIP archive (waitData-reindex.zip)',
            'command': f'python src/javacore_analyser/javacore_analyser_batch.py {waitdata_path} /tmp/javacores --use_ai=False',
            'skip': not waitdata_exists
        }
    ]
    
    if not waitdata_exists:
        print(f"WARNING: {waitdata_path} not found, skipping Test 1")
    
    # Run tests
    results = []
    for test in tests:
        if test.get('skip', False):
            continue
        elapsed, success = run_command_with_timing(test['command'], test['name'])
        results.append({
            'name': test['name'],
            'time': elapsed,
            'success': success
        })
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['name']}: {result['time']:.2f}s")
    
    total_time = sum(r['time'] for r in results)
    print(f"\nTotal execution time: {total_time:.2f}s")
    
    return results

if __name__ == '__main__':
    main()

# Made with Bob
