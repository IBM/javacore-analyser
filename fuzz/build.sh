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

# Copy every fuzz target to $OUT
for fuzzer in $(find "$SRC/javacore_analyser/fuzz" -name "fuzz_*.py"); do
    cp "$fuzzer" "$OUT/"
done
