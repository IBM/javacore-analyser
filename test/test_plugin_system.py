#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Comprehensive tests for the plugin system.

This module tests the plugin architecture including:
- DataSourcePlugin abstract interface
- PluginManager discovery and loading
- Plugin file pattern matching
- Integration with the analysis workflow
"""

import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
from xml.dom.minidom import Document

from javacore_analyser.plugin_interface import DataSourcePlugin
from javacore_analyser.plugin_manager import PluginManager


class MockValidPlugin(DataSourcePlugin):
    """
    Mock plugin implementation for testing.

    This plugin simulates a valid data source plugin that processes
    test files with a .testdata extension.
    """

    def get_plugin_name(self) -> str:
        """Return unique plugin identifier."""
        return "mock_test_plugin"

    def get_display_name(self) -> str:
        """Return human-readable plugin name."""
        return "Mock Test Plugin"

    def get_file_patterns(self) -> List[str]:
        """Return glob patterns for test file discovery."""
        return ["*.testdata", "*test*.log"]

    def can_process(self, filepath: str) -> bool:
        """Validate whether this plugin can process the given file."""
        if not os.path.exists(filepath):
            return False
        # Check file extension and minimum size
        if filepath.endswith('.testdata') or 'test' in os.path.basename(filepath):
            return os.path.getsize(filepath) > 10
        return False

    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """Process test files and return structured data."""
        return {
            'files_processed': len(filepaths),
            'file_list': [os.path.basename(f) for f in filepaths],
            'total_size': sum(os.path.getsize(f) for f in filepaths if os.path.exists(f))
        }

    def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Any:
        """Generate XML representation of processed data."""
        root = doc.createElement('mock_plugin_data')
        root.setAttribute('files_processed', str(data['files_processed']))
        root.setAttribute('total_size', str(data['total_size']))

        files_node = doc.createElement('files')
        for filename in data['file_list']:
            file_node = doc.createElement('file')
            file_node.setAttribute('name', filename)
            files_node.appendChild(file_node)
        root.appendChild(files_node)

        return root

    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return key summary metrics."""
        return {
            'Files Processed': data.get('files_processed', 0),
            'Total Size': f"{data.get('total_size', 0)} bytes"
        }


class MockPluginWithOptionalMethods(MockValidPlugin):
    """
    Mock plugin that implements optional methods.

    Tests that optional methods can be overridden and provide custom behavior.
    """

    def get_xsl_template(self) -> Optional[str]:
        """Return custom XSL template."""
        return "<xsl:stylesheet>Custom XSL Content</xsl:stylesheet>"

    def get_time_range(self, data: Dict[str, Any]) -> Optional[tuple]:
        """Return time range for the data."""
        from datetime import datetime
        return (datetime(2024, 1, 1), datetime(2024, 1, 2))


class IncompletePlugin(DataSourcePlugin):
    """
    Incomplete plugin implementation for testing abstract method enforcement.

    This plugin intentionally does not implement all required methods.
    """

    def get_plugin_name(self) -> str:
        return "incomplete_plugin"

    # Missing other required methods


