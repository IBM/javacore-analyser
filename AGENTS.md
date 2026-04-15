# AGENTS.md

This file provides guidance to agents when working with code in this repository.

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

## Testing and Validation

Before creating a pull request:
1. **Run all tests**: Ensure all unit tests pass
2. **Manual testing**: Run the tool and review output to verify functionality
3. **Code review**: Check for PEP 8 compliance and proper documentation

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