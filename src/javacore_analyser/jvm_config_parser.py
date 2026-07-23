#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import re

from javacore_analyser.constants import (
    XMX, XMS, XMN, GC_POLICY, COMPRESSED_REFS, NO_COMPRESSED_REFS, VERBOSE_GC, UNKNOWN
)


class JvmConfigParser:
    """Parses JVM configuration arguments from a javacore file line.

    Responsible for extracting memory settings (Xmx, Xms, Xmn), GC policy,
    compressed references flag, and verbose GC flag from 2CIUSERARG lines.
    """

    def __init__(self):
        self.xmx = ""
        self.xms = ""
        self.xmn = ""
        self.gc_policy = ""
        self.compressed_refs = False
        self.verbose_gc = False
        self.user_args = []

    @staticmethod
    def parse_mem_arg(line):
        """Extract a memory argument value (e.g. 512m, 1g) from a javacore user-arg line."""
        line = line.split()[-1]  # avoid matching the '2' in tag name 2CIUSERARG
        tokens = re.findall(r"\d+[KkMmGg]?$", line)
        if len(tokens) != 1:
            return UNKNOWN
        return tokens[0]

    def parse_xmx(self, line):
        self.xmx = self.parse_mem_arg(line)

    def parse_xms(self, line):
        self.xms = self.parse_mem_arg(line)

    def parse_xmn(self, line):
        self.xmn = self.parse_mem_arg(line)

    def parse_gc_policy(self, line):
        self.gc_policy = line[line.rfind(":") + 1:].strip()

    def parse_compressed_refs(self, line):
        if COMPRESSED_REFS in line:
            self.compressed_refs = True
        if NO_COMPRESSED_REFS in line:
            self.compressed_refs = False

    def parse_verbose_gc(self, line):
        if VERBOSE_GC in line:
            self.verbose_gc = True

    def add_user_arg(self, line):
        # 2CIUSERARG               -Djava.lang.stringBuffer.growAggressively=false
        # Search for - and trim everything before
        arg = line[line.find('-'):].rstrip()
        logging.debug("User arg: " + arg)
        self.user_args.append(arg)

    def parse_user_args(self, line):
        self.add_user_arg(line)
        if XMX in line:
            self.parse_xmx(line)
        if XMS in line:
            self.parse_xms(line)
        if XMN in line:
            self.parse_xmn(line)
        if GC_POLICY in line:
            self.parse_gc_policy(line)
        if COMPRESSED_REFS in line or NO_COMPRESSED_REFS in line:
            self.parse_compressed_refs(line)
        if VERBOSE_GC in line:
            self.parse_verbose_gc(line)

    def apply_to(self, javacore_analyzer):
        """Copy parsed JVM config values onto a JavacoreAnalyzer (or JavacoreSet) instance."""
        javacore_analyzer.xmx = self.xmx
        javacore_analyzer.xms = self.xms
        javacore_analyzer.xmn = self.xmn
        javacore_analyzer.gc_policy = self.gc_policy
        javacore_analyzer.compressed_refs = self.compressed_refs
        javacore_analyzer.verbose_gc = self.verbose_gc
        javacore_analyzer.user_args = self.user_args
