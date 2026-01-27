# Ask Mode Rules

## Project Structure (Non-Obvious)

- `src/javacore_analyser/` contains main analysis logic, not just utilities
- `test/data/` has multiple subdirectories for different test scenarios (archives, encoding, verboseGc, etc.)
- Config file auto-generates in working directory on first run (not in project root)
- Debug logs always named `wait2-debug.log` in output directory (hardcoded, not configurable)

## Documentation Context

- Two entry points: `javacore_analyser_batch` (CLI) and `javacore_analyser_web` (Flask web app)
- LLM integration has two separate implementations: Ollama (server) vs HuggingFace (local)
- Archive extraction supports 5 formats: zip, 7z, tar.gz, tar.bz2, tgz
- Input files can be: directory, archive, semicolon-separated list, or single javacore file
- Single javacore files MUST match `*javacore*.txt` pattern to be recognized

## Testing Context

- Tests MUST run from project root with `PYTHONPATH=src:test`
- Test data organized by scenario: archives/, encoding/, issue129/, verboseGc/, etc.
- Minimum javacore size is 5KB (smaller files treated as corrupted)