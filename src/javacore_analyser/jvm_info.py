#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Optional
from xml.dom.minidom import Document, Element, parseString

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
            name = getattr(file_reader, "name", "unknown")
            msg = (
                f"Error during processing file: {name}\n"
                f"line number: {lines_read}\n"
                f"line: {line}\n"
                f"Check the exception below what happened"
            )
            logging.exception(msg)
            raise RuntimeError(msg) from e

    def parse_verbose_gc(self, file_path: str) -> None:
        """Parse JVM information from a verbosegc XML file."""
        try:
            file = Path(file_path)
            xml_text = file.read_text()
            xml_text = xml_text.replace("&#x1;", "?")
            closing_tag = "</verbosegc>"
            if closing_tag not in xml_text:
                xml_text = xml_text + closing_tag

            doc = parseString(xml_text)
            root = doc.documentElement

            # Find the initialized element
            initialized_nodes = root.getElementsByTagName("initialized")
            if not initialized_nodes:
                return
            initialized_node = initialized_nodes[0]

            # 1. Parse start time from timestamp attribute, convert to javacore format if possible
            timestamp = initialized_node.getAttribute("timestamp")
            if timestamp:
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                    self.jvm_start_time = dt.strftime("%Y/%m/%d at %H:%M:%S:%f")[:-3]
                except Exception:
                    try:
                        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                        self.jvm_start_time = dt.strftime("%Y/%m/%d at %H:%M:%S:000")
                    except Exception:
                        self.jvm_start_time = timestamp

            # 2. Parse attributes directly under initialized
            for child in initialized_node.childNodes:
                if child.nodeType == child.ELEMENT_NODE and child.tagName == "attribute":
                    name = child.getAttribute("name")
                    val = child.getAttribute("value")
                    if name == "gcPolicy":
                        self.gc_policy = val[val.rfind(":") + 1:].strip()
                    elif name == "compressedRefs":
                        self.compressed_refs = val.lower() == "true"
                    elif name == "maxHeapSize":
                        if val.startswith("0x"):
                            self.xmx = str(int(val, 16))
                        else:
                            self.xmx = val
                    elif name == "initialHeapSize":
                        if val.startswith("0x"):
                            self.xms = str(int(val, 16))
                        else:
                            self.xms = val

            # 3. Parse system element
            system_nodes = initialized_node.getElementsByTagName("system")
            if system_nodes:
                system_node = system_nodes[0]
                os_name = ""
                os_version = ""
                for child in system_node.childNodes:
                    if child.nodeType == child.ELEMENT_NODE and child.tagName == "attribute":
                        name = child.getAttribute("name")
                        val = child.getAttribute("value")
                        if name == "numCPUs":
                            self.number_of_cpus = val
                        elif name == "architecture":
                            self.architecture = val
                        elif name == "os":
                            os_name = val
                        elif name == "osVersion":
                            os_version = val
                if os_name:
                    self.os_level = f"{os_name} {os_version}".strip()

            # 4. Parse vmargs and populate cmd_line, user_args
            vmargs_nodes = initialized_node.getElementsByTagName("vmargs")
            if vmargs_nodes:
                vmargs_node = vmargs_nodes[0]
                for child in vmargs_node.childNodes:
                    if child.nodeType == child.ELEMENT_NODE and child.tagName == "vmarg":
                        arg_name = child.getAttribute("name")
                        if arg_name:
                            self.user_args.append(arg_name)
                            # Parse out information matching userargs logic
                            if "-Xmx" in arg_name:
                                parsed_val = self._parse_mem_arg(arg_name)
                                if parsed_val != UNKNOWN:
                                    self.xmx = parsed_val
                            if "-Xms" in arg_name:
                                parsed_val = self._parse_mem_arg(arg_name)
                                if parsed_val != UNKNOWN:
                                    self.xms = parsed_val
                            if "-Xmn" in arg_name:
                                parsed_val = self._parse_mem_arg(arg_name)
                                if parsed_val != UNKNOWN:
                                    self.xmn = parsed_val
                            if "-Xgcpolicy" in arg_name:
                                self.gc_policy = arg_name[arg_name.rfind(":") + 1:].strip()
                            if "-Xcompressedrefs" in arg_name or "-Xnocompressedrefs" in arg_name:
                                if "-Xnocompressedrefs" in arg_name:
                                    self.compressed_refs = False
                                elif "-Xcompressedrefs" in arg_name:
                                    self.compressed_refs = True
                            if "-verbose:gc" in arg_name:
                                self.verbose_gc = True

            self.verbose_gc = True # Definitely True for verbosegc parser

            # Reconstruct cmd_line from vmargs
            if self.user_args:
                non_sun_command_args = [arg for arg in self.user_args if not arg.startswith("-Dsun.java.command=")]
                sun_command_val = next(
                    (arg.split("=", 1)[1] for arg in self.user_args if arg.startswith("-Dsun.java.command=")), ""
                )
                self.cmd_line = f"java {' '.join(non_sun_command_args)} {sun_command_val}".strip()

        except Exception as e:
            msg = f"Error during processing verbosegc file: {file_path}. Check the exception below what happened"
            logging.exception(msg)
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
        if NO_COMPRESSED_REFS in line:
            self.compressed_refs = False
        elif COMPRESSED_REFS in line:
            self.compressed_refs = True

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
