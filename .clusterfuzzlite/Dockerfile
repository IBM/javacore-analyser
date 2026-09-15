#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# ClusterFuzzLite Dockerfile for Python fuzzing with atheris.
# See https://google.github.io/clusterfuzzlite/build-integration/python-lang/

FROM gcr.io/oss-fuzz-base/base-builder-python

# Copy project source to $SRC (=/src) and build.sh to $SRC so the
# base-builder compile script can find it at /src/build.sh.
COPY . $SRC/
WORKDIR $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh
