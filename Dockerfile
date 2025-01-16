#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

FROM python:3

EXPOSE 5000/tcp
RUN mkdir /reports
VOLUME ["/reports"]

CMD javacore_analyser_web --port=5000 --reports-dir=/reports

# This is the most frequently modified line so it should be at the end.
RUN pip install --no-cache-dir javacore-analyser