class TestPluginInterface(unittest.TestCase):
    """Test the DataSourcePlugin abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that DataSourcePlugin cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DataSourcePlugin()

    def test_incomplete_plugin_cannot_be_instantiated(self):
        """Test that incomplete plugin implementations cannot be instantiated."""
        with self.assertRaises(TypeError):
            IncompletePlugin()

    def test_valid_plugin_can_be_instantiated(self):
        """Test that a complete plugin implementation can be instantiated."""
        plugin = MockValidPlugin()
        self.assertIsNotNone(plugin)
        self.assertIsInstance(plugin, DataSourcePlugin)

    def test_required_methods_exist(self):
        """Test that all required abstract methods are implemented."""
        plugin = MockValidPlugin()

        # Test all required methods
        self.assertEqual(plugin.get_plugin_name(), "mock_test_plugin")
        self.assertEqual(plugin.get_display_name(), "Mock Test Plugin")
        self.assertIsInstance(plugin.get_file_patterns(), list)
        self.assertGreater(len(plugin.get_file_patterns()), 0)

        # Test can_process with a mock file
        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Test data content")
            temp_file = f.name

        try:
            self.assertTrue(plugin.can_process(temp_file))
        finally:
            os.unlink(temp_file)

    def test_optional_methods_have_defaults(self):
        """Test that optional methods have default implementations."""
        plugin = MockValidPlugin()

        # Test default implementations
        self.assertIsNone(plugin.get_xsl_template())
        self.assertIsNone(plugin.get_time_range({}))
        # MockValidPlugin overrides get_summary_metrics, so test with base class behavior
        # by checking that the method exists and returns a dict
        metrics = plugin.get_summary_metrics({})
        self.assertIsInstance(metrics, dict)

    def test_optional_methods_can_be_overridden(self):
        """Test that optional methods can be overridden."""
        plugin = MockPluginWithOptionalMethods()

        # Test overridden implementations
        self.assertIsNotNone(plugin.get_xsl_template())
        self.assertIn("Custom XSL Content", plugin.get_xsl_template())

        time_range = plugin.get_time_range({})
        self.assertIsNotNone(time_range)
        self.assertEqual(len(time_range), 2)

    def test_process_files_returns_dict(self):
        """Test that process_files returns a dictionary."""
        plugin = MockValidPlugin()

        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Test data content")
            temp_file = f.name

        try:
            result = plugin.process_files([temp_file])
            self.assertIsInstance(result, dict)
            self.assertIn('files_processed', result)
            self.assertEqual(result['files_processed'], 1)
        finally:
            os.unlink(temp_file)

    def test_generate_xml_creates_element(self):
        """Test that generate_xml creates an XML element."""
        plugin = MockValidPlugin()
        doc = Document()
        data = {'files_processed': 2, 'file_list': ['test1.txt', 'test2.txt'], 'total_size': 1024}

        element = plugin.generate_xml(doc, data)
        self.assertIsNotNone(element)
        self.assertEqual(element.getAttribute('files_processed'), '2')
        self.assertEqual(element.getAttribute('total_size'), '1024')


class TestPluginManager(unittest.TestCase):
    """Test the PluginManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.temp_dir) / "plugins"
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_plugin_directory_creation(self, mock_home):
        """Test that plugin directory is created if it doesn't exist."""
        mock_home.return_value = Path(self.temp_dir)

        manager = PluginManager()
        expected_dir = Path(self.temp_dir) / ".javacore_analyser" / "plugins"

        self.assertTrue(expected_dir.exists())
        self.assertTrue(expected_dir.is_dir())

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_plugin_discovery_empty_directory(self, mock_home):
        """Test plugin discovery with an empty plugin directory."""
        mock_home.return_value = Path(self.temp_dir)

        manager = PluginManager()
        manager.discover_plugins()

        self.assertEqual(len(manager.get_all_plugins()), 0)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_plugin_discovery_with_valid_plugin(self, mock_home):
        """Test plugin discovery with a valid plugin."""
        mock_home.return_value = Path(self.temp_dir)

        # Create the .javacore_analyser/plugins directory structure
        plugins_base = Path(self.temp_dir) / ".javacore_analyser" / "plugins"
        plugins_base.mkdir(parents=True, exist_ok=True)

        # Create a valid plugin
        plugin_subdir = plugins_base / "test_plugin"
        plugin_subdir.mkdir(parents=True, exist_ok=True)

        # Get absolute path to src directory
        src_dir = Path(__file__).parent.parent / 'src'

        # Write plugin code that will work when loaded dynamically
        plugin_file = plugin_subdir / "plugin.py"
        plugin_file.write_text(f'''
import sys
# Ensure src is in path for imports
src_path = r"{src_dir.absolute()}"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from javacore_analyser.plugin_interface import DataSourcePlugin
from typing import List, Dict, Any
from xml.dom.minidom import Document

class TestPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "test_plugin"
    
    def get_display_name(self) -> str:
        return "Test Plugin"
    
    def get_file_patterns(self) -> List[str]:
        return ["*.test"]
    
    def can_process(self, filepath: str) -> bool:
        return filepath.endswith('.test')
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        return {{"count": len(filepaths)}}
    
    def generate_xml(self, doc: Document, data: Dict[str, Any]):
        return doc.createElement("test")
''')

        manager = PluginManager()
        manager.discover_plugins()

        plugins = manager.get_all_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].get_plugin_name(), "test_plugin")

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_plugin_discovery_skips_invalid_plugins(self, mock_home):
        """Test that invalid plugins are skipped during discovery."""
        mock_home.return_value = Path(self.temp_dir)

        # Create an invalid plugin (syntax error)
        plugin_subdir = self.plugin_dir / "invalid_plugin"
        plugin_subdir.mkdir(parents=True, exist_ok=True)

        plugin_code = '''
from javacore_analyser.plugin_interface import DataSourcePlugin

class InvalidPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "invalid"
    # Missing required methods - this will cause instantiation to fail
'''

        plugin_file = plugin_subdir / "plugin.py"
        plugin_file.write_text(plugin_code)

        manager = PluginManager()
        manager.discover_plugins()

        # Should not load the invalid plugin
        self.assertEqual(len(manager.get_all_plugins()), 0)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_plugin_discovery_skips_directories_without_plugin_py(self, mock_home):
        """Test that directories without plugin.py are skipped."""
        mock_home.return_value = Path(self.temp_dir)

        # Create a directory without plugin.py
        empty_dir = self.plugin_dir / "empty_plugin"
        empty_dir.mkdir(parents=True, exist_ok=True)

        manager = PluginManager()
        manager.discover_plugins()

        self.assertEqual(len(manager.get_all_plugins()), 0)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_get_plugin_by_name(self, mock_home):
        """Test retrieving a plugin by its name."""
        mock_home.return_value = Path(self.temp_dir)

        # Create the .javacore_analyser/plugins directory structure
        plugins_base = Path(self.temp_dir) / ".javacore_analyser" / "plugins"
        plugins_base.mkdir(parents=True, exist_ok=True)

        # Create a valid plugin
        plugin_subdir = plugins_base / "named_plugin"
        plugin_subdir.mkdir(parents=True, exist_ok=True)

        # Get absolute path to src directory
        src_dir = Path(__file__).parent.parent / 'src'

        plugin_file = plugin_subdir / "plugin.py"
        plugin_file.write_text(f'''
import sys
src_path = r"{src_dir.absolute()}"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from javacore_analyser.plugin_interface import DataSourcePlugin
from typing import List, Dict, Any
from xml.dom.minidom import Document

class NamedPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "named_plugin"
    
    def get_display_name(self) -> str:
        return "Named Plugin"
    
    def get_file_patterns(self) -> List[str]:
        return ["*.named"]
    
    def can_process(self, filepath: str) -> bool:
        return True
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        return {{}}
    
    def generate_xml(self, doc: Document, data: Dict[str, Any]):
        return doc.createElement("named")
''')

        manager = PluginManager()
        manager.discover_plugins()

        plugin = manager.get_plugin("named_plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.get_plugin_name(), "named_plugin")

        # Test non-existent plugin
        self.assertIsNone(manager.get_plugin("nonexistent"))

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_find_files_for_plugins(self, mock_home):
        """Test finding files that match plugin patterns."""
        mock_home.return_value = Path(self.temp_dir)

        # Create the .javacore_analyser/plugins directory structure
        plugins_base = Path(self.temp_dir) / ".javacore_analyser" / "plugins"
        plugins_base.mkdir(parents=True, exist_ok=True)

        # Create a valid plugin
        plugin_subdir = plugins_base / "file_finder_plugin"
        plugin_subdir.mkdir(parents=True, exist_ok=True)

        # Get absolute path to src directory
        src_dir = Path(__file__).parent.parent / 'src'

        plugin_file = plugin_subdir / "plugin.py"
        plugin_file.write_text(f'''
import sys
import os
src_path = r"{src_dir.absolute()}"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from javacore_analyser.plugin_interface import DataSourcePlugin
from typing import List, Dict, Any
from xml.dom.minidom import Document

class FileFinderPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "file_finder"
    
    def get_display_name(self) -> str:
        return "File Finder"
    
    def get_file_patterns(self) -> List[str]:
        return ["*.finder", "test*.txt"]
    
    def can_process(self, filepath: str) -> bool:
        return os.path.exists(filepath) and os.path.getsize(filepath) > 5
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        return {{}}
    
    def generate_xml(self, doc: Document, data: Dict[str, Any]):
        return doc.createElement("finder")
''')

        # Create test data directory with matching files
        data_dir = Path(self.temp_dir) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create files that should match
        (data_dir / "file1.finder").write_text("content1")
        (data_dir / "test_data.txt").write_text("content2")
        (data_dir / "other.log").write_text("content3")  # Should not match

        manager = PluginManager()
        manager.discover_plugins()

        result = manager.find_files_for_plugins(str(data_dir))

        # Should find the plugin and its matching files
        self.assertEqual(len(result), 1)
        plugin = list(result.keys())[0]
        files = result[plugin]

        self.assertEqual(plugin.get_plugin_name(), "file_finder")
        self.assertEqual(len(files), 2)

        # Check that the correct files were found
        filenames = [os.path.basename(f) for f in files]
        self.assertIn("file1.finder", filenames)
        self.assertIn("test_data.txt", filenames)
        self.assertNotIn("other.log", filenames)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_find_files_for_plugins_with_nonexistent_directory(self, mock_home):
        """Test find_files_for_plugins with a non-existent directory."""
        mock_home.return_value = Path(self.temp_dir)

        manager = PluginManager()
        manager.discover_plugins()

        result = manager.find_files_for_plugins("/nonexistent/directory")
        self.assertEqual(len(result), 0)

    @patch('javacore_analyser.plugin_manager.Path.home')
    def test_duplicate_plugin_names_handled(self, mock_home):
        """Test that duplicate plugin names are handled gracefully."""
        mock_home.return_value = Path(self.temp_dir)

        # Create the .javacore_analyser/plugins directory structure
        plugins_base = Path(self.temp_dir) / ".javacore_analyser" / "plugins"
        plugins_base.mkdir(parents=True, exist_ok=True)

        # Get absolute path to src directory
        src_dir = Path(__file__).parent.parent / 'src'

        # Create two plugins with the same name
        for i in range(2):
            plugin_subdir = plugins_base / f"duplicate_plugin_{i}"
            plugin_subdir.mkdir(parents=True, exist_ok=True)

            plugin_file = plugin_subdir / "plugin.py"
            plugin_file.write_text(f'''
import sys
src_path = r"{src_dir.absolute()}"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from javacore_analyser.plugin_interface import DataSourcePlugin
from typing import List, Dict, Any
from xml.dom.minidom import Document

class DuplicatePlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "duplicate"
    
    def get_display_name(self) -> str:
        return "Duplicate Plugin"
    
    def get_file_patterns(self) -> List[str]:
        return ["*.dup"]
    
    def can_process(self, filepath: str) -> bool:
        return True
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        return {{}}
    
    def generate_xml(self, doc: Document, data: Dict[str, Any]):
        return doc.createElement("dup")
''')

        manager = PluginManager()
        manager.discover_plugins()

        # Should only load one plugin (first one wins)
        plugins = manager.get_all_plugins()
        self.assertEqual(len(plugins), 1)


class TestPluginIntegration(unittest.TestCase):
    """Test plugin integration with the analysis workflow."""

    def test_plugin_xml_generation_integration(self):
        """Test that plugin XML can be generated and integrated."""
        plugin = MockValidPlugin()

        # Create test data
        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Test data content for integration")
            temp_file = f.name

        try:
            # Process files
            data = plugin.process_files([temp_file])
            self.assertIsInstance(data, dict)

            # Generate XML
            doc = Document()
            xml_element = plugin.generate_xml(doc, data)

            # Verify XML structure
            self.assertIsNotNone(xml_element)
            self.assertEqual(xml_element.tagName, 'mock_plugin_data')
            self.assertTrue(xml_element.hasAttribute('files_processed'))

            # Verify XML can be serialized
            xml_string = xml_element.toxml()
            self.assertIn('mock_plugin_data', xml_string)
            self.assertIn('files_processed', xml_string)

        finally:
            os.unlink(temp_file)

    def test_plugin_summary_metrics_integration(self):
        """Test that plugin summary metrics can be retrieved."""
        plugin = MockValidPlugin()

        # Create test data
        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Test data content for metrics")
            temp_file = f.name

        try:
            # Process files and get metrics
            data = plugin.process_files([temp_file])
            metrics = plugin.get_summary_metrics(data)

            # Verify metrics
            self.assertIsInstance(metrics, dict)
            self.assertIn('Files Processed', metrics)
            self.assertEqual(metrics['Files Processed'], 1)

        finally:
            os.unlink(temp_file)

    def test_plugin_file_validation_workflow(self):
        """Test the complete file validation workflow."""
        plugin = MockValidPlugin()

        # Create valid and invalid test files
        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Valid test data")
            valid_file = f.name

        with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
            f.write(b"Small")  # Too small (< 10 bytes)
            invalid_file = f.name

        try:
            # Test validation
            self.assertTrue(plugin.can_process(valid_file))
            self.assertFalse(plugin.can_process(invalid_file))

            # Test processing only valid files
            data = plugin.process_files([valid_file])
            self.assertEqual(data['files_processed'], 1)

        finally:
            os.unlink(valid_file)
            os.unlink(invalid_file)

    def test_plugin_with_multiple_files(self):
        """Test plugin processing with multiple files."""
        plugin = MockValidPlugin()

        # Create multiple test files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.testdata', delete=False) as f:
                f.write(f"Test data content {i}".encode())
                temp_files.append(f.name)

        try:
            # Process all files
            data = plugin.process_files(temp_files)

            # Verify results
            self.assertEqual(data['files_processed'], 3)
            self.assertEqual(len(data['file_list']), 3)
            self.assertGreater(data['total_size'], 0)

        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()


# Made with Bob