# Liberty SystemOut Plugin - Example Plugin for Javacore Analyser

This is an example plugin that demonstrates how to extend javacore-analyser with custom data source plugins. The Liberty SystemOut Plugin processes WebSphere Liberty server log files (systemout.log, console.log, messages.log) and integrates them into the analysis report.

## Overview

This plugin serves as a **reference implementation** for plugin developers. It demonstrates:

- ✅ Implementing all required abstract methods from `DataSourcePlugin`
- ✅ File pattern matching and validation
- ✅ Parsing custom file formats (Liberty logs)
- ✅ Generating XML output for report integration
- ✅ Providing summary metrics
- ✅ Time range extraction for correlation
- ✅ Comprehensive error handling and logging
- ✅ Full documentation with docstrings

## What This Plugin Does

The Liberty SystemOut Plugin:

1. **Discovers** Liberty log files matching these patterns:
   - `systemout.log`
   - `console.log`
   - `messages.log`
   - `*systemout*.log` (rotated logs)

2. **Validates** files by checking for Liberty log format markers:
   - Timestamp format: `[1/3/24, 10:15:30:123 EST]`
   - Message ID format: `CWWKE0001I`, `SRVE0315E`, etc.
   - Standard Liberty log structure

3. **Parses** Liberty log content to extract:
   - Log messages by severity (Audit, Warning, Error, Info, Other)
   - Message IDs and their frequencies
   - Timestamps for time range analysis
   - Thread IDs and class names
   - Message text (truncated for long messages)

4. **Generates** XML output with:
   - Summary statistics (total files, total messages)
   - Severity distribution (errors, warnings, info, etc.)
   - Top 10 most frequent message IDs
   - Individual log file details
   - Sample messages (prioritizing errors and warnings)

5. **Provides** summary metrics for dashboards:
   - Total log files processed
   - Total messages across all logs
   - Error count
   - Warning count
   - Most frequent message ID

6. **Extracts** time range for correlation with javacores

## Liberty Log Format

This plugin expects Liberty logs in this format:

```
[1/3/24, 10:15:30:123 EST] 00000001 com.ibm.ws.kernel.launch.internal.FrameworkManager A CWWKE0001I: The server defaultServer has been launched.

[1/3/24, 10:15:35:456 EST] 00000023 com.ibm.ws.app.manager.AppMessageHelper I CWWKZ0001I: Application myapp started in 2.345 seconds.

[1/3/24, 10:16:00:789 EST] 00000045 com.example.MyClass E SRVE0315E: An exception occurred: java.lang.NullPointerException
    at com.example.MyClass.doSomething(MyClass.java:42)
    at com.example.MyServlet.doGet(MyServlet.java:28)
```

Format breakdown:
- `[timestamp]` - Date and time with timezone
- `threadId` - Hexadecimal thread identifier
- `className` - Fully qualified class name
- `severity` - A (Audit), W (Warning), E (Error), I (Info), O (Other)
- `messageId` - 4 letters + 4 digits + severity letter
- `message` - The actual log message

## Installation

### Step 1: Create Plugin Directory

```bash
mkdir -p ~/.javacore_analyser/plugins/liberty_systemout
```

### Step 2: Copy Plugin Files

Copy the plugin files to your plugin directory:

```bash
# Copy from the example
cp docs/example_plugin/__init__.py ~/.javacore_analyser/plugins/liberty_systemout/
cp docs/example_plugin/plugin.py ~/.javacore_analyser/plugins/liberty_systemout/
cp docs/example_plugin/liberty_systemout.xsl ~/.javacore_analyser/plugins/liberty_systemout/
```

### Step 3: Enable Plugins

Edit your `config.ini` file (or create one in your working directory):

```ini
[plugins]
# Enable custom plugin system
enable_plugins = true
```

### Step 4: Verify Installation

Run javacore-analyser with the `--help` flag to ensure no errors occur:

```bash
python -m javacore_analyser --help
```

Check the logs for plugin loading messages:
```
INFO: Loaded plugin: Liberty System Out
```

## Usage

### Basic Usage

Place your Liberty log files in the same directory as your javacores:

```bash
input_dir/
├── javacore.20240101.120000.txt
├── javacore.20240101.120100.txt
├── systemout.log
├── console.log
└── messages.log
```

