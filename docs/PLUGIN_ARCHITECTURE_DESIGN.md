# Plugin Architecture Design for Javacore Analyser

## Executive Summary

This document proposes a plugin architecture that allows users to extend javacore-analyser with custom data source plugins while keeping the existing javacores, verbose GC, and HAR file functionality unchanged. The design focuses on extensibility through a well-defined plugin interface and simple HTML generation directly in Python.

## Problem Statement

Currently, the tool supports three data sources (javacores, verbose GC, HAR files) but:
- Adding new data sources requires modifying core code
- Users cannot add custom data sources without forking the project
- The architecture doesn't provide a standard way to integrate new diagnostic data types

## Design Goals

1. **Non-Breaking**: Keep existing functionality exactly as is
2. **User Extensibility**: Allow users to add custom plugins without modifying core code
3. **Simple Integration**: Minimal boilerplate for plugin development
4. **Discoverability**: Automatic plugin discovery mechanism
5. **Documentation**: Clear guide for plugin developers

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│              Existing Core (Unchanged)                  │
│  - JavacoreSet                                          │
│  - VerboseGcParser                                      │
│  - HarFile                                              │
│  - Report generation                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            │ extends
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Plugin System (New)                        │
│  - Plugin discovery                                     │
│  - Plugin registration                                  │
│  - Plugin lifecycle management                          │
│  - HTML injection wrapper generation                    │
└─────────────────────────────────────────────────────────┘
                            │
                            │ loads
                            ▼
┌─────────────────────────────────────────────────────────┐
│              User Plugins (External)                    │
│  - Thread dump plugin                                   │
│  - Heap dump plugin                                     │
│  - Custom log plugin                                    │
│  - Any user-defined plugin                              │
└─────────────────────────────────────────────────────────┘
```

### Rendering Approach

Plugin rendering is intentionally simple:

1. Plugins parse their own files in Python
2. Plugins return XML for structured report integration
3. Plugins return HTML strings from `generate_html()`
4. The report generator wraps that HTML in `plugins.xsl`
5. XSL injects the HTML fragment into the final report using `disable-output-escaping`

This keeps presentation logic in normal Python code, so plugin authors only need Python knowledge and do not need to learn XSL.

## Plugin Interface

### Base Plugin Class

Users create plugins by extending the `DataSourcePlugin` abstract base class:

```python
# src/javacore_analyser/plugin_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.dom.minidom import Document, Element

class DataSourcePlugin(ABC):
    """
    Abstract base class for custom data source plugins.
    
    Users extend this class to add support for new diagnostic data types.
    """
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Return unique plugin identifier.
        
        Example: 'threaddump', 'heapdump', 'customlog'
        """
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """
        Return human-readable name for reports.
        
        Example: 'Thread Dumps', 'Heap Dumps', 'Custom Application Logs'
        """
        pass
    
    @abstractmethod
    def get_file_patterns(self) -> List[str]:
        """
        Return glob patterns for file discovery.
        
        Example: ['*.tdump', '*threaddump*.txt']
        """
        pass
    
    @abstractmethod
    def can_process(self, filepath: str) -> bool:
        """
        Validate if this plugin can process the given file.
        
        Args:
            filepath: Path to file to check
            
        Returns:
            True if plugin can process this file
        """
        pass
    
    @abstractmethod
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Process files and return structured data.
        
        Args:
            filepaths: List of file paths to process
            
        Returns:
            Dictionary containing processed data. Structure is plugin-defined.
        """
        pass
    
    @abstractmethod
    def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Element:
        """
        Generate XML representation for report integration.
        
        Args:
            doc: XML Document object
            data: Processed data from process_files()
            
        Returns:
            XML Element to be included in report
        """
        pass
    
    @abstractmethod
    def generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML content for direct injection into the final report.
        
        Plugins return a complete HTML fragment as a string. This HTML is generated
        in Python, typically with f-strings, and then injected into the final report
        by a generated XSL wrapper using `disable-output-escaping="yes"`.
        
        Plugin authors should use `html.escape()` for any file names, messages,
        or other user-controlled values inserted into the HTML.
        
        Available CSS classes from the main report include:
        - `tablesorter` for sortable tables
        - `expandit` for collapsible section headers
        - `error_row` for error-highlighted rows
        - `warning_row` for warning-highlighted rows
        - `error_cell` for error-highlighted cells
        
        Args:
            data: Processed data from process_files()
            
        Returns:
            HTML string to be injected into the report, or an empty string if
            the plugin has nothing to render
        """
        pass
    
    def get_time_range(self, data: Dict[str, Any]) -> Optional[tuple[datetime, datetime]]:
        """
        Return time range for temporal correlation with javacores.
        
        Args:
            data: Processed data from process_files()
            
        Returns:
            (start_time, end_time) tuple, or None if not applicable
        """
        return None
    
    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return key metrics for dashboard display.
        
        Args:
            data: Processed data from process_files()
            
        Returns:
            Dictionary of metric_name: metric_value
        """
        return {}
    
    def get_description(self) -> str:
        """
        Return detailed description of what the plugin does.
        
        This description should explain:
        - What type of data the plugin processes
        - What analysis or insights it provides
        - What file formats it supports
        - Any special requirements or limitations
        
        Returns:
            Multi-line string describing the plugin's purpose and functionality
        """
        return f"{self.get_display_name()} plugin - no description provided."
