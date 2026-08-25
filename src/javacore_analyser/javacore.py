#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import codecs
import datetime
import logging
import os.path
from typing import Any, Optional

from javacore_analyser.constants import (
    CURRENT_THREAD_INFO,
    DATETIME,
    ENCODING,
    SIGINFO,
    THREAD_INFO,
)
from javacore_analyser.jvm_info import JvmInfo
from javacore_analyser.thread_snapshot import ThreadSnapshot


class CorruptedJavacoreException(Exception):
    
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Javacore:

    def __init__(self):
        self.javacore_set: Any = None
        self.datetime: Optional[datetime.datetime] = None
        self.timestamp: Optional[float] = None
        self.filename: Optional[str] = None
        self.file_reader: Any = None
        self.snapshots: list[ThreadSnapshot] = []
        self.siginfo: Optional[str] = None
        self.__total_cpu: float = -1
        self.__load: float = -1
        self.__encoding: Optional[str] = None
        self.jvm_info: JvmInfo = JvmInfo()
        self.curr_line: str = ""
        self.line_num: int = 0

    @staticmethod
    def create(filename, javacore_set):
        javacore = Javacore()
        javacore.filename = filename
        javacore.javacore_set = javacore_set
        javacore.parse()
        return javacore

    def parse(self):
        try:
            self.file_reader = codecs.open(self.filename, encoding=self.get_encoding(), errors='strict')  # type: ignore[arg-type]
            self._parse_siginfo()
            self._parse_datetime()
            self.line_num += self.jvm_info.parse(self.file_reader)
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
        self.__total_cpu /= int(self.jvm_info.number_of_cpus)  # type: ignore[arg-type,operator]

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
        file = codecs.open(self.filename, errors='strict')  # type: ignore[arg-type]
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
                raise CorruptedJavacoreException("Javacore " + str(self.filename) + " is corrupted in line " + string)
        string = bts.decode('utf-8', 'ignore')
        return string

    def _parse_thread_snapshots(self):
        """ creates a ThreadSnapshot object for each "3XMTHREADINFO" tag found in the javacore """
        line = ""
        is_current = False
        try:
            while True:
                line = self.file_reader.readline()
                self.line_num += 1
                if not line:
                    break
                line = self.encode(line)
                if line.startswith(CURRENT_THREAD_INFO):
                    is_current = True
                elif line.startswith(THREAD_INFO):
                    line = self.process_thread_name(line)
                    snapshot = ThreadSnapshot.create(line, self.file_reader, self, is_current=is_current)
                    if is_current:
                        self.current_thread = snapshot
                        is_current = False
                    self.snapshots.append(snapshot)
        except Exception as e:
            msg: str = "Corrupted javacore file {} \n" \
                       "Error message: {} \n" \
                       "Line number: {} \n" \
                       "Previous line: {} \n" \
                       .format(self.basefilename(), e, str(self.line_num), line)
            raise CorruptedJavacoreException(msg) from e

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
        logging.debug("Javacore filename: " + str(self.filename))
        self.print_thread_snapshots()
        logging.debug("\n")

    def print_thread_snapshots(self):
        for snapshot in self.snapshots:
            logging.debug(snapshot)

    def basefilename(self) -> str:
        return os.path.basename(self.filename or "")

    def basefilename_without_extension(self):
        return os.path.splitext(self.basefilename())[0]

    def get_id(self):
        """Unique identifier of javacore"""
        return self.basefilename()
