#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite Dockerfile for Python fuzzing with atheris.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/

FROM gcr.io/oss-fuzz-base/base-builder-python

# Copy the project source and fuzz targets
COPY . $SRC/javacore_analyser
WORKDIR $SRC/javacore_analyser

# Install package dependencies including atheris for fuzzing
RUN pip3 install atheris && pip3 install -e ".[full]" || pip3 install -e .

COPY fuzz/build.sh $SRC/
