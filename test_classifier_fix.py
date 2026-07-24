#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify that the ML classifier returns non-empty classifications
for all thread snapshots, including those with 'Unknown' state.
"""

import sys
import os
import io

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src and test to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'test'))

from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier

def test_classifier_classes():
    """Test that the classifier has no NaN classes."""
    print("Loading classifier...")
    classifier = JavacoreClassifier()
    
    print(f"\nLoaded {len(classifier.classes)} classes:")
    for idx, cls in enumerate(classifier.classes):
        print(f"  {idx}: {cls}")
    
    # Verify no empty or NaN classes
    empty_classes = []
    for idx, cls in enumerate(classifier.classes):
        if not cls or str(cls).strip() == "" or str(cls).lower() == "nan":
            empty_classes.append(idx)
    
    if empty_classes:
        print(f"\n[FAIL] Found {len(empty_classes)} empty/NaN classes at indices: {empty_classes}")
        return False
    else:
        print("\n[OK] All classes are valid (no NaN or empty strings)!")
        return True

def test_predictions_with_various_states():
    """Test predictions with various thread states."""
    print("\n" + "="*60)
    print("Testing predictions with various thread states...")
    print("="*60)
    
    classifier = JavacoreClassifier()
    
    test_cases = [
        ("R", "Running state"),
        ("CW", "Condition Wait state"),
        ("S", "Sleeping state"),
        ("Z", "Zombie state"),
        ("P", "Parked state"),
        ("B", "Blocked state"),
        ("Unknown", "Unknown state (invalid)"),
        ("UNKNOWN", "UNKNOWN state (invalid)"),
        ("Invalid", "Invalid state"),
    ]
    
    all_passed = True
    for state, description in test_cases:
        result = classifier.predict(
            name="Test Thread",
            cpu_usage=0.05,
            allocated_mem=1024000,
            state=state,
            blocking_threads=0,
            stack_trace="at java.lang.Thread.run(Thread.java:748)",
            stack_trace_depth=15
        )
        
        if not result or result.strip() == "":
            print(f"  [FAIL] {description} ({state}): EMPTY RESULT")
            all_passed = False
        else:
            print(f"  [OK] {description} ({state}): '{result}'")
    
    return all_passed

if __name__ == "__main__":
    print("ML Classifier Fix Verification")
    print("="*60)
    
    test1_passed = test_classifier_classes()
    test2_passed = test_predictions_with_various_states()
    
    print("\n" + "="*60)
    if test1_passed and test2_passed:
        print("[OK] ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("[FAIL] SOME TESTS FAILED")
        sys.exit(1)

# Made with Bob
