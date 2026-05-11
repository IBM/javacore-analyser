#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os.path
import platform
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock

from javacore_analyser import javacore_analyser_batch


class TestZipSlipSecurity(unittest.TestCase):
    """
    Test suite for Zip Slip vulnerability protection (Issue #211, Commit 85fc5e2e).
    
    These tests verify that the security fixes in _is_safe_path() and _safe_extract()
    properly prevent path traversal attacks while allowing legitimate archive extraction.
    """

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory and logging handlers."""
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Clean up logging handlers
        root = logging.getLogger()
        for handler in root.handlers.copy():
            root.removeHandler(handler)
            handler.close()

    # ========== Tests for _is_safe_path() ==========

    def test_is_safe_path_valid_relative_path(self):
        """Test that a normal relative path within base directory is allowed."""
        base_path = self.test_dir
        file_path = "javacore.txt"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertTrue(result, "Valid relative path should be allowed")

    def test_is_safe_path_valid_subdirectory(self):
        """Test that a file in a subdirectory is allowed."""
        base_path = self.test_dir
        file_path = "subdir/javacore.txt"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertTrue(result, "File in subdirectory should be allowed")

    def test_is_safe_path_current_directory(self):
        """Test that current directory reference is allowed."""
        base_path = self.test_dir
        file_path = "./javacore.txt"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertTrue(result, "Current directory reference should be allowed")

    def test_is_safe_path_parent_traversal_attack(self):
        """Test that parent directory traversal is blocked."""
        base_path = self.test_dir
        file_path = "../etc/passwd"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertFalse(result, "Parent directory traversal should be blocked")

    def test_is_safe_path_multiple_parent_traversal(self):
        """Test that multiple parent directory traversals are blocked."""
        base_path = self.test_dir
        file_path = "../../../etc/passwd"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertFalse(result, "Multiple parent traversals should be blocked")

    def test_is_safe_path_absolute_path_attack(self):
        """Test that absolute paths are blocked."""
        base_path = self.test_dir
        file_path = "/etc/passwd"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertFalse(result, "Absolute path should be blocked")

    def test_is_safe_path_windows_style_traversal(self):
        """Test that Windows-style path traversal is blocked on Windows.
        
        Note: On Unix/macOS, backslashes are treated as regular filename characters,
        not path separators, so this pattern would be a valid filename.
        The security check still works because actual Windows systems would interpret
        backslashes as separators, and archives created on Windows with malicious
        paths would use forward slashes in the archive format anyway.
        """
        base_path = self.test_dir
        file_path = "..\\..\\windows\\system32\\config"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        
        # On Unix/macOS, backslashes are literal characters, so this is a valid filename
        # On Windows, this would be a path traversal and should be blocked
        # Since we're testing on Unix, we expect True (valid filename)
        # The real protection comes from archive formats normalizing paths to forward slashes
        if platform.system() == 'Windows':
            self.assertFalse(result, "Windows-style traversal should be blocked on Windows")
        else:
            # On Unix, backslashes are just characters in the filename
            self.assertTrue(result, "On Unix, backslashes are literal characters")

    def test_is_safe_path_mixed_traversal(self):
        """Test that mixed traversal (subdir then parent) is blocked when it escapes."""
        base_path = self.test_dir
        file_path = "subdir/../../outside/file.txt"
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertFalse(result, "Mixed traversal escaping base should be blocked")

    def test_is_safe_path_nested_subdirectory_with_parent(self):
        """Test that traversal within subdirectories is allowed if it stays inside base."""
        base_path = self.test_dir
        file_path = "subdir1/subdir2/../file.txt"  # Resolves to subdir1/file.txt
        result = javacore_analyser_batch._is_safe_path(base_path, file_path)
        self.assertTrue(result, "Traversal within base directory should be allowed")

    # ========== Tests for _safe_extract() ==========

    def test_safe_extract_valid_archive(self):
        """Test that extraction succeeds with all valid paths."""
        mock_archive = MagicMock()
        mock_archive.extractall = MagicMock()
        
        valid_members = [
            "javacore.20220606.114458.32888.0001.txt",
            "subdir/javacore.20220606.114502.32888.0002.txt",
            "data/verbosegc.txt"
        ]
        
        # Should not raise an exception
        try:
            javacore_analyser_batch._safe_extract(mock_archive, self.test_dir, valid_members)
            mock_archive.extractall.assert_called_once_with(path=self.test_dir)
        except Exception as e:
            self.fail(f"Valid archive extraction should not raise exception: {e}")

    def test_safe_extract_malicious_archive_parent_traversal(self):
        """Test that extraction fails with parent directory traversal."""
        mock_archive = MagicMock()
        
        malicious_members = [
            "javacore.txt",
            "../../../etc/passwd"  # Malicious path
        ]
        
        with self.assertRaises(Exception) as context:
            javacore_analyser_batch._safe_extract(mock_archive, self.test_dir, malicious_members)
        
        self.assertIn("Unsafe path detected", str(context.exception))
        self.assertIn("../../../etc/passwd", str(context.exception))

    def test_safe_extract_malicious_archive_absolute_path(self):
        """Test that extraction fails with absolute path."""
        mock_archive = MagicMock()
        
        malicious_members = [
            "javacore.txt",
            "/etc/passwd"  # Absolute path
        ]
        
        with self.assertRaises(Exception) as context:
            javacore_analyser_batch._safe_extract(mock_archive, self.test_dir, malicious_members)
        
        self.assertIn("Unsafe path detected", str(context.exception))

    def test_safe_extract_all_malicious_paths(self):
        """Test that extraction fails when all paths are malicious."""
        mock_archive = MagicMock()
        
        malicious_members = [
            "../../../etc/passwd",
            "../../root/.ssh/id_rsa",
            "/var/log/system.log"
        ]
        
        with self.assertRaises(Exception) as context:
            javacore_analyser_batch._safe_extract(mock_archive, self.test_dir, malicious_members)
        
        self.assertIn("Unsafe path detected", str(context.exception))

    def test_safe_extract_empty_member_list(self):
        """Test that extraction succeeds with empty member list."""
        mock_archive = MagicMock()
        mock_archive.extractall = MagicMock()
        
        # Should not raise an exception
        try:
            javacore_analyser_batch._safe_extract(mock_archive, self.test_dir, [])
            mock_archive.extractall.assert_called_once_with(path=self.test_dir)
        except Exception as e:
            self.fail(f"Empty member list should not raise exception: {e}")

    # ========== Integration Tests ==========

    def test_extract_archive_with_malicious_zip(self):
        """Test that extract_archive rejects a malicious ZIP file."""
        # Create a malicious ZIP file
        malicious_zip = os.path.join(self.test_dir, "malicious.zip")
        with zipfile.ZipFile(malicious_zip, 'w') as zf:
            # Add a legitimate file
            zf.writestr("javacore.txt", "legitimate content")
            # Add a malicious file with path traversal
            zf.writestr("../../../etc/passwd", "malicious content")
        
        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir)
        
        # Should raise an exception
        with self.assertRaises(Exception) as context:
            javacore_analyser_batch.extract_archive(malicious_zip, output_dir)
        
        self.assertIn("Unsafe path detected", str(context.exception))

    def test_extract_archive_legitimate_zip_still_works(self):
        """Test that legitimate ZIP files still extract successfully."""
        # Create a legitimate ZIP file
        legitimate_zip = os.path.join(self.test_dir, "legitimate.zip")
        with zipfile.ZipFile(legitimate_zip, 'w') as zf:
            zf.writestr("javacore.20220606.114458.32888.0001.txt", "javacore content")
            zf.writestr("subdir/javacore.20220606.114502.32888.0002.txt", "more content")
            zf.writestr("data/verbosegc.txt", "gc log content")
        
        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir)
        
        # Should extract successfully
        try:
            result = javacore_analyser_batch.extract_archive(legitimate_zip, output_dir)
            self.assertEqual(result, output_dir)
            
            # Verify files were extracted
            self.assertTrue(os.path.exists(os.path.join(output_dir, "javacore.20220606.114458.32888.0001.txt")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "subdir", "javacore.20220606.114502.32888.0002.txt")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "data", "verbosegc.txt")))
        except Exception as e:
            self.fail(f"Legitimate ZIP extraction should not fail: {e}")

    def test_path_traversal_variations(self):
        """Test various path traversal attack patterns.
        
        Note: This test focuses on Unix-style path traversal patterns.
        Windows-style backslash patterns are platform-specific and tested separately.
        """
        base_path = self.test_dir
        
        # Collection of known path traversal patterns (Unix-style)
        malicious_patterns = [
            "../etc/passwd",
            "../../etc/passwd",
            "../../../etc/passwd",
            "/etc/passwd",
            "/var/log/system.log",
            "subdir/../../../etc/passwd",
            "subdir/../../outside.txt",
            "./../../../etc/passwd",
        ]
        
        for pattern in malicious_patterns:
            with self.subTest(pattern=pattern):
                result = javacore_analyser_batch._is_safe_path(base_path, pattern)
                self.assertFalse(result, f"Pattern '{pattern}' should be blocked")

    def test_legitimate_path_variations(self):
        """Test various legitimate path patterns."""
        base_path = self.test_dir
        
        # Collection of legitimate path patterns
        legitimate_patterns = [
            "javacore.txt",
            "subdir/javacore.txt",
            "data/logs/verbosegc.txt",
            "./javacore.txt",
            "subdir/./javacore.txt",
            "a/b/c/d/e/file.txt",  # Deep nesting is OK
            "subdir/../javacore.txt",  # Stays within base
            "a/b/../c/file.txt",  # Stays within base
        ]
        
        for pattern in legitimate_patterns:
            with self.subTest(pattern=pattern):
                result = javacore_analyser_batch._is_safe_path(base_path, pattern)
                self.assertTrue(result, f"Pattern '{pattern}' should be allowed")

# Made with Bob
