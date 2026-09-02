#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import re
from typing import Optional
from xml.dom.minidom import Document, Element

from javacore_analyser.constants import (
    ARCHITECTURE,
    CMD_LINE,
    COMPRESSED_REFS,
    CPU_NUMBER_TAG,
    GC_POLICY,
    JAVA_VERSION,
    MEM_SECTION,
    NO_COMPRESSED_REFS,
    OS_LEVEL,
    STARTTIME,
    UNKNOWN,
    USER_ARGS,
    VERBOSE_GC,
    XMN,
    XMS,
    XMX,
)


class JvmInfo:
    """Holds JVM configuration information parsed from the header section of a javacore file.

    Instances are created by :meth:`parse`, which reads lines from an already-open file
    reader starting just after the datetime/siginfo section and continuing until the
    ``0MEMUSER`` memory section marker that ends the JVM header block.
    """

    def __init__(self):
        self.number_of_cpus: Optional[str] = None  # number of cpus the VM is using
        self.xmx: str = ""
        self.xms: str = ""
        self.xmn: str = ""
        self.gc_policy: str = ""
        self.compressed_refs: bool = False
        self.verbose_gc: bool = False
        self.os_level: str = ""
        self.architecture: str = ""
        self.java_version: str = ""
        self.jvm_start_time: str = ""
        self.cmd_line: str = ""
        self.user_args: list[str] = []

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def parse(self, file_reader) -> int:
        """Parse JVM information from *file_reader*.

        The caller must have already positioned the file pointer so that the
        next ``readline()`` call returns the first line of the JVM header block.

        Returns the number of lines read so the caller can add it to its own
        line counter.
        """
        lines_read = 0
        line = ""
        try:
            while True:
                line = file_reader.readline()
                lines_read += 1
                if line.startswith(CPU_NUMBER_TAG):
                    self.number_of_cpus = line.split()[-1]
                elif line.startswith(USER_ARGS):
                    self._parse_user_args(line)
                elif line.startswith(OS_LEVEL):
                    self.os_level = line[line.rfind(":") + 1:].strip()
                elif line.startswith(ARCHITECTURE):
                    self.architecture = line[line.rfind(":") + 1:].strip()
                elif line.startswith(JAVA_VERSION):
                    self.java_version = line[len(JAVA_VERSION) + 1:].strip()
                elif line.startswith(STARTTIME):
                    self.jvm_start_time = line[line.find(":") + 1:].strip()
                elif line.startswith(CMD_LINE):
                    self.cmd_line = line[len(CMD_LINE) + 1:].strip()
                elif line.startswith(MEM_SECTION):
                    return lines_read
        except Exception as e:
            logging.exception(e)
            name = getattr(file_reader, "name", "unknown")
            msg = (
                f"Error during processing file: {name}\n"
                f"line number: {lines_read}\n"
                f"line: {line}\n"
                f"Check the exception below what happened"
            )
            logging.error(msg)
            raise RuntimeError(msg) from e

    def _parse_user_args(self, line: str):
        self._add_user_arg(line)
        if XMX in line:
            self._parse_xmx(line)
        if XMS in line:
            self._parse_xms(line)
        if XMN in line:
            self._parse_xmn(line)
        if GC_POLICY in line:
            self._parse_gc_policy(line)
        if COMPRESSED_REFS in line or NO_COMPRESSED_REFS in line:
            self._parse_compressed_refs(line)
        if VERBOSE_GC in line:
            self._parse_verbose_gc(line)

    def _parse_mem_arg(self, line: str) -> str:
        line = line.split()[-1]  # avoid matching the '2' in tag name 2CIUSERARG
        tokens = re.findall(r"\d+[KkMmGg]?$", line)
        if len(tokens) != 1:
            return UNKNOWN
        return tokens[0]

    def _parse_xmx(self, line: str):
        self.xmx = self._parse_mem_arg(line)

    def _parse_xms(self, line: str):
        self.xms = self._parse_mem_arg(line)

    def _parse_xmn(self, line: str):
        self.xmn = self._parse_mem_arg(line)

    def _parse_gc_policy(self, line: str):
        self.gc_policy = line[line.rfind(":") + 1:].strip()

    def _parse_compressed_refs(self, line: str):
        if COMPRESSED_REFS in line:
            self.compressed_refs = True
        if NO_COMPRESSED_REFS in line:
            self.compressed_refs = False

    def _parse_verbose_gc(self, line: str):
        if VERBOSE_GC in line:
            self.verbose_gc = True

    def _add_user_arg(self, line: str):
        # 2CIUSERARG               -Djava.lang.stringBuffer.growAggressively=false
        # Search for '-' and trim everything before it
        arg = line[line.find("-"):].rstrip()
        logging.debug("User arg: " + arg)
        self.user_args.append(arg)

    # ------------------------------------------------------------------
    # XML serialisation
    # ------------------------------------------------------------------

    def to_xml(self, doc: Document) -> Element:
        """Return a ``<jvm_info>`` :class:`~xml.dom.minidom.Element` containing
        all JVM configuration fields, suitable for appending to the report XML."""
        jvm_info_node: Element = doc.createElement("jvm_info")

        def _text_child(tag: str, value: str) -> None:
            node = doc.createElement(tag)
            node.appendChild(doc.createTextNode(value))
            jvm_info_node.appendChild(node)

        _text_child("number_of_cpus", self.number_of_cpus or "")
        _text_child("xmx", self.xmx)
        _text_child("xms", self.xms)
        _text_child("xmn", self.xmn)
        _text_child("verbose_gc", str(self.verbose_gc))
        _text_child("gc_policy", self.gc_policy)
        _text_child("compressed_refs", str(self.compressed_refs))
        _text_child("architecture", self.architecture)
        _text_child("java_version", self.java_version)
        _text_child("os_level", self.os_level)
        _text_child("jvm_start_time", self.jvm_start_time)
        _text_child("cmd_line", self.cmd_line)

        user_args_list_node = doc.createElement("user_args_list")
        for arg in self.user_args:
            arg_node = doc.createElement("user_arg")
            arg_node.appendChild(doc.createTextNode(arg))
            user_args_list_node.appendChild(arg_node)
        jvm_info_node.appendChild(user_args_list_node)

        return jvm_info_node
