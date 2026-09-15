#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# Property-based fuzz tests using Hypothesis.
#
# Exercises two high-risk parsing surfaces:
#   - StackTraceElement.set_line()  — arbitrary javacore text lines
#   - VerboseGcFile.__init__()      — arbitrary XML-like file content
#
# Run with:
#   PYTHONPATH=src:test python -m unittest test.test_hypothesis_fuzz
#

import os
import tempfile
import unittest

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from javacore_analyser.stack_trace_element import StackTraceElement
from javacore_analyser.verbose_gc import VerboseGcFile, GcVerboseProcessingException

# Any Unicode text that fits in a line (no surrogates, arbitrary length)
_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),  # exclude surrogates
    max_size=512,
)

# Larger blobs for file-level inputs
_file_content = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=8192,
)


class TestStackTraceElementHypothesis(unittest.TestCase):
    """Property: StackTraceElement.set_line() must never raise an unhandled exception
    for any Unicode input string."""

    @given(line=_text)
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_set_line_never_crashes(self, line):
        """Constructing a StackTraceElement from any string must not raise."""
        # No assertion about the result — we only care that it does not crash.
        StackTraceElement(line)

    @given(line=_text)
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_set_line_result_is_none_or_string(self, line):
        """get_line() must return either None or a str — never another type."""
        element = StackTraceElement(line)
        result = element.get_line()
        self.assertIsInstance(result, (str, type(None)),
                              f"get_line() returned unexpected type {type(result)!r} for input {line!r}")

    @given(line=_text)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_get_kind_str_always_valid(self, line):
        """get_kind_str() must always return one of the expected string values."""
        element = StackTraceElement(line)
        self.assertIn(element.get_kind_str(), ("java", "native", ""))


class TestVerboseGcFileHypothesis(unittest.TestCase):
    """Property: VerboseGcFile must either parse successfully or raise
    GcVerboseProcessingException — never any other exception."""

    @given(content=_file_content)
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_never_raises_unexpected_exception(self, content):
        """Parsing arbitrary file content must not propagate unexpected exceptions."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            VerboseGcFile(tmp_path)
        except GcVerboseProcessingException:
            # Expected for malformed content — not a bug.
            pass
        finally:
            os.unlink(tmp_path)

    @given(
        content=st.just(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<verbosegc xmlns=\"http://www.ibm.com/j9/verbosegc\" version=\"R29_Java8_SR8_FP5\">"
            "</verbosegc>"
        )
    )
    @settings(max_examples=1)
    def test_valid_empty_verbosegc_parses_without_exception(self, content):
        """A minimal valid verbosegc document must parse without any exception."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            VerboseGcFile(tmp_path)  # must not raise
        finally:
            os.unlink(tmp_path)

