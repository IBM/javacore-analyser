#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Unit tests for JavacoreClassifier — correctness and performance.
"""

import time
import unittest

from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier


class TestJavacoreClassifier(unittest.TestCase):
    """Tests for JavacoreClassifier.predict() correctness and performance."""

    @classmethod
    def setUpClass(cls):
        """Load the model once for the entire test class to avoid repeated I/O overhead."""
        cls.classifier = JavacoreClassifier()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _predict(self, **kwargs) -> str:
        """Call predict() with sensible defaults, overridden by kwargs."""
        defaults = dict(
            name="WebContainer : 5",
            cpu_usage=0.05,
            allocated_mem=1024000,
            state="R",
            blocking_threads=0,
            stack_trace="at java.lang.Thread.run(Thread.java:748)",
            stack_trace_depth=15,
        )
        defaults.update(kwargs)
        return self.classifier.predict(**defaults)

    # ------------------------------------------------------------------
    # Correctness tests
    # ------------------------------------------------------------------

    def test_predict_returns_nonempty_string(self):
        """predict() should return a non-empty string for normal inputs."""
        result = self._predict()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_predict_none_stack_trace(self):
        """predict() should handle None stack_trace without error."""
        result = self._predict(stack_trace=None)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_predict_nan_stack_trace(self):
        """predict() should handle float('nan') stack_trace without error."""
        result = self._predict(stack_trace=float("nan"))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_predict_comma_cpu_usage(self):
        """predict() should handle a comma-delimited CPU usage string."""
        result = self._predict(cpu_usage="0,05")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_predict_unrecognised_state(self):
        """predict() should return a valid result for an unrecognised thread state."""
        result = self._predict(state="UNKNOWN")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    # ------------------------------------------------------------------
    # Performance test  (Fixes #305)
    # ------------------------------------------------------------------

    def test_predict_performance(self):
        """A single predict() call must complete in under 2 seconds.

        The optimised path (pre-compiled regexes + numpy feature vector) runs
        ~18 ms on typical hardware. This guard catches regressions back toward
        the original ~490 ms pandas-based implementation.

        Fixes Profile classify_javacore.inference.py.predict_thread_snapshot #305
        """
        start = time.perf_counter()
        self._predict()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0, f"predict() took {elapsed:.3f}s — performance regression detected")
