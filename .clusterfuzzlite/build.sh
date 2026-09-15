#!/bin/bash -eu
#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite build script for Python fuzzing with atheris.
# Copies each fuzz target to $OUT so the fuzzer runner can discover them.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/

# Install the package so the fuzz targets can import javacore_analyser
pip3 install "$SRC/javacore_analyser" || true

# For each fuzz target:
#   1. Copy the .py source to $OUT so atheris can find it.
#   2. Create an executable shell wrapper with the same stem (no extension)
#      — ClusterFuzzLite only discovers fuzz targets that are executable
#      files with no extension inside $OUT.
for fuzzer in $(find "$SRC/javacore_analyser/.clusterfuzzlite" -name "fuzz_*.py"); do
    fuzzer_name=$(basename "$fuzzer" .py)
    cp "$fuzzer" "$OUT/"
    # Write the launcher that the runner will invoke
    cat > "$OUT/$fuzzer_name" << EOF
#!/bin/bash
exec python3 "$OUT/${fuzzer_name}.py" "\$@"
EOF
    chmod +x "$OUT/$fuzzer_name"
done
