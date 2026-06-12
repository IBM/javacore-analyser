# Project Structure

This document provides a comprehensive overview of the javacore-analyser project structure to help AI coding assistants and developers quickly understand the codebase organization without scanning all files.

## Overview

Javacore Analyser is a Python tool that analyzes IBM Javacore files, verbose GC logs, and HAR files to generate diagnostic reports. The tool supports both batch processing (CLI) and web-based interfaces.

## Directory Structure

```
javacore-analyser/
├── src/javacore_analyser/          # Main source code
│   ├── ai/                          # AI/LLM integration modules
│   ├── data/                        # Static resources (JS, CSS, XSL, prompts)
│   ├── ml/                          # Machine learning models and inference
│   └── templates/                   # Flask web templates
├── test/                            # Unit tests and test data
│   └── data/                        # Test fixtures (javacores, archives, etc.)
├── docs/                            # Documentation and examples
│   └── example_plugin/              # Reference plugin implementation
├── collectors/                      # Data collection scripts
└── [config files]                   # Build and configuration files
```

## Core Source Modules (`src/javacore_analyser/`)

### Entry Points

| File | Purpose | Key Functions |
|------|---------|---------------|
| `__main__.py` | CLI entry point | Routes to batch or web mode |
| `javacore_analyser_batch.py` | Batch processing CLI | `main()`, `batch_process()`, archive extraction |
| `javacore_analyser_web.py` | Flask web application | Routes for upload, compress, delete |

### Core Analysis Classes

| File | Class | Purpose |
|------|-------|---------|
| `javacore_set.py` | `JavacoreSet` | Main orchestrator - processes javacores, generates reports |
| `javacore.py` | `Javacore` | Represents single javacore file, parses threads |
| `java_thread.py` | `Thread` | Represents thread across multiple javacores |
| `thread_snapshot.py` | `ThreadSnapshot` | Single thread state at one point in time |
| `verbose_gc.py` | `VerboseGcParser`, `VerboseGcFile`, `GcCollection` | Parses verbose GC logs |
| `har_file.py` | `HarFile`, `HttpCall` | Parses HAR (HTTP Archive) files |

### Data Structures

| File | Class | Purpose |
|------|-------|---------|
| `stack_trace.py` | `StackTrace` | Represents thread stack trace |
| `stack_trace_element.py` | `StackTraceElement` | Single stack frame |
| `stack_trace_kind.py` | Enums | Stack trace types (Java, native, etc.) |
| `snapshot_collection.py` | `SnapshotCollection` | Base collection class |
| `abstract_snapshot_collection.py` | `AbstractSnapshotCollection` | Abstract base for collections |
| `code_snapshot_collection.py` | `CodeSnapshotCollection` | Groups threads by code path |
| `snapshot_collection_collection.py` | `SnapshotCollectionCollection` | Collection of collections |

### Plugin System

| File | Class/Purpose |
|------|---------------|
| `plugin_interface.py` | `DataSourcePlugin` - Abstract base class for plugins |
| `plugin_manager.py` | `PluginManager` - Discovers and loads plugins from `~/.javacore_analyser/plugins/` |

**Plugin Architecture:**
- Plugins extend `DataSourcePlugin` abstract class
- Loaded from `~/.javacore_analyser/plugins/` directory
- Each plugin processes custom file types and generates HTML/XML for reports
- See `docs/PLUGIN_ARCHITECTURE_DESIGN.md` for detailed design
- See `docs/example_plugin/` for reference implementation

### AI/LLM Integration (`ai/`)

| File | Purpose |
|------|---------|
| `llm.py` | Abstract base class for LLM providers |
| `ollama_llm.py` | Ollama server integration (requires external Ollama) |
| `huggingface_llm.py` | HuggingFace local inference |
| `prompter.py` | Base class for prompt generation |
| `tips_prompter.py` | Generates prompts for intelligent tips |
| `performance_recommendations_prompter.py` | Generates performance analysis prompts |

**LLM Methods:**
- `ollama`: Requires Ollama server, uses models like `ibm/granite4:latest`
- `huggingface`: Local inference, uses models like `ibm-granite/granite-4.0-micro`

### Machine Learning (`ml/`)

| File | Purpose |
|------|---------|
| `classify_javacore_inference.py` | Thread classification inference |
| `classify_javacore_inference_test_code.py` | Test code for ML inference |
| `csv_dataset_generator.py` | Generates training datasets |
| `javacoreThreadsClassifierModel.ubj` | Pre-trained model file |
| `javacoreThreadsClassifierInputParameters.json` | Model input parameters |
| `javacoreThreadsClassifierLabelEncoderMapping.json` | Label encoding mappings |

### Utilities

| File | Purpose |
|------|---------|
| `properties.py` | Singleton configuration manager, loads `config.ini` |
| `common_utils.py` | Logging setup, argument parsing |
| `exceptions.py` | Custom exception classes |
| `constants.py` | Project-wide constants |
| `tips.py` | Analysis tips generation (CPU, GC, blocking threads, etc.) |

## Data Resources (`src/javacore_analyser/data/`)

### JavaScript Libraries (`data/jquery/`)
- jQuery, Chart.js, tablesorter plugins
- Custom scripts: `wait2scripts.js`, `search.js`, `sorting.js`, `tablesorter-init.js`
- CSS themes for tables

### XSL Templates (`data/xml/`)

```
data/xml/
├── index.xml                        # Main report index
├── report.xsl                       # Main report stylesheet
├── sections/                        # Report section templates
│   ├── header.xsl
│   ├── input_files.xsl
│   ├── system_information.xsl
│   ├── system_resources.xsl
│   ├── all_threads.xsl
│   ├── all_code.xsl
│   ├── top_blockers.xsl
│   ├── intelligent_tips.xsl
│   ├── http_calls.xsl
│   └── footer.xsl
├── javacores/                       # Javacore detail templates
│   ├── javacore.xml
│   └── javacore.xsl
└── threads/                         # Thread detail templates
    ├── thread.xml
    └── thread.xsl
```

### Other Resources
- `data/html/` - Error and processing templates
- `data/prompts/` - LLM prompt templates
- `data/style.css`, `data/style.js`, `data/expand.js` - Report styling

## Test Structure (`test/`)

### Test Files

| File | Tests |
|------|-------|
| `test_javacore_analyser.py` | Main integration tests, archive processing |
| `test_javacore_set.py` | JavacoreSet functionality |
| `test_javacore.py` | Javacore parsing |
| `test_java_thread.py` | Thread analysis |
| `test_thread_snapshot.py` | Thread snapshot parsing |
| `test_verbose_gc_parser.py` | Verbose GC parsing |
| `test_har_file.py` | HAR file processing |
| `test_code_snapshot_collection.py` | Code collection grouping |
| `test_stack_trace.py`, `test_stack_trace_element.py` | Stack trace handling |
| `test_plugin_system.py` | Plugin loading and execution |
| `test_properties.py` | Configuration management |
| `test_tips.py` | Tips generation |
| `test_exceptions.py` | Exception handling |
| `test_zip_slip_security.py` | Security validation |
| `test_gc_collection.py` | GC collection parsing |

### Test Data (`test/data/`)

