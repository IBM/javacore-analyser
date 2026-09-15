#!/bin/bash -eu
#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite build script for Python fuzzing with atheris.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/
#
# Called by build_fuzzers action with:
#   $SRC  — the project source directory (= github.workspace passed via project-src-path)
#   $OUT  — the output directory where fuzz target binaries must be placed

# Install atheris and the project package so fuzz targets can import javacore_analyser
pip3 install atheris
pip3 install "$SRC"

# For each fuzz target:
#   1. Copy the .py source to $OUT so it is importable at runtime.
#   2. Create an executable shell wrapper with the same stem (no extension) —
#      ClusterFuzzLite discovers fuzz targets as executable files with no extension.
for fuzzer in $(find "$SRC/.clusterfuzzlite" -name "fuzz_*.py"); do
    fuzzer_name=$(basename "$fuzzer" .py)
    cp "$fuzzer" "$OUT/"
    printf '#!/bin/bash\nexec python3 "%s/%s.py" "$@"\n' "$OUT" "$fuzzer_name" > "$OUT/$fuzzer_name"
    chmod +x "$OUT/$fuzzer_name"
done
