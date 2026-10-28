#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

FROM python:3@sha256:5acd826ebc4a7bb4cc50ff2dd0dc479043fab0ae40c4f1661018980374df00b3

LABEL org.opencontainers.image.source="https://github.com/IBM/javacore-analyser"
LABEL org.opencontainers.image.description="This is a tool to analyse IBM Javacore files and provide the report used to analyse hang/outage and performance issues."
LABEL org.opencontainers.image.licenses="Apache-2.0"

EXPOSE 5000/tcp
RUN mkdir /reports
VOLUME ["/reports"]

# As default we do not set the version to have the latest one for build.
ARG version=""
#RUN ["pip", "install", "--no-cache-dir", "--root-user-action", "ignore", "javacore-analyser${version}"]
RUN pip install --no-cache-dir --root-user-action ignore javacore-analyser${version}
CMD ["javacore_analyser_web", "--port=5000", "--reports-dir=/reports"]