```

### HTML Generation Example

A minimal plugin can generate report content directly in Python:

```python
def generate_html(self, data: Dict[str, Any]) -> str:
    from html import escape
    
    html = f'''
<h3><a id="toggle_plugin" href="javascript:expand_it(plugin,toggle_plugin)" class="expandit">
    {escape(self.get_display_name())}
</a></h3>
<div id="plugin" style="display:none;">
    <table class="tablesorter">
        <thead>
            <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
            <tr><td>Total Files</td><td>{data['total_files']}</td></tr>
            <tr><td>Total Items</td><td>{data['total_items']}</td></tr>
        </tbody>
    </table>
</div>
'''
    return html
```

This approach is much simpler than authoring XSL templates because plugin developers work entirely in Python.

## Plugin Discovery and Loading

### Plugin Directory Structure

```
~/.javacore_analyser/plugins/          # User plugin directory
├── my_custom_plugin/
│   ├── __init__.py
│   └── plugin.py                      # Contains plugin class
├── another_plugin/
│   ├── __init__.py
│   └── plugin.py
└── requirements.txt                   # Optional: plugin dependencies
```

### Plugin Manager

```python
# src/javacore_analyser/plugin_manager.py

import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Type
from javacore_analyser.plugin_interface import DataSourcePlugin

