# Plan Mode Rules

## Architecture (Non-Obvious)

- Properties class is singleton with custom `__create_key` pattern (not standard Python singleton)
- Config auto-generation uses `importlib_resources` to copy from package (not file paths)
- Two separate LLM implementations: OllamaLLM (server) vs HuggingFaceLLM (local inference)
- String properties auto-convert to bool/int during load (e.g., "true" → True, "123" → 123)

## Critical Constraints

- Tests MUST run from project root with `PYTHONPATH=src:test` (not from test/ directory)
- Debug log filename hardcoded as `wait2-debug.log` (not configurable)
- Javacore files must be ≥5KB or treated as corrupted (MIN_JAVACORE_SIZE constant)
- Single javacore files must match `*javacore*.txt` pattern (fnmatch validation)
- Input file separator defaults to `;` but configurable via `--separator`

## Build & Deployment

- Uses `hatchling` + `versioningit` for dynamic versioning (not static version in pyproject.toml)
- Travis CI sets `PYTHONPATH=src:test` globally for all test runs
- Container runs web app on port 5000, reports stored in `/reports` volume
- Package data accessed via `importlib_resources`, never `__file__` paths