Run the analysis:

```bash
python -m javacore_analyser input_dir/ output_dir/
```

The plugin will automatically:
1. Discover the Liberty log files
2. Validate and process them
3. Include results in the generated report

### Expected Output

The plugin will log its activity:

```
INFO: Loaded 1 custom plugins: liberty_systemout
INFO: Processing 3 files with Liberty System Out
INFO: Processed systemout.log: 1523 messages
INFO: Processed console.log: 245 messages
INFO: Processed messages.log: 892 messages
```

The generated report will include a "Liberty System Out" section with:
- Summary statistics (total files, messages, errors, warnings)
- Severity distribution chart
- Top 10 most frequent message IDs
- Details for each processed log file
- Sample messages (errors and warnings prioritized)
- Time range for correlation with javacores

## File Structure

```
docs/example_plugin/
├── __init__.py              # Package initialization
├── plugin.py                # Main plugin implementation (LibertySystemOutPlugin)
├── liberty_systemout.xsl    # XSL template for HTML report rendering
└── README.md                # This file
```

### Key Files

#### `__init__.py`
Simple package initialization file with copyright header and package documentation.

#### `plugin.py`
Contains the `LibertySystemOutPlugin` class that extends `DataSourcePlugin`. This is where all the plugin logic lives:

- **`get_plugin_name()`**: Returns "liberty_systemout" (internal identifier)
- **`get_display_name()`**: Returns "Liberty System Out" (human-readable name)
- **`get_description()`**: Returns detailed description of plugin functionality
- **`get_file_patterns()`**: Returns list of glob patterns for file discovery
- **`can_process(filepath)`**: Validates if a file is a valid Liberty log
- **`process_files(filepaths)`**: Parses Liberty logs and extracts data
- **`generate_xml(doc, data)`**: Creates XML representation for reports
- **`get_summary_metrics(data)`**: Returns key metrics for dashboards
- **`get_time_range(data)`**: Extracts time range for correlation
- **`get_xsl_template()`**: Returns XSL template content for HTML rendering

#### `liberty_systemout.xsl`
XSL stylesheet that transforms the XML data generated by the plugin into formatted HTML for the analysis report. The template includes:

- Summary statistics table (total files, total messages)
- Severity distribution table with color-coded rows
- Top message IDs table showing most frequent Liberty messages
- Individual log file details with severity breakdowns
- Expandable sections with documentation
- Error highlighting for failed file processing

## Customization

You can customize this plugin for your needs:

### Change File Patterns

Edit the `get_file_patterns()` method:

```python
def get_file_patterns(self) -> List[str]:
    return ['systemout*.log', 'trace*.log', 'ffdc*.log']
```

### Modify Validation Logic

Update the `can_process()` method to match your log format:

```python
def can_process(self, filepath: str) -> bool:
    # Add your custom validation logic
    with open(filepath, 'r') as f:
        first_line = f.readline()
        return 'YOUR_LOG_MARKER' in first_line
```

### Extend Parsing

Enhance the `_parse_liberty_log()` method to extract additional information:

```python
def _parse_liberty_log(self, filepath: str) -> Dict[str, Any]:
    # Add custom parsing logic
    # Extract FFDC information
    # Parse stack traces
    # Identify performance issues
    pass
```

### Add Custom Metrics

Extend `get_summary_metrics()` to provide more insights:

```python
def get_summary_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'Total Messages': data['total_messages'],
        'Critical Errors': self._count_critical_errors(data),
        'Application Starts': self._count_app_starts(data),
        'OutOfMemory Errors': self._count_oom_errors(data)
    }
```

### Filter Specific Messages

Add filtering logic to focus on specific message types:

```python
def _parse_liberty_log(self, filepath: str) -> Dict[str, Any]:
    # ... existing code ...
    
    # Filter for specific message IDs
    critical_messages = [m for m in messages if m['message_id'] in ['CWWKE0701E', 'SRVE0315E']]
    
    return {
        # ... existing fields ...
        'critical_messages': critical_messages
    }
```

## Development Tips

### 1. Error Handling

Always wrap file operations in try-except blocks:

```python
try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
except Exception as e:
    logging.error(f"Error reading file {filepath}: {e}")
    return False
```

### 2. Logging

