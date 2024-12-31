#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

FROM python:3

EXPOSE 5000/tcp
ENV REPORTS_DIR=/reports
RUN mkdir /reports
VOLUME ["/reports"]

RUN pip install --no-cache-dir --root-user-action ignore javacore-analyser

CMD [ "javacore_analyser_web" ]
