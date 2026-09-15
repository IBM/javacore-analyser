#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite Dockerfile for Python fuzzing with atheris.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/
#
# NOTE: This Dockerfile is NOT used by the GitHub Actions ClusterFuzzLite
# integration (which uses project-src-path instead). It is kept for
# local OSS-Fuzz helper.py compatibility only.

FROM gcr.io/oss-fuzz-base/base-builder-python

# Copy the project source — the repo root becomes $SRC/javacore_analyser
COPY . $SRC/javacore_analyser
WORKDIR $SRC/javacore_analyser

# The build script expects $SRC to point directly at the repo root.
# Create a symlink so both $SRC/javacore_analyser and $SRC point at the source.
RUN ln -sf $SRC/javacore_analyser/.clusterfuzzlite/build.sh $SRC/build.sh

COPY .clusterfuzzlite/build.sh $SRC/