Use Python's logging module for debugging:

```python
import logging

logging.info("Processing started")
logging.debug(f"Found {count} messages")
logging.warning(f"Unexpected format in {filepath}")
logging.error(f"Failed to process: {error}")
```

### 3. Validation

Implement robust validation in `can_process()`:

- Check file size (not too small, not too large)
- Verify file format markers
- Handle encoding issues (use `errors='ignore'`)
- Return False for invalid files (don't raise exceptions)

### 4. Performance

For large log files:

- Use regex efficiently (compile patterns once)
- Don't load entire file if not necessary
- Truncate long messages for XML output
- Limit sample messages to reasonable number
- Set file size limits (e.g., 500MB)

### 5. Testing

Test your plugin with:

- Valid Liberty log files
- Invalid files (wrong format)
- Empty files
- Very large files (100MB+)
- Files with encoding issues
- Rotated log files
- Logs from different Liberty versions

## Troubleshooting

### Plugin Not Loading

**Problem**: Plugin doesn't appear in logs

**Solutions**:
1. Check plugin directory: `~/.javacore_analyser/plugins/liberty_systemout/`
2. Verify `plugin.py` exists in the directory
3. Ensure `enable_plugins = true` in config.ini
4. Check logs for error messages
5. Verify Python can import the plugin (no syntax errors)

### Files Not Detected

**Problem**: Liberty log files not being processed

**Solutions**:
1. Check file patterns match your filenames
2. Verify `can_process()` returns True for your files
3. Check file permissions (must be readable)
4. Review validation logic in `can_process()`
5. Enable debug logging to see validation details

### Processing Errors

**Problem**: Plugin fails during processing

**Solutions**:
1. Check logs for specific error messages
2. Verify log format matches expected Liberty format
3. Test with smaller/simpler files first
4. Add more error handling in parsing code
5. Check for encoding issues (use `errors='ignore'`)

### Regex Not Matching

**Problem**: Log entries not being parsed

**Solutions**:
1. Test regex patterns with sample log entries
2. Check for variations in Liberty log format
3. Use online regex testers for debugging
4. Add logging to see what's being matched
5. Consider making regex more flexible

## Creating Your Own Plugin

Use this plugin as a template:

1. **Copy the structure**:
   ```bash
   cp -r docs/example_plugin ~/.javacore_analyser/plugins/myplugin
   ```

2. **Rename the class**:
   ```python
   class MyCustomPlugin(DataSourcePlugin):
   ```

3. **Update plugin identification**:
   ```python
   def get_plugin_name(self) -> str:
       return "myplugin"
   
   def get_display_name(self) -> str:
       return "My Custom Data Source"
   ```

4. **Define file patterns**:
   ```python
   def get_file_patterns(self) -> List[str]:
       return ['*.mydata', '*custom*.log']
   ```

5. **Implement validation**:
   ```python
   def can_process(self, filepath: str) -> bool:
       # Your validation logic
       pass
   ```

6. **Implement parsing**:
   ```python
   def process_files(self, filepaths: List[str]) -> Dict[str, Any]:
       # Your parsing logic
       pass
   ```

7. **Generate XML output**:
   ```python
   def generate_xml(self, doc: Document, data: Dict[str, Any]) -> Element:
       # Your XML generation logic
       pass
   ```

## Additional Resources

- **Plugin Interface Documentation**: See `src/javacore_analyser/plugin_interface.py`
- **Plugin Architecture Design**: See `docs/PLUGIN_ARCHITECTURE_DESIGN.md`
- **Plugin Manager Implementation**: See `src/javacore_analyser/plugin_manager.py`

## Contributing

If you create a useful plugin, consider sharing it with the community:

1. Create a GitHub repository for your plugin
2. Document installation and usage
3. Add examples and test data
4. Share on the javacore-analyser discussions

## License

```
Copyright IBM Corp. 2024 - 2026
SPDX-License-Identifier: Apache-2.0
```

This example plugin is provided as-is for educational purposes. Feel free to modify and adapt it for your needs.

## Support

For questions or issues:

1. Check the plugin architecture design document
2. Review the plugin interface documentation
3. Examine the plugin manager implementation
4. Open an issue on the javacore-analyser GitHub repository

---

**Made with Bob** 🤖