class PluginManager:
    """Manages plugin discovery, loading, and lifecycle"""
    
    def __init__(self):
        self._plugins: Dict[str, DataSourcePlugin] = {}
        self._plugin_dir = self._get_plugin_directory()
    
    def _get_plugin_directory(self) -> Path:
        """Get user plugin directory, create if doesn't exist"""
        plugin_dir = Path.home() / '.javacore_analyser' / 'plugins'
        plugin_dir.mkdir(parents=True, exist_ok=True)
        return plugin_dir
    
    def discover_plugins(self) -> List[str]:
        """
        Discover and load all plugins from plugin directory.
        
        Returns:
            List of loaded plugin names
        """
        loaded = []
        
        if not self._plugin_dir.exists():
            return loaded
        
        # Scan for plugin directories
        for item in self._plugin_dir.iterdir():
            if item.is_dir() and (item / 'plugin.py').exists():
                try:
                    plugin = self._load_plugin(item)
                    if plugin:
                        self._plugins[plugin.get_plugin_name()] = plugin
                        loaded.append(plugin.get_plugin_name())
                        logging.info(f"Loaded plugin: {plugin.get_display_name()}")
                except Exception as e:
                    logging.warning(f"Failed to load plugin from {item}: {e}")
        
        return loaded
    
    def _load_plugin(self, plugin_dir: Path) -> Optional[DataSourcePlugin]:
        """Load a single plugin from directory"""
        plugin_file = plugin_dir / 'plugin.py'
        
        # Load module
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_dir.name}", 
            plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # Find plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, DataSourcePlugin) and 
                attr is not DataSourcePlugin):
                return attr()
        
        return None
    
    def get_plugin(self, name: str) -> Optional[DataSourcePlugin]:
        """Get plugin by name"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, DataSourcePlugin]:
        """Get all loaded plugins"""
        return self._plugins.copy()
    
    def find_files_for_plugins(self, directory: str) -> Dict[str, List[str]]:
        """
        Scan directory and map files to plugins.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Dictionary mapping plugin_name -> list of matching files
        """
        import fnmatch
        
        file_mapping = {}
        
        for plugin_name, plugin in self._plugins.items():
            matching_files = []
            patterns = plugin.get_file_patterns()
            
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    # Check patterns
                    if any(fnmatch.fnmatch(filename, pattern) 
                          for pattern in patterns):
                        # Validate with plugin
                        if plugin.can_process(filepath):
                            matching_files.append(filepath)
            
            if matching_files:
                file_mapping[plugin_name] = matching_files
        
        return file_mapping
```

## Integration with Existing Code

### Modified JavacoreSet

Add plugin support to existing `JavacoreSet.create()` method:

```python
# In src/javacore_analyser/javacore_set.py

class JavacoreSet:
    def __init__(self, path):
        # ... existing code ...
        self.plugin_data = {}  # Store plugin results
        self.plugin_manager = None  # Will be set if plugins enabled
    
    @staticmethod
    def create(path):
        jset = JavacoreSet(path)
        jset.populate_files_list()
        
        # Existing code for javacores, verbose GC, HAR files
        # ... unchanged ...
        
        # NEW: Load and process plugins if enabled
        if Properties.get_instance().get_property("enable_plugins", False):
            jset._process_plugins()
        
        return jset
    
    def _process_plugins(self):
        """Process custom plugins"""
        from javacore_analyser.plugin_manager import PluginManager
        
        self.plugin_manager = PluginManager()
        loaded = self.plugin_manager.discover_plugins()
        
        if not loaded:
            logging.info("No custom plugins found")
            return
        
        logging.info(f"Loaded {len(loaded)} custom plugins: {', '.join(loaded)}")
        
        # Find files for each plugin
        file_mapping = self.plugin_manager.find_files_for_plugins(self.path)
        
        # Process each plugin
        for plugin_name, filepaths in file_mapping.items():
            plugin = self.plugin_manager.get_plugin(plugin_name)
            try:
                logging.info(f"Processing {len(filepaths)} files with {plugin.get_display_name()}")
                data = plugin.process_files(filepaths)
                self.plugin_data[plugin_name] = {
                    'plugin': plugin,
                    'data': data,
                    'files': filepaths
                }
            except Exception as e:
                logging.error(f"Plugin {plugin_name} failed: {e}")
```

### Report Generation Integration

#### XML Generation

```python
# In src/javacore_analyser/javacore_set.py

def __create_report_xml(self, filename):
    """Modified to include plugin data"""
    # ... existing XML generation code ...
    
    # NEW: Add plugin sections
    if self.plugin_data:
        plugins_node = self.doc.createElement('plugins')
        
        for plugin_name, plugin_info in self.plugin_data.items():
            plugin = plugin_info['plugin']
            data = plugin_info['data']
            
            try:
                plugin_node = plugin.generate_xml(self.doc, data)
                plugin_node.setAttribute('name', plugin_name)
                plugin_node.setAttribute('display_name', plugin.get_display_name())
                plugins_node.appendChild(plugin_node)
            except Exception as e:
                logging.error(f"Failed to generate XML for plugin {plugin_name}: {e}")
        
        root.appendChild(plugins_node)
    
    # ... rest of existing code ...
```

#### HTML Wrapper Generation

The system automatically generates a `plugins.xsl` file during report creation, but that file is now only a thin wrapper around HTML strings returned by plugins. This is handled by the `__generate_plugins_xsl()` method in `JavacoreSet`:

```python
# In src/javacore_analyser/javacore_set.py

@staticmethod
def __generate_plugins_xsl(temp_dir: str, plugin_data: dict) -> Optional[str]:
    """
    Generate plugins.xsl file dynamically from loaded plugin HTML content.
    
    This method creates a plugins.xsl file that wraps HTML content generated by plugins
    into a single XSL template named "plugins". The generated file is used by report.xsl
    to include plugin-specific content in the final HTML report.
    
    The method handles:
    - Calling generate_html() on each plugin to get HTML content
    - Wrapping HTML in CDATA sections with disable-output-escaping for proper injection
    - Combining all plugin HTML into a single plugins.xsl file
    - Creating a fallback empty template if no plugins are loaded or if errors occur
    - Comprehensive error handling and logging for HTML generation failures
    """
    plugins_xsl_path = os.path.join(temp_dir, "plugins.xsl")
    
    try:
        plugins_xsl_content = '''<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# This file is auto-generated during report creation.
# It contains HTML wrappers for all loaded plugins.
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="plugins">
'''
        
        if plugin_data:
            logging.info("Generating plugins.xsl with plugin HTML content")
            
            for plugin_name, plugin_info in plugin_data.items():
                try:
                    plugin = plugin_info['plugin']
                    data = plugin_info.get('data', {})
                    html_content = plugin.generate_html(data)
                    
                    if html_content:
                        plugins_xsl_content += f'''
        <!-- Plugin: {plugin.get_display_name()} -->
        <xsl:text disable-output-escaping="yes"><![CDATA[
{html_content}
        ]]></xsl:text>

'''
                        logging.info(f"Added HTML content for plugin: {plugin.get_display_name()}")
                    else:
                        logging.debug(f"Plugin {plugin.get_display_name()} returned no HTML content")
                        
                except Exception as e:
                    logging.error(f"Error generating HTML for plugin {plugin_name}: {e}")
                    plugins_xsl_content += f'''
        <!-- Plugin: {plugin_name} - Error generating HTML -->
        <xsl:text disable-output-escaping="yes"><![CDATA[
<div class="error_row" style="padding: 10px; margin: 10px 0;">
    <strong>Error in plugin {plugin_name}:</strong> {e}
</div>
        ]]></xsl:text>

'''
        else:
            plugins_xsl_content += "        <!-- No plugins loaded -->\n"
        
        plugins_xsl_content += '''    </xsl:template>

</xsl:stylesheet>
'''
        
        with open(plugins_xsl_path, 'w', encoding='utf-8') as f:
            f.write(plugins_xsl_content)
        
        return plugins_xsl_path
        
    except Exception as e:
        logging.error(f"Error generating plugins.xsl: {e}")
        # Fallback empty template
        with open(plugins_xsl_path, 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template name="plugins">
        <!-- Error generating plugin HTML wrappers -->
    </xsl:template>
</xsl:stylesheet>
''')
        return plugins_xsl_path
```

**Implementation Details:**

1. **Method Signature**: The method remains a static method that takes `temp_dir` and `plugin_data`, returning an `Optional[str]` path to the generated wrapper file.

2. **HTML Injection**: For each loaded plugin:
   - The system calls `generate_html(data)`
   - The returned HTML fragment is wrapped in `<xsl:text disable-output-escaping="yes">`
   - CDATA is used so the plugin HTML can be embedded safely in the generated XSL file
   - The final report receives the HTML exactly as produced by the plugin

3. **Error Handling**:
   - Individual plugin HTML generation errors are logged but do not stop other plugins from rendering
   - A visible error block can be injected into the report so plugin failures are discoverable
   - If wrapper generation fails completely, a fallback empty template is written

4. **Empty Template**: If no plugins are loaded or no plugin returns HTML, an empty but valid `plugins` template is generated to prevent report rendering errors.

#### Report XSL Integration

The main `report.xsl` file still includes a static reference to `plugins.xsl`, but the generated file now contains HTML injection wrappers rather than plugin-authored XSL:

```xml
<!-- src/javacore_analyser/data/xml/report.xsl -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <!-- Import section templates -->
    <xsl:include href="sections/header.xsl"/>
    <xsl:include href="sections/input_files.xsl"/>
    <!-- ... other sections ... -->
    <xsl:include href="sections/http_calls.xsl"/>
    <xsl:include href="plugins.xsl"/>  <!-- Generated HTML injection wrapper -->
    <xsl:include href="sections/footer.xsl"/>
    
    <xsl:template name="body_content">
        <!-- ... existing sections ... -->
        <xsl:call-template name="http_calls"/>
        <xsl:call-template name="plugins"/>  <!-- Inject plugin HTML -->
        <xsl:call-template name="footer"/>
    </xsl:template>
</xsl:stylesheet>
```

#### Rendering Flow

```text
plugin.process_files()
        │
        ▼
plugin.generate_xml() ──────► report XML
        │
        ▼
plugin.generate_html() ─────► HTML fragment
        │
        ▼
__generate_plugins_xsl()
        │ wraps HTML in xsl:text + disable-output-escaping
        ▼
plugins.xsl
        │ included by
        ▼
report.xsl
        │ injects
        ▼
final HTML report
```

**Key Points:**

1. **Static Include**: `report.xsl` still uses a static `<xsl:include href="plugins.xsl"/>` directive
2. **Dynamic Generation**: `plugins.xsl` is regenerated for each report run
3. **Python-First Rendering**: Plugin authors generate HTML in Python rather than authoring XSL
4. **Direct HTML Injection**: HTML is inserted into the report using `disable-output-escaping`
5. **Error Visibility**: Plugin rendering failures can be surfaced directly in the report

## Example: Custom Plugin Implementation

### Thread Dump Plugin Example

```python
# ~/.javacore_analyser/plugins/threaddump/plugin.py

from html import escape
from javacore_analyser.plugin_interface import DataSourcePlugin
from typing import List, Dict, Any
import os
import re

class ThreadDumpPlugin(DataSourcePlugin):
    """Plugin to analyze thread dump files"""
    
    def get_plugin_name(self) -> str:
        return "threaddump"
    
    def get_display_name(self) -> str:
        return "Thread Dumps"
    
    def get_description(self) -> str:
        return """
Thread Dump Plugin - Analyzes Java thread dump files

This plugin processes thread dump files and extracts information about:
- Thread states and counts
- Thread names and IDs
- Stack traces
- Lock information

Supported file patterns: *.tdump, *thread_dump*.txt, *threaddump*.log
        """.strip()
    
    def get_file_patterns(self) -> List[str]:
        return ['*.tdump', '*thread_dump*.txt', '*threaddump*.log']
    
    def can_process(self, filepath: str) -> bool:
        """Check if file contains thread dump data"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = ''.join(f.readline() for _ in range(10))
                return 'Full thread dump' in first_lines or 'Thread-' in first_lines
        except Exception:
            return False
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        """Parse thread dump files"""
        dumps = []
        
        for filepath in filepaths:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            threads = re.findall(r'"([^"]+)" #(\d+)', content)
            
            dumps.append({
                'file': os.path.basename(filepath),
                'thread_count': len(threads),
                'threads': threads[:10]
            })
        
        return {
            'dumps': dumps,
            'total_files': len(filepaths),
            'total_threads': sum(d['thread_count'] for d in dumps)
        }
    
    def generate_xml(self, doc, data: Dict[str, Any]):
        """Generate XML for report correlation and structured data export"""
        root = doc.createElement('threaddumps')
        root.setAttribute('total_files', str(data['total_files']))
        root.setAttribute('total_threads', str(data['total_threads']))
        
        for dump in data['dumps']:
            dump_node = doc.createElement('dump')
            dump_node.setAttribute('file', dump['file'])
            dump_node.setAttribute('thread_count', str(dump['thread_count']))
            root.appendChild(dump_node)
        
        return root
    
    def generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML directly in Python using f-strings"""
        rows = []
        for dump in data['dumps']:
            rows.append(f"""
            <tr>
                <td>{escape(dump['file'])}</td>
                <td>{dump['thread_count']}</td>
            </tr>""")
        
        html = f'''
<h3><a id="toggle_threaddumps" href="javascript:expand_it(threaddumps,toggle_threaddumps)" class="expandit">
    {escape(self.get_display_name())}
</a></h3>
<div id="threaddumps" style="display:none;">
    <table class="tablesorter">
        <thead>
            <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
            <tr><td>Total Files</td><td>{data['total_files']}</td></tr>
            <tr><td>Total Threads</td><td>{data['total_threads']}</td></tr>
        </tbody>
    </table>

    <h4>Thread Dump Files</h4>
    <table class="tablesorter">
        <thead>
            <tr><th>File</th><th>Thread Count</th></tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</div>
'''
        return html
    
    def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'Total Thread Dumps': data['total_files'],
            'Total Threads': data['total_threads'],
            'Avg Threads per Dump': data['total_threads'] // data['total_files']
        }
```

This example keeps the same report functionality, but the presentation logic now lives in `generate_html()` instead of an external XSL file. The key advantage is that the plugin developer writes ordinary Python and can safely inject values with `html.escape()`.

## Configuration

### Enable Plugins in config.ini

```ini
[plugins]
# Enable custom plugin system
enable_plugins = true

# Plugin directory (default: ~/.javacore_analyser/plugins)
# plugin_directory = /custom/path/to/plugins
```

## User Guide for Plugin Development

### Step 1: Create Plugin Directory

```bash
mkdir -p ~/.javacore_analyser/plugins/my_plugin
cd ~/.javacore_analyser/plugins/my_plugin
```

### Step 2: Create Plugin File

```bash
touch __init__.py
touch plugin.py
```

### Step 3: Implement Plugin Class

```python
# plugin.py
from javacore_analyser.plugin_interface import DataSourcePlugin

class MyCustomPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "myplugin"
    
    def get_display_name(self) -> str:
        return "My Custom Data Source"
    
    def get_file_patterns(self) -> List[str]:
        return ['*.mydata']
    
    def can_process(self, filepath: str) -> bool:
        # Validate file
        return filepath.endswith('.mydata')
    
    def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
        # Parse and analyze files
        return {'processed': len(filepaths)}
    
    def generate_xml(self, doc, data: Dict[str, Any]):
        # Generate XML for report
        node = doc.createElement('mydata')
        node.setAttribute('count', str(data['processed']))
        return node
```

### Step 4: Test Plugin

```bash
# Enable plugins in config
echo "enable_plugins = true" >> ~/.javacore_analyser/config.ini

# Run analysis
python -m javacore_analyser input_dir/ output_dir/
```

## Plugin Development Best Practices

1. **Error Handling**: Always wrap file processing in try-except blocks
2. **Validation**: Implement robust `can_process()` validation
3. **Logging**: Use Python logging for debugging
4. **Documentation**: Document expected file formats
5. **Testing**: Create unit tests for your plugin
6. **Dependencies**: Document any external dependencies in requirements.txt

## Benefits

1. **Zero Core Changes**: Existing functionality untouched
2. **User Empowerment**: Users can add custom data sources
3. **Community Growth**: Users can share plugins
4. **Maintainability**: Plugins isolated from core code
5. **Flexibility**: Each plugin defines its own data structure
6. **Simplicity**: Plugin developers only need Python knowledge
7. **Direct HTML Generation**: Plugins build report sections with normal Python f-strings
8. **Safer Output Handling**: Plugins can explicitly escape dynamic values with `html.escape()`
9. **Consistent Styling**: Plugins reuse existing report CSS classes such as `tablesorter`, `expandit`, `error_row`, `warning_row`, and `error_cell`

## Migration Path

### Phase 1: Add Plugin Infrastructure (v1.0)
- Implement `DataSourcePlugin` interface
- Implement `PluginManager`
- Add plugin hooks to `JavacoreSet`
- Document plugin development


## Conclusion

This design allows users to extend javacore-analyser with custom data sources through a simple plugin interface, without requiring any changes to the core codebase. Plugins generate HTML directly in Python and the report system injects that HTML through a generated XSL wrapper, so plugin authors do not need to write XSL templates. The existing javacores, verbose GC, and HAR file functionality remains completely unchanged, ensuring backward compatibility while enabling future extensibility.