```
test/data/
├── javacores/                       # Sample javacore files
├── verboseGc/                       # Sample verbose GC logs
├── archives/                        # Test archives (.zip, .7z, .tar.gz, etc.)
├── issue129/, quotationMarks/       # Specific issue test cases
├── encoding/                        # Encoding test files
├── ml/                              # ML test datasets
└── verboseGcJavacores/              # Combined javacore + GC test sets
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project metadata, dependencies, build config |
| `requirements.txt` | Python dependencies |
| `config.ini` | Runtime configuration (auto-generated on first run) |
| `.gitignore` | Git exclusions |
| `Dockerfile` | Container image definition |

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `AGENTS.md` | Guidelines for AI coding assistants |
| `PROJECT_STRUCTURE.md` | This file - project structure overview |
| `REQUIREMENTS.md` | System requirements and dependencies |
| `CONTRIBUTING.md` | Contribution guidelines |
| `CHANGELOG.md` | Version history |
| `PLUGIN_ARCHITECTURE_DESIGN.md` | Plugin system design document |

## Key Workflows

### Batch Processing Flow
1. `javacore_analyser_batch.py` → Entry point
2. Extract archives if needed → `extract_archive()`
3. Create `JavacoreSet` → `JavacoreSet.create()`
4. Parse javacores → `parse_javacores()`
5. Parse verbose GC → `parse_verbose_gc_files()`
6. Parse HAR files → `HarFile`
7. Load plugins → `_process_plugins()`
8. Generate XML → `__create_report_xml()`
9. Generate HTML → `generate_htmls_from_xmls_xsls()`

### Web Processing Flow
1. User uploads files → `/upload` route
2. Save to reports directory
3. Same processing as batch mode
4. Serve generated HTML reports
5. Provide download/delete options

### Plugin Loading Flow
1. Check `enable_plugins` in config
2. `PluginManager.discover_plugins()` scans `~/.javacore_analyser/plugins/`
3. Load plugin classes extending `DataSourcePlugin`
4. Find matching files → `find_files_for_plugins()`
5. Process files → `plugin.process_files()`
6. Generate XML → `plugin.generate_xml()`
7. Generate HTML → `plugin.generate_html()`
8. Inject into report via `plugins.xsl`

## Important Patterns

### Singleton Pattern
- `Properties` class uses singleton pattern with `__new__()` method
- Access via `Properties.get_instance()`

### Resource Loading
- Uses `importlib_resources` for package data files
- Never uses `__file__` paths directly

### Logging
- Import `logging` module directly
- Call `logging.info()`, `logging.warning()`, `logging.error()` directly
- Do NOT create module-local loggers with `logging.getLogger(__name__)`

### File Handling
- Multiple input files use `;` separator (configurable with `--separator`)
- Archive support: `.zip`, `.7z`, `.tar.gz`, `.tar.bz2`, `.tgz`
- Minimum javacore size: 5KB (smaller = corrupted)
- Javacore pattern: `*javacore*.txt`

### Testing
- **CRITICAL**: Run tests from project root with `PYTHONPATH=src:test`
- Command: `PYTHONPATH=src:test python -m unittest discover`
- Single test: `PYTHONPATH=src:test python -m unittest test.test_javacore_analyser.TestJavacoreAnalyser.test_zip`

## Common Modification Scenarios

### Adding New Analysis Feature
1. Modify parsing in `javacore.py` or `thread_snapshot.py`
2. Update XML generation in `javacore_set.py`
3. Add XSL template in `data/xml/sections/`
4. Update `report.xsl` to include new section
5. Add tests in `test/`

### Adding New File Type Support
1. Create plugin in `~/.javacore_analyser/plugins/your_plugin/`
2. Extend `DataSourcePlugin` class
3. Implement required methods
4. Enable plugins in `config.ini`

### Modifying Report Layout
1. Edit XSL templates in `data/xml/sections/`
2. Modify CSS in `data/style.css`
3. Update JavaScript in `data/jquery/` if needed

### Adding LLM Provider
1. Create new class in `ai/` extending base `LLM` class
2. Implement `generate_response()` method
3. Update `llm.py` factory method
4. Add configuration in `config.ini`

## Dependencies

### Core Dependencies
- `py7zr` - Archive extraction
- `lxml` - XML/XSL processing
- `pyana` - Analysis utilities
- `importlib-resources` - Resource loading
- `tqdm` - Progress bars
- `haralyzer` - HAR file parsing

### Optional Dependencies
- `flask`, `waitress` - Web interface
- `ollama`, `Markdown` - Ollama LLM integration
- `torch`, `transformers`, `pandas` - HuggingFace LLM integration

## Build and Distribution

### Build Commands
```bash
python -m build                    # Build distribution packages
pip install .                      # Install from source
pip install -r requirements.txt    # Install dependencies
```

### Package Structure
- Source in `src/javacore_analyser/`
- Tests excluded from distribution
- Entry points: `javacore_analyser_batch`, `javacore_analyser_web`

## Security Considerations

- Zip slip protection in archive extraction
- Path validation for user-provided paths
- HTML escaping in plugin-generated content
- File size validation for javacores

## Performance Notes

- Parallel HTML generation from XML/XSL
- Configurable thread count for processing
- Efficient file pattern matching for plugins
- Lazy loading of large files

---

**Last Updated**: 2026-06-12  
**For**: Issue #292 - Create project structure description