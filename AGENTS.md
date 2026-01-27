# AGENTS.md

This file provides guidance to agents when working with code in this repository.

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