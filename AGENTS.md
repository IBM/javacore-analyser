# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Structure

For a comprehensive overview of the project structure, file organization, and key workflows, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md). This document helps AI coding assistants quickly understand the codebase without scanning all files.

## Coding Standards

The project follows **PEP 8** coding standard (https://peps.python.org/pep-0008/) with the following specifics:
- **Maximum line length**: 120 characters
- **Type hints**: Recommended for better readability and maintainability
- Follow PEP 8 naming conventions (snake_case for functions/variables, PascalCase for classes)

## Branching Strategy

Each new feature or bug fix should be developed in a separate branch:
- **Branch naming format**: `issue-<issue-id>-short-description-with-minus-as-space`
- **Examples**:
  - `issue-242-default-llm-options`
  - `issue-239-update-chart-js-library`
  - `issue-105-plugin-architecture`

## Commit Guidelines

All commits must follow these rules:
- **Signed-off-by required**: Use `--signoff` flag with every commit
- **Reference issue**: Include `Ref #<issue-id>` or `Fixes #<issue-id>` in commit message
- **Example commands**:
  ```bash
  git commit --signoff -m "Fixes #243 Upgrading chart.js JS library"
  git commit --signoff -m "Ref #243 Move setting LLM options to llm.py"
  ```

## Pull Request Guidelines

- **PR title format**: `#<issue-id> Issue description`
- **Examples**:
  - `#242 Add support for default LLM options`
  - `#1 Add more parameters for verbose gc chart`
- **PR description**: Must contain `Fixes #<issue-id>` to auto-link and close the issue
- **Testing summary**: Must include a "How it was tested" section with specific validation details:
  - For code changes: Include test commands used (e.g., `PYTHONPATH=src:test python -m unittest discover` or `PYTHONPATH=src:test python -m unittest test.test_javacore_analyser.TestJavacoreAnalyser.test_zip`)
  - For manual testing: Describe the steps and commands executed
  - For documentation-only changes: State "Documentation-only change, no tests required"

## Testing and Validation

Before creating a pull request:
1. **Run all tests**: Ensure all unit tests pass (not required if only documentation is updated)
2. **Manual testing**: Run the tool and review output to verify functionality
3. **Code review**: Check for PEP 8 compliance and proper documentation

**Note**: Tests are not required when only documentation files are updated.

## Testing

**CRITICAL**: Tests MUST be run from project root with `PYTHONPATH=src:test`:
```bash
PYTHONPATH=src:test python -m unittest discover
```

Running tests from `test/` directory will fail. The working directory must be the project root.

## Running Single Test

```bash
PYTHONPATH=src:test python -m unittest test.test_javacore_analyser.TestJavacoreAnalyser.test_zip
```

## Build Commands

```bash
python -m build                    # Build distribution packages
pip install .                      # Install from source
pip install -r requirements.txt    # Install dependencies
```

## Configuration Behavior

- `config.ini` is auto-generated in working directory on first run (uses `importlib_resources` to copy from package)
- Debug logs are always named `wait2-debug.log` in the output/reports directory (not configurable)
- Use `--config_file` to specify alternate config location

## Input File Handling

- Multiple input files use `;` separator by default: `file1.txt;file2.txt`
- Change separator with `--separator` flag
- Single javacore files must match pattern `*javacore*.txt`
- Minimum valid javacore size: 5KB (smaller files treated as corrupted)

## LLM Integration

Two distinct methods (not interchangeable):
- `llm_method=ollama`: Requires Ollama server, uses models like `ibm/granite4:latest`
- `llm_method=huggingface`: Local inference, uses models like `ibm-granite/granite-4.0-micro`

Model format differs between methods - check config.ini for examples.

## Archive Support

Supports: `.zip`, `.7z`, `.tar.gz`, `.tar.bz2`, `.tgz`

## Code Patterns

- Properties class uses standard Python singleton pattern with `__new__()` method
- String properties auto-convert to bool/int in `load_properties()` method
- Uses `importlib_resources` for accessing package data files (not `__file__` paths)

## Logging

Use the standard `logging` module directly at module level. The project convention is to import `logging` and call
`logging.info(...)`, `logging.warning(...)`, `logging.error(...)`, `logging.debug(...)`, and `logging.exception(...)`
directly. Do not create module-local loggers with `logger = logging.getLogger(__name__)` unless there is a specific
project-wide change introducing that pattern.

### Correct pattern

```python
import logging

logging.info("Starting plugin discovery")
logging.debug(f"Scanning directory: {plugin_dir}")
logging.warning(f"Plugin directory does not exist: {plugin_dir}")
```

### Avoid

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Starting plugin discovery")
```