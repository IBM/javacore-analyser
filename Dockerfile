#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

FROM python:3

EXPOSE 5000/tcp
RUN mkdir /reports
VOLUME ["/reports"]

CMD javacore_analyser_web --port=5000 --reports-dir=/reports

# As default we do not set the version to have the latest one for build.
ARG version=
# This is the most frequently modified line so it should be at the end.
RUN pip install --root-user-action ignore --no-cache-dir javacore-analyser${version}
