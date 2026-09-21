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
# How it works
# ------------
# Hypothesis generates hundreds of randomised inputs for each test, shrinks
# any failing input to the smallest reproducer, and remembers the failing
# example in a local database so it is always re-run on subsequent runs.
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

# Shared strategy: any Unicode string up to one line long.
# Surrogates (category "Cs") are excluded because Python cannot encode them
# to UTF-8, which would cause unrelated encode errors rather than parser bugs.
_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=512,
)

# Larger strategy for file content: up to 8 KiB of arbitrary Unicode text.
# Used to feed VerboseGcFile with XML-like blobs of random garbage.
_file_content = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=8192,
)


class TestStackTraceElementHypothesis(unittest.TestCase):
    """Property-based tests for StackTraceElement.set_line().

    StackTraceElement is the first parser that sees every line in a javacore
    file.  Its set_line() method must survive any input without raising an
    unhandled exception, regardless of whether the line matches one of the
    known prefixes (4XESTACKTRACE / 4XENATIVESTACK).
    """

    @given(line=_text)
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_set_line_never_crashes(self, line):
        """Constructing a StackTraceElement from any string must not raise."""
        # We make no assertion about the *result* — the only contract tested
        # here is that the constructor does not propagate any exception for
        # any input, including lines that match neither known prefix.
        StackTraceElement(line)

    @given(line=_text)
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_set_line_result_is_none_or_string(self, line):
        """get_line() must return either None or a str — never another type."""
        # After construction the parsed line is either None (unrecognised
        # prefix) or the extracted method/frame string.  Any other return
        # type is a coding error.
        element = StackTraceElement(line)
        result = element.get_line()
        self.assertIsInstance(result, (str, type(None)),
                              f"get_line() returned unexpected type {type(result)!r} for input {line!r}")

    @given(line=_text)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_get_kind_str_always_valid(self, line):
        """get_kind_str() must always return one of the expected string values."""
        # The only valid returns are "java" (default), "native" (4XENATIVESTACK
        # prefix) and "" (fallback).  Any other value would break XSL rendering.
        element = StackTraceElement(line)
        self.assertIn(element.get_kind_str(), ("java", "native", ""))


class TestVerboseGcFileHypothesis(unittest.TestCase):
    """Property-based tests for VerboseGcFile XML parsing.

    VerboseGcFile reads an IBM verbose GC log file and parses it as XML.
    The only acceptable outcomes for any input are:
      1. Successful parse — file happened to be valid XML.
      2. GcVerboseProcessingException — file is malformed; this is the
         documented contract for bad input.
    Any other exception (IndexError, AttributeError, etc.) is a bug.
    """

    @given(content=_file_content)
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_never_raises_unexpected_exception(self, content):
        """Parsing arbitrary file content must not propagate unexpected exceptions."""
        # Write the generated content to a real temp file because VerboseGcFile
        # accepts a file path, not a string.  The .xml suffix keeps the code
        # path consistent with production usage.
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
            # Always clean up the temp file, even if the test assertion fails.
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
        # Sanity check: a structurally correct but empty verbosegc file must
        # never raise any exception (not even GcVerboseProcessingException).
        # This guards against regressions that break the happy path.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            VerboseGcFile(tmp_path)  # must not raise
        finally:
            os.unlink(tmp_path)

