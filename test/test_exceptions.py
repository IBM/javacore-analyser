#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import unittest

from javacore_analyser.exceptions import InvalidLLMMethodError


class TestExceptions(unittest.TestCase):
    """Test cases for custom exceptions."""

    def test_invalid_llm_method_error_message(self):
        """Test that InvalidLLMMethodError generates the correct error message."""
        error = InvalidLLMMethodError("invalid_method")
        expected_message = "Invalid LLM method: 'invalid_method'. Supported methods are: ollama, huggingface"
        self.assertEqual(str(error), expected_message)

    def test_invalid_llm_method_error_attributes(self):
        """Test that InvalidLLMMethodError stores the correct attributes."""
        error = InvalidLLMMethodError("invalid_method")
        self.assertEqual(error.llm_method, "invalid_method")
        self.assertEqual(error.supported_methods, ['ollama', 'huggingface'])

    def test_invalid_llm_method_error_custom_supported_methods(self):
        """Test InvalidLLMMethodError with custom supported methods."""
        custom_methods = ['method1', 'method2', 'method3']
        error = InvalidLLMMethodError("invalid", custom_methods)
        self.assertEqual(error.supported_methods, custom_methods)
        expected_message = "Invalid LLM method: 'invalid'. Supported methods are: method1, method2, method3"
        self.assertEqual(str(error), expected_message)

    def test_invalid_llm_method_error_is_value_error(self):
        """Test that InvalidLLMMethodError is a subclass of ValueError."""
        error = InvalidLLMMethodError("invalid")
        self.assertIsInstance(error, ValueError)

# Made with Bob
