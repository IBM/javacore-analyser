# Advance Mode Rules

## Non-Obvious Coding Patterns

- Properties singleton uses custom `__create_key` pattern instead of standard Python singleton
- String config values auto-convert to bool/int in `Properties.load_properties()` (e.g., "true" → True, "123" → 123)
- Always use `importlib_resources` for package data access, never `__file__` paths
- Debug log filename is hardcoded as `wait2-debug.log` in `common_utils.create_file_logging()`
- Javacore files must be ≥5KB (MIN_JAVACORE_SIZE constant) or treated as corrupted
- Input file separator defaults to `;` but configurable via `--separator` flag
- Single javacore files must match `*javacore*.txt` pattern (fnmatch)

## LLM Integration

Two incompatible methods:
- `ollama`: Server-based, model format like `ibm/granite4:latest`
- `huggingface`: Local inference, model format like `ibm-granite/granite-4.0-micro`

Check `config.ini` for correct model format per method.

## Testing Requirements

MUST set `PYTHONPATH=src:test` and run from project root:
```bash
PYTHONPATH=src:test python -m unittest test.test_module.TestClass.test_method