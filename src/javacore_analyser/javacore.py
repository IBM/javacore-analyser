#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import codecs
import datetime
import logging
import os.path
import re

from javacore_analyser.constants import *
from javacore_analyser.thread_snapshot import ThreadSnapshot


class CorruptedJavacoreException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Javacore:

    def __init__(self):
        self.javacore_set = None
        self.datetime = None
        self.timestamp = None
        self.filename = None
        self.file_reader = None
        self.snapshots = []
        self.siginfo = None
        self.__total_cpu = -1
        self.__load = -1
        self.__encoding = None

        self.number_of_cpus = None  # number of cpus the VM is using
        self.xmx = ""
        self.xms = ""
        self.xmn = ""
        self.gc_policy = ""
        self.compressed_refs = False
        self.verbose_gc = False
        self.os_level = ""
        self.architecture = ""
        self.java_version = ""
        self.jvm_start_time = ""
        self.cmd_line = ""
        self.user_args = []
        self.snapshots = []
        self.curr_line = ""
        self.line_num = 0

    @staticmethod
    def create(filename, javacore_set):
        javacore = Javacore()
        javacore.filename = filename
        javacore.javacore_set = javacore_set
        javacore.parse()
        return javacore

    def parse(self):
        try:
            self.file_reader = codecs.open(self.filename, encoding=self.get_encoding(), errors='strict')
            self._parse_siginfo()
            self._parse_datetime()
            self._parse_header_data()
            self._parse_thread_snapshots()
        except UnicodeDecodeError as e:
            msg: str = "Unicode, decode error in file {}. Error message: {}".format(self.basefilename(), e)
            raise CorruptedJavacoreException(msg) from e
        finally:
            self.file_reader.close()

    def _parse_siginfo(self):
        while True:
            self.line = self.file_reader.readline()
            self.line_num += 1
            if self.line.startswith(SIGINFO + " "):
                self.siginfo = self.line[len(SIGINFO):].strip()
                return

    def _parse_datetime(self):
        # 1TIDATETIME    Date: 2022/04/12 at 09:56:36:266
        datetime_object = None  # for coding good practices only
        while True:
            self.line = self.file_reader.readline()
            self.line_num += 1
            if not self.line: break
            if self.line.startswith(DATETIME + " ") or self.line.startswith(DATETIME + "\t"):
                line = self.line[len(DATETIME):].strip()
                fmt = "Date: %Y/%m/%d at %H:%M:%S:%f"
                self.datetime = datetime.datetime.strptime(line, fmt)
                self.timestamp = self.datetime.timestamp()
                break

    def _parse_header_data(self):
        i = 0
        try:
            while True:
                self.line = self.file_reader.readline()
                self.line_num += 1
                i += 1
                if self.line.startswith(CPU_NUMBER_TAG):  # for example: 3XHNUMCPUS       How Many       : 16
                    self.number_of_cpus = self.line.split()[-1]
                    continue
                elif self.line.startswith(USER_ARGS):
                    self._parse_user_args(self.line)
                    continue
                elif self.line.startswith(OS_LEVEL):
                    self.os_level = self.line[self.line.rfind(":") + 1:].strip()
                    continue
                elif self.line.startswith(ARCHITECTURE):
                    self.architecture = self.line[self.line.rfind(":") + 1:].strip()
                    continue
                elif self.line.startswith(JAVA_VERSION):
                    self.java_version = self.line[len(JAVA_VERSION) + 1:].strip()
                    continue
                elif self.line.startswith(STARTTIME):
                    self.jvm_start_time = self.line[self.line.find(":") + 1:].strip()
                    continue
                elif self.line.startswith(CMD_LINE):
                    self.cmd_line = self.line[len(CMD_LINE) + 1:].strip()
                    continue
                elif self.line.startswith(MEM_SECTION): # end of header data section
                    return
        except Exception as e:
            logging.exception(e)
            if self.file_reader is not None:
                msg = f'Error during processing file: {self.file_reader.name} \n' \
                      f'line number: {self.line_num} \n' \
                      f'line: {self.line}\n' \
                      f'Check the exception below what happened'
                logging.error(msg)
            raise CorruptedJavacoreException(msg) from e

    def _parse_user_args(self, line):
        self._add_user_arg(line)
        if line.__contains__(XMX): self._parse_xmx(line)
        if line.__contains__(XMS): self._parse_xms(line)
        if line.__contains__(XMN): self._parse_xmn(line)
        if line.__contains__(GC_POLICY): self._parse_gc_policy(line)
        if line.__contains__(COMPRESSED_REFS) or line.__contains__(NO_COMPRESSED_REFS): self._parse_compressed_refs(line)
        if line.__contains__(VERBOSE_GC): self._parse_verbose_gc(line)

    def _parse_mem_arg(self, line):
        line = line.split()[-1]  # avoid matching the '2' in tag name 2CIUSERARG
        tokens = re.findall("\d+[KkMmGg]?$", line)
        if len(tokens) != 1: return UNKNOWN
        return tokens[0]
    
    def _parse_xmx(self, line):
        self.xmx = self._parse_mem_arg(line)

    def _parse_xms(self, line):
        self.xms = self._parse_mem_arg(line)

    def _parse_xmn(self, line):
        self.xmn = self._parse_mem_arg(line)

    def _parse_gc_policy(self, line):
        self.gc_policy = line[line.rfind(":") + 1:].strip()

    def _parse_compressed_refs(self, line):
        if line.__contains__(COMPRESSED_REFS): self.compressed_refs = True
        if line.__contains__(NO_COMPRESSED_REFS): self.compressed_refs = False

    def _parse_verbose_gc(self, line):
        if line.__contains__(VERBOSE_GC): self.verbose_gc = True

    def _add_user_arg(self, line):
        # 2CIUSERARG               -Djava.lang.stringBuffer.growAggressively=false
        # Search for - and trim everything before
        # (from https://stackoverflow.com/questions/30945784/how-to-remove-all-characters-before-a-specific
        # -character-in-python)
        arg = line[line.find('-'):].rstrip()
        logging.debug("User arg: " + arg)
        self.user_args.append(arg)
    
    def _parse_thread_snapshots(self):
        """ creates a ThreadSnapshot object for each "3XMTHREADINFO" tag found in the javacore """
        try:
            while True:
                self.line = self.file_reader.readline()
                self.line_num += 1
                if not self.line:
                    break
                self.line = self.encode(self.line)
                if self.line.startswith(THREAD_INFO):
                    self.line = self.process_thread_name(self.line)
                    snapshot = ThreadSnapshot.create(self.line, self.file_reader, self)
                    self.snapshots.append(snapshot)
        except Exception as e:
            msg: str = "Corrupted javacore file {} \n" \
                        "Error message: {} \n" \
                        "Line number: {} \n" \
                        "Previous line: {} \n" \
                        .format(self.basefilename(), e, str(self.line_num), self.line)
            raise CorruptedJavacoreException(msg) from e


    def is_interesting(self):  # method is to be overloaded in subclasses, ignore the static warning
        return True

    def get_cpu_percentage(self):
        if self.__total_cpu == -1:
            self.__calculate_total_cpu_and_load()
        return self.__total_cpu

    def __calculate_total_cpu_and_load(self):
        self.__total_cpu = 0
        for s in self.snapshots:
            self.__total_cpu += s.get_cpu_percentage()
        self.__load = self.__total_cpu / 100
        self.__total_cpu /= int(self.number_of_cpus)

    def get_load(self):
        if self.__load == -1:
            self.__calculate_total_cpu_and_load()
        return self.__load

    def get_snapshot_by_name(self, name):
        for snapshot in self.snapshots:
            if snapshot.name == name: return snapshot
        return None

    def get_encoding(self):
        if self.__encoding:
            return self.__encoding
        # assuming cp-850 encoding as default.
        # This should never be required, as javacores are guaranteed
        # to contain encoding information
        self.__encoding = "850"
        # opening the file without specifying the encoding (which we don't know yet)
        # the encoding line is near the top of the javacore
        # so assuming everything up to that point is plain old ASCII
        file = codecs.open(self.filename, errors='strict')
        while True:
            line = file.readline()
            if not line:
                break
            if line.startswith(ENCODING):
                # Leave the default encoding if it was not defined
                # 1TICHARSET     [not available]
                if not line.__contains__("[not available]"):
                    self.__encoding = line.split(" ")[-1].strip()
                break
        file.close()
        return self.__encoding

    def encode(self, string):
        bts = str.encode(string, self.get_encoding(), 'ignore')
        for i in range(0, len(bts)):
            # fix for 'XML Syntax error PCDATA invalid char#405'
            if bts[i] < 32 and bts[i] != 9 and bts[i] != 10 and bts[i] != 13 and bts[i] != 1:
                raise CorruptedJavacoreException("Javacore " + self.filename + " is corrupted in line " + string)
        string = bts.decode('utf-8', 'ignore')
        return string

    def process_thread_name(self, line):
        count = line.count('"')
        if count == 0: return line  # anonymous native threads
        while True:
            count = line.count('"')
            if count == 1:
                next_line = self.file_reader.readline()
                self.line_num += 1
                line = line + next_line
            else:
                return line

    def print_javacore(self):
        logging.debug("Javacore filename: " + self.filename)
        self.print_thread_snapshots()
        logging.debug("\n")

    def print_thread_snapshots(self):
        for snapshot in self.snapshots:
            logging.debug(snapshot)

    def basefilename(self):
        return os.path.basename(self.filename)

    def basefilename_without_extension(self):
        return os.path.splitext(self.basefilename())[0]

    def get_id(self):
        """Unique identifier of javacore"""
        return self.basefilename()
