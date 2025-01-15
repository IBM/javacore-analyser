#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#
import os

from haralyzer import HarParser
import json


class HarFile:

    def __init__(self, path):
        self.path = path
        with open(path, 'r') as f:
            self.har = HarParser(json.loads(f.read()))

    def get_xml(self, doc):
        har_file_node = doc.createElement("har_file")
        har_file_node.setAttribute("filename", os.path.basename(self.path))
        har_file_node.setAttribute("hostname", str(self.har.hostname))
        har_file_node.setAttribute("browser", str(self.har.browser))
        for page in self.har.pages:
            for entry in page.entries:
                http_call = HttpCall(entry)
                har_file_node.appendChild(http_call.get_xml(doc))
        return har_file_node


class HttpCall:

    def __init__(self, call):
        self.call = call
        self.url = call.url
        self.status = str(call.status)
        self.start_time = str(call.startTime)
        self.duration = str(self.get_total_time())
        self.timings = str(call.timings)
        self.size = str(call.response.bodySize)
        self.success = str(self.get_success())

    def get_total_time(self):
        total = 0
        if len(self.call.timings) > 0:
            for key in self.call.timings.keys():
                time = int(self.call.timings[key])
                if time > 0:
                    total += time
        return total

    def get_success(self):
        if self.status.startswith('4') or self.status.startswith('5'):
            return False
        return True

    def get_xml(self, doc):
        http_call_node = doc.createElement("http_call")
        http_call_node.setAttribute("url", self.url)
        http_call_node.setAttribute("status", self.status)
        http_call_node.setAttribute("start_time", self.start_time)
        http_call_node.setAttribute("duration", self.duration)
        http_call_node.setAttribute("timings", self.timings)
        http_call_node.setAttribute("size", self.size)
        http_call_node.setAttribute("success", self.success)
        return http_call_node
