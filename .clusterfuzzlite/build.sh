#!/bin/bash -eu
#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite build script for Python fuzzing with atheris.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/
#
# When run on a GitHub Actions runner (not inside an OSS-Fuzz Docker container),
# $SRC and $OUT are not set — fall back to workspace-relative paths that
# ClusterFuzzLite itself uses on the runner.

# Resolve source root:
#   - Inside an OSS-Fuzz Docker container the repo is cloned to $SRC/javacore_analyser.
#   - On a GitHub Actions runner the repo is checked out directly into $GITHUB_WORKSPACE
#     (no subdirectory), so PROJECT_ROOT = $GITHUB_WORKSPACE.
#   - Fallback for running the script directly from the repo (local testing).
if [ -n "${SRC:-}" ] && [ -d "${SRC}/javacore_analyser" ]; then
    PROJECT_ROOT="${SRC}/javacore_analyser"
elif [ -n "${GITHUB_WORKSPACE:-}" ]; then
    PROJECT_ROOT="${GITHUB_WORKSPACE}"
else
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

# Resolve output dir: prefer $OUT (set inside OSS-Fuzz containers), otherwise
# use the build-out directory that ClusterFuzzLite's runner action reads from.
FUZZ_OUT="${OUT:-${GITHUB_WORKSPACE:-${PROJECT_ROOT}}/build-out}"
mkdir -p "$FUZZ_OUT"

# Install the package so fuzz targets can import javacore_analyser
pip3 install "$PROJECT_ROOT" || true

# For each fuzz target:
#   1. Copy the .py source to $FUZZ_OUT so it is importable at runtime.
#   2. Create an executable shell wrapper with the same stem (no extension) —
#      ClusterFuzzLite discovers fuzz targets as executable files with no extension.
for fuzzer in $(find "$PROJECT_ROOT/.clusterfuzzlite" -name "fuzz_*.py"); do
    fuzzer_name=$(basename "$fuzzer" .py)
    cp "$fuzzer" "$FUZZ_OUT/"
    cat > "$FUZZ_OUT/$fuzzer_name" << WRAPPER
#!/bin/bash
exec python3 "$FUZZ_OUT/${fuzzer_name}.py" "\$@"
WRAPPER
    chmod +x "$FUZZ_OUT/$fuzzer_name